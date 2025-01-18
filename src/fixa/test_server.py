import json
import logging
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
from typing import Dict, Tuple, Any, List, Literal, Optional
from typing_extensions import TypedDict
from openai.types.chat import ChatCompletionMessageParam

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Store scenarios and agents by call_sid
active_pairs: Dict[str, Tuple[Scenario, Agent]] = {}

class CallStatus(TypedDict):
    status: Literal["in_progress", "completed", "error"]
    messages: Optional[List[ChatCompletionMessageParam]]

# Mapping from call_sid to status
call_status: Dict[str, CallStatus] = {}

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

@app.get("/status")
async def status():
    return call_status

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

    # Set the status to in_progress
    call_status[call_sid] = {
        "status": "in_progress",
        "messages": None,
    }
    logger.info(f"OUTBOUND CALL {call_sid} to {request.to}")
    return {"success": True, "call_id": call_sid}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    start_data = websocket.iter_text()
    await start_data.__anext__()
    call_data = json.loads(await start_data.__anext__())
    stream_sid = call_data["start"]["streamSid"]
    call_sid = call_data["start"]["callSid"]
    logger.info(f"WebSocket connection accepted for call {call_sid}")
    
    # Get the scenario and agent for this call
    pair = active_pairs.get(call_sid)
    if not pair:
        logger.error(f"No scenario/agent pair found for call {call_sid}")
        return
        
    scenario, agent = pair
    try:
        messages = await run_bot(agent, scenario, websocket, stream_sid, call_sid)
        call_status[call_sid] = {
            "status": "completed",
            "messages": messages,
        }
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        call_status[call_sid] = {
            "status": "error",
            "messages": None,
        }
    finally:
        logger.info("============================================= BOT FINISHED =============================================")
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