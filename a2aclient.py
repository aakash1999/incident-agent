import asyncio, json, uuid
from fasta2a.client import A2AClient

async def main():
    client = A2AClient("http://localhost:8000")
    message = {
        "role": "user",
        "parts": [{"kind": "text", "text": "Billing page loads but checkout fails for some users."}],
        "kind": "message",
        "message_id": str(uuid.uuid4()),
    }
    resp = await client.send_message(
        message,
        configuration={"accepted_output_modes": ["application/json"], "blocking": True},
    )
    # If structured output is present, it will appear as a DataPart artifact
    result = resp.get("result", resp)
    artifacts = result.get("artifacts", [])
    data_parts = [
        part["data"]
        for artifact in artifacts
        for part in artifact.get("parts", [])
        if part.get("kind") == "data"
    ]
    print(json.dumps(data_parts[0] if data_parts else result, indent=2))

asyncio.run(main())