import json
import logging
import uvicorn
from fixa.bot import run_bot
from fixa.scenario import Scenario
from fixa.agent import Agent
from fastapi import FastAPI, WebSocket, Form
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
import os 
from pydantic import BaseModel, Field
import argparse
from typing import Dict, Tuple, List, Literal, Optional
from typing_extensions import TypedDict
from openai.types.chat import ChatCompletionMessageParam

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables
twilio_client: Optional[Client] = None
port: Optional[int] = None
ngrok_url: Optional[str] = None

def set_args(server_port: int, server_ngrok_url: str):
    """Set the server arguments."""
    global port, ngrok_url
    port = server_port
    ngrok_url = server_ngrok_url

def set_twilio_client(client: Client):
    """Set the Twilio client."""
    global twilio_client
    twilio_client = client

# Store scenarios and agents by call_sid
active_pairs: Dict[str, Tuple[Scenario, Agent]] = {}

class CallStatus(TypedDict):
    status: Literal["in_progress", "completed", "error"]
    transcript: Optional[List[ChatCompletionMessageParam]]
    stereo_recording_url: Optional[str]
    error: Optional[str]

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
    assert ngrok_url is not None
    ws_url = ngrok_url.replace('https://', '')
    return f"<Response><Connect><Stream url='wss://{ws_url}/ws'></Stream></Connect><Pause length='10'/></Response>"

class OutboundCallRequest(BaseModel):
    to: str
    from_: str = Field(alias='from')
    scenario_prompt: str
    agent_prompt: str
    agent_voice_id: str = "79a125e8-cd45-4c13-8a67-188112f4dd22"  # Default to British Lady

class TranscriptRequest(BaseModel):
    call_sid: str
    transcript: List[ChatCompletionMessageParam]

class RecordingRequest(BaseModel):
    RecordingUrl: str
    CallSid: str

@app.get("/status")
async def status():
    return call_status

@app.post("/outbound")
async def outbound_call(request: OutboundCallRequest):
    assert twilio_client is not None, "Twilio client not initialized"
    assert ngrok_url is not None, "ngrok URL not set"
    
    call = twilio_client.calls.create(
        record=True,
        recording_channels="dual",
        recording_status_callback=f"{ngrok_url}/recording",
        to=request.to,
        from_=request.from_,
        twiml=get_stream_twiml(),
    )
    call_sid = call.sid
    if call_sid is None:
        raise ValueError("Call SID is None")
        
    # Create scenario and agent
    scenario = Scenario(name="outbound_call", prompt=request.scenario_prompt)
    agent = Agent(name="agent", prompt=request.agent_prompt, voice_id=request.agent_voice_id)
    
    # Store them for this call
    active_pairs[call_sid] = (scenario, agent)

    # Set the status to in_progress
    call_status[call_sid] = {
        "status": "in_progress",
        "transcript": None,
        "stereo_recording_url": None,
        "error": None
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
        transcript = await run_bot(agent, scenario, websocket, stream_sid, call_sid)
        call_status[call_sid] = {
            "status": "completed",
            "transcript": transcript,
            "stereo_recording_url": None,
            "error": None
        }
    except Exception as e:
        logger.error(f"Bot failed for call {call_sid}: {str(e)}")
        call_status[call_sid] = {
            "status": "error",
            "transcript": None,
            "stereo_recording_url": None,
            "error": str(e)
        }
    finally:
        del active_pairs[call_sid]

@app.post("/recording")
async def recording(RecordingSid: str = Form(), RecordingUrl: str = Form(), CallSid: str = Form()):
    logger.info(f"Recording SID: {RecordingSid}, Recording URL: {RecordingUrl}, Call SID: {CallSid}")
    if CallSid in call_status:
        # Format the recording URL with authentication credentials
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        base_url = RecordingUrl.replace("https://", "")
        authenticated_url = f"https://{account_sid}:{auth_token}@{base_url}"
        call_status[CallSid]["stereo_recording_url"] = authenticated_url
        if call_status[CallSid]["status"] != "completed":
            # If recording is received before call is completed, mark as error
            call_status[CallSid]["status"] = "error"
            call_status[CallSid]["error"] = "agent failed to start"
    return {"success": True}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--ngrok_url", type=str, required=True)
    parsed_args = parser.parse_args()
    
    set_args(parsed_args.port, parsed_args.ngrok_url)
    set_twilio_client(Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")))
    
    assert port is not None, "Port not set"
    uvicorn.run(app, host="0.0.0.0", port=port)

# python server.py --port 8765