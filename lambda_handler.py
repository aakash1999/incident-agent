import json

from app import build_agent

agent = build_agent()


def handler(event, context):
    # Accept common payload shapes: {"text": "..."} or API Gateway body
    text = None
    if isinstance(event, dict):
        text = event.get("text") or event.get("input")
        if not text and isinstance(event.get("body"), str):
            try:
                body = json.loads(event["body"])
                text = body.get("text") or body.get("input")
            except json.JSONDecodeError:
                text = event["body"]

    if not text:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'text' in request."}),
        }

    result = agent.run_sync(text)
    return {
        "statusCode": 200,
        "body": result.output.model_dump_json(),
    }
