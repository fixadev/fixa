import requests
import uuid
from typing import List
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from fixa.evaluators.evaluator import BaseEvaluator, EvaluationResult
from fixa.scenario import Scenario
import aiohttp


class CloudEvaluator(BaseEvaluator):
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key:
            raise ValueError("fixa-observe API key required for cloud evaluator")
    
    async def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam], stereo_recording_url: str) -> List[EvaluationResult]:
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
                f"https://api.fixa.dev/v1/upload-call",
                json={
                    "callId": str(uuid.uuid4()),
                    "scenario": scenario,
                    "transcript": transcript,
                    "stereoRecordingUrl": stereo_recording_url,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                }
            ) as response:
                await response.json()

        return []