import os

from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.settings import ModelSettings

from models import SeverityResult

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
""".strip()


def build_agent() -> Agent[SeverityResult]:
    model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

    model = BedrockConverseModel(
        model_id,
        settings=ModelSettings(temperature=0),
    )

    return Agent(
        model,
        output_type=SeverityResult,
        instructions=SEVERITY_INSTRUCTIONS,
        output_retries=2,
    )


agent = build_agent()
app = agent.to_a2a()
