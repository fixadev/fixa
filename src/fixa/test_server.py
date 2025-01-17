import json

import uvicorn
from fixa.bot import run_bot
from fixa.scenario import Scenario
from fixa.agent import Agent
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
import os 
from pydantic import BaseModel, Field
import argparse
from typing import Dict, Tuple

# Store scenarios and agents by call_sid
active_pairs: Dict[str, Tuple[Scenario, Agent]] = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_stream_twiml():
    """
    Returns the TwiML for the websocket stream.
    """
    ws_url = args.ngrok_url.replace('https://', '')
    return f"<Response><Connect><Stream url='wss://{ws_url}/ws'></Stream></Connect><Pause length='10'/></Response>"

class OutboundCallRequest(BaseModel):
    to: str
    from_: str = Field(alias='from')
    scenario_prompt: str
    agent_prompt: str
    agent_voice_id: str = "79a125e8-cd45-4c13-8a67-188112f4dd22"  # Default to British Lady

@app.post("/outbound")
async def outbound_call(request: OutboundCallRequest):
    call = twilio_client.calls.create(
        to=request.to,
        from_=request.from_,
        twiml=get_stream_twiml(),
    )
    call_sid = call.sid
    if call_sid is None:
        raise ValueError("Call SID is None")
        
    # Create scenario and agent
    scenario = Scenario(name="", prompt=request.scenario_prompt)
    agent = Agent(prompt=request.agent_prompt, voice_id=request.agent_voice_id)
    
    # Store them for this call
    active_pairs[call_sid] = (scenario, agent)
    print(f"OUTBOUND CALL {call_sid} to {request.to}")
    return {"success": True, "call_id": call_sid}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    start_data = websocket.iter_text()
    await start_data.__anext__()
    call_data = json.loads(await start_data.__anext__())
    print(call_data, flush=True)
    stream_sid = call_data["start"]["streamSid"]
    call_sid = call_data["start"]["callSid"]
    print(f"WebSocket connection accepted for call {call_sid}")
    
    # Get the scenario and agent for this call
    pair = active_pairs.get(call_sid)
    if not pair:
        print(f"No scenario/agent pair found for call {call_sid}")
        return
        
    scenario, agent = pair
    messages = await run_bot(agent, scenario, websocket, stream_sid, call_sid)
    print(messages)

    # Clean up
    del active_pairs[call_sid]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--ngrok_url", type=str, required=True)
    args = parser.parse_args()

    # Initialize Twilio client
    twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

    uvicorn.run(app, host="0.0.0.0", port=args.port)

# python server.py --port 8765