import os
from typing import List
import asyncio

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from twilio.rest import Client

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame, EndTaskFrame
from pipecat.processors.frame_processor import FrameDirection
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from loguru import logger
import sys

from fixa.scenario import Scenario
from fixa.agent import Agent

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

class Bot:
    def __init__(self, websocket_client, stream_sid, call_sid):
        self.websocket_client = websocket_client
        self.stream_sid = stream_sid
        self.call_sid = call_sid
        self.twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self.task = None
        self.transport = None

    def get_end_call_twiml(self):
        return "<Response><Hangup/></Response>"

    async def end_call(self, function_name, tool_call_id, args, llm, context, result_callback):
        print("ending call!")
        self.twilio_client.calls(self.call_sid).update(twiml=self.get_end_call_twiml())
        await llm.push_frame(EndTaskFrame(), FrameDirection.UPSTREAM)

    async def on_client_connected(self, transport, client):
        assert self.task is not None

        # Kick off the conversation.
        # self.messages.append({"role": "system", "content": "your first response should be an empty string. nothing else."})
        # await self.task.queue_frames([self.context_aggregator.user().get_context_frame()])

    async def on_client_disconnected(self, transport, client):
        assert self.task is not None

        await self.task.queue_frames([EndFrame()])

    async def run(self, agent: Agent, scenario: Scenario):
        self.transport = FastAPIWebsocketTransport(
            websocket=self.websocket_client,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=TwilioFrameSerializer(self.stream_sid),
            ),
        )

        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY") or "", model="gpt-4o")
        llm.register_function("end_call", self.end_call)

        tools = [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": "end_call",
                    "description": "ends the call",
                },
            )
        ]

        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY") or "")
        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY") or "",
            voice_id=agent.voice_id,
        )

        self.messages: List[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": agent.prompt,
            },
            {
                "role": "system",
                "content": scenario.prompt,
            },
            {
                "role": "system",
                "content": "end the call if the user says goodbye",
            },
        ]

        context = OpenAILLMContext(self.messages, tools)
        self.context_aggregator = llm.create_context_aggregator(context)

        pipeline = Pipeline(
            [
                self.transport.input(),
                stt,
                self.context_aggregator.user(),
                llm,
                tts,
                self.transport.output(),
                self.context_aggregator.assistant(),
            ]
        )

        self.task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

        self.transport.event_handler("on_client_connected")(self.on_client_connected)
        self.transport.event_handler("on_client_disconnected")(self.on_client_disconnected)

        runner = PipelineRunner(handle_sigint=False)
        await runner.run(self.task) 

        return self.messages

async def run_bot(agent: Agent, scenario: Scenario, websocket_client, stream_sid, call_sid):
    bot = Bot(websocket_client, stream_sid, call_sid)
    try:
        transcript = await bot.run(agent, scenario)
        return transcript
    except asyncio.CancelledError:
        # print("Bot run cancelled")
        return None
