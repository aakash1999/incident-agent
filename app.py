import os
import uuid
from datetime import datetime, timezone
from collections import deque
from threading import Lock

import boto3
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import RunContext

from models import SeverityLevel, SeverityResult

SEVERITY_INSTRUCTIONS = """
You are an incident triage agent. Classify the customer problem into P1-P4.

Severity guidelines:
- P1 (Critical): complete outage, security incident, significant data loss, or
  widespread impact across many customers with no viable workaround.
- P2 (High): major degradation or partial outage with significant business
  impact; limited workaround or only some users affected.
- P3 (Medium): minor degradation, localized impact, or clear workaround exists.
- P4 (Low): cosmetic issues, questions, low urgency, or informational requests.

Return a concise summary and rationale that references impact/scope/urgency.

After you decide severity, summary, and rationale:
- Call `store_incident` with the original customer text plus your severity/summary/rationale.
- Call `notify_incident` with the same fields.
- Call each tool once. If a tool has already been called, do not call it again.

Do not mention tool calls in the summary or rationale.
Then return the final response as the same structured output (severity, summary, rationale) only.
""".strip()

INCIDENTS_TABLE_ENV = "INCIDENTS_TABLE_NAME"
INCIDENTS_TOPIC_ENV = "INCIDENTS_TOPIC_ARN"
_TOOL_GUARD_LOCK = Lock()
_TOOL_CALLS_BY_RUN: dict[int, set[str]] = {}
_TOOL_RUN_ORDER: deque[int] = deque()
_TOOL_GUARD_MAX_RUNS = 200


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _should_execute_tool(ctx: RunContext[None], tool_name: str) -> bool:
    run_key = id(ctx.messages) if ctx.messages is not None else id(ctx)
    with _TOOL_GUARD_LOCK:
        if run_key not in _TOOL_CALLS_BY_RUN:
            _TOOL_CALLS_BY_RUN[run_key] = set()
            _TOOL_RUN_ORDER.append(run_key)
            while len(_TOOL_RUN_ORDER) > _TOOL_GUARD_MAX_RUNS:
                old_key = _TOOL_RUN_ORDER.popleft()
                _TOOL_CALLS_BY_RUN.pop(old_key, None)

        called = _TOOL_CALLS_BY_RUN[run_key]
        if tool_name in called:
            return False
        called.add(tool_name)
        return True


def store_incident(
    ctx: RunContext[None],
    severity: SeverityLevel,
    summary: str,
    rationale: str,
    customer_text: str,
) -> dict:
    """Store the incident in DynamoDB.

    Args:
        severity: The severity (P1-P4).
        summary: One-sentence summary of the issue.
        rationale: Short reasoning for the severity.
        customer_text: Original customer-reported problem text.
    """
    if not _should_execute_tool(ctx, "store_incident"):
        print("[tool] Skipping duplicate store_incident call")
        return {"skipped": True, "reason": "duplicate_call"}

    table_name = os.getenv(INCIDENTS_TABLE_ENV) or os.getenv("INCIDENTS_TABLE")
    if not table_name:
        raise RuntimeError(
            f"Missing {INCIDENTS_TABLE_ENV} env var (or INCIDENTS_TABLE)."
        )

    incident_id = str(uuid.uuid4())
    item = {
        "incident_id": incident_id,
        "created_at": _utc_now_iso(),
        "severity": severity,
        "summary": summary,
        "rationale": rationale,
        "customer_text": customer_text,
    }

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    table.put_item(Item=item)

    print(f"[tool] Stored incident {incident_id} in DynamoDB table {table_name}")
    return {"incident_id": incident_id, "table": table_name}


def notify_incident(
    ctx: RunContext[None],
    severity: SeverityLevel,
    summary: str,
    rationale: str,
    customer_text: str,
) -> dict:
    """Send an SNS notification about the incident.

    Args:
        severity: The severity (P1-P4).
        summary: One-sentence summary of the issue.
        rationale: Short reasoning for the severity.
        customer_text: Original customer-reported problem text.
    """
    if not _should_execute_tool(ctx, "notify_incident"):
        print("[tool] Skipping duplicate notify_incident call")
        return {"skipped": True, "reason": "duplicate_call"}

    topic_arn = os.getenv(INCIDENTS_TOPIC_ENV) or os.getenv("INCIDENTS_TOPIC")
    if not topic_arn:
        raise RuntimeError(
            f"Missing {INCIDENTS_TOPIC_ENV} env var (or INCIDENTS_TOPIC)."
        )

    subject = f"Incident {severity}: {summary}"
    if len(subject) > 100:
        subject = subject[:97] + "..."

    message = "\n".join(
        [
            f"Severity: {severity}",
            f"Summary: {summary}",
            f"Rationale: {rationale}",
            f"Customer Text: {customer_text}",
            f"Timestamp (UTC): {_utc_now_iso()}",
        ]
    )

    sns = boto3.client("sns")
    response = sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
    message_id = response.get("MessageId")

    print(f"[tool] Sent SNS notification {message_id} to {topic_arn}")
    return {"message_id": message_id, "topic_arn": topic_arn}


def build_agent() -> Agent[SeverityResult]:
    model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

    model = BedrockConverseModel(
        model_id,
        settings=ModelSettings(temperature=0),
    )

    agent = Agent(
        model,
        output_type=SeverityResult,
        instructions=SEVERITY_INSTRUCTIONS,
        output_retries=2,
        end_strategy="exhaustive",
    )

    agent.tool(store_incident)
    agent.tool(notify_incident)
    return agent


agent = build_agent()
app = agent.to_a2a()
