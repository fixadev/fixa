import asyncio
from dataclasses import asdict
import uuid
from typing import List, Optional
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from fixa.evaluators.evaluator import BaseEvaluator, EvaluationResponse, EvaluationResult
from fixa.scenario import Scenario
import aiohttp
import json

api_url = "https://api.fixa.dev/v1"

class CloudEvaluator(BaseEvaluator):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key:
            raise ValueError("fixa-observe API key required for cloud evaluator")
    
    async def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam], stereo_recording_url: str) -> Optional[EvaluationResponse]:
        """Evaluate a call using fixa-observe.
        Args:
            scenario (Scenario): Scenario to evaluate
            transcript (List[ChatCompletionMessageParam | ChatCompletionToolParam]): Transcript of the call
            stereo_recording_url (str): URL of the stereo recording to evaluate
        Returns:
            bool: True if all evaluations passed, False otherwise
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/upload-call",
                json={
                    "callId": str(uuid.uuid4()),
                    "agentId": "test",
                    "scenario": asdict(scenario),
                    "transcript": transcript,
                    "stereoRecordingUrl": stereo_recording_url,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                }
            ) as response:
                data = await response.json()
                if not data["success"]:
                    raise Exception(f"Failed to upload call: {data}")
                call_id = data["callId"]

            max_retries = 10
            retries = 0
            await asyncio.sleep(5)
            while retries < max_retries:
                async with session.get(
                    f"{api_url}/calls/{call_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                ) as response:
                    if response.status == 200:
                        results = await response.json()
                        evaluation_results = results["call"]["evaluationResults"]
                        return EvaluationResponse(
                            evaluation_results=[EvaluationResult(name=r["evaluation"]["evaluationTemplate"]["name"], passed=r["success"], reason=r["details"]) for r in evaluation_results],
                            extra_data={
                               "fixa_observe_call_url": f"https://www.fixa.dev/observe/calls/{call_id}"
                            }
                        )
                    
                    # Wait a bit before polling again
                    await asyncio.sleep(2)
                    retries += 1

        # failed to get call results!
        raise Exception("Failed to get call results")