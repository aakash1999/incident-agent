# incident-agent
An Intelligent AI Code based agent using Pydantic AI and AWS Bedrock. To build this along with me please follow my channel Peace Of Code in youtube. 

FYI - This Readme will be updated as we keep building the agent.

# Steps to Run the Agent in Local
1. First Create virtual env in python and install the dependencies
Python3 -m venv myenv

source myenv/bin/activate

Pip3 install -r requirements.txt

2. Run the app
uvicorn app:app --host 0.0.0.0 --port 8000

3. Test the agent:
Agent Card:
postman request 'http://localhost:8000/.well-known/agent-card.json'

Call the agent with a query/customer complaint:
postman request POST 'http://localhost:8000/' \
  --header 'Content-Type: application/json' \
  --header 'Accept: application/json' \
  --body '{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "kind": "message",
      "messageId": "msg-1",
      "parts": [
        { "kind": "text", "text": "All checkout payments are failing across regions; no workaround.THere is a huge outage" }
      ]
    },
    "configuration": {
      "acceptedOutputModes": ["application/json"]
    }
  }
}
'

Get the task ID then check the status of the task:
postman request POST 'http://localhost:8000/' \
  --header 'Content-Type: application/json' \
  --body '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tasks/get",
    "params": {
      "id": "965e691b-e095-41f7-9bb0-e1f558a81fb9"
    }
  }'