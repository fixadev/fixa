import os
import sys

from openai.types.chat import ChatCompletionMessageParam

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import EndFrame
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

from fixa.scenario import Scenario

class Agent:
    def __init__(self, *, prompt: str, voice_id: str):
        """Initialize an Agent.
        
        Args:
            prompt (str): The system prompt for the agent
            voice_id (str): The cartesia voice id for the agent
        """
        self.prompt = prompt
        self.voice_id = voice_id 


    async def run_bot(self, scenario: Scenario, websocket_client, stream_sid):
        transport = FastAPIWebsocketTransport(
            websocket=websocket_client,
            params=FastAPIWebsocketParams(
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
                serializer=TwilioFrameSerializer(stream_sid),
            ),
        )

        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY") or "", model="gpt-4o")

        stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY") or "")

        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY") or "",
            voice_id=self.voice_id,
        )

        messages: list[ChatCompletionMessageParam] = [
            # {
            #     "role": "system",
            #     "content": "You are a helpful LLM in an audio call. Your goal is to demonstrate your capabilities in a succinct way. Your output will be converted to audio so don't include special characters in your answers. Respond to what the user said in a creative and helpful way.",
            # },
            {
                "role": "system",
                "content": self.prompt,
            },
            {
                "role": "system",
                "content": scenario.prompt,
            },
        ]

        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        pipeline = Pipeline(
            [
                transport.input(),  # Websocket input from client
                stt,  # Speech-To-Text
                context_aggregator.user(),
                llm,  # LLM
                tts,  # Text-To-Speech
                transport.output(),  # Websocket output to client
                context_aggregator.assistant(),
            ]
        )

        task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            # Kick off the conversation.
            messages.append({"role": "system", "content": "your first response should be an empty string. nothing else."})
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            await task.queue_frames([EndFrame()])

        runner = PipelineRunner(handle_sigint=False)

        await runner.run(task)
