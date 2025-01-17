import requests
import uuid
from typing import List
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from fixa.evaluators.evaluator import Scenario


class CloudEvaluator():
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key:
            raise ValueError("fixa-observe API key required for cloud evaluator")
    
    def evaluate_call(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam | ChatCompletionToolParam], stereo_recording_url: str) -> bool:
        """Evaluate a call using fixa-observe.
        Args:
            scenario (Scenario): Scenario to evaluate
            transcript (List[ChatCompletionMessageParam | ChatCompletionToolParam]): Transcript of the call
            stereo_recording_url (str): URL of the stereo recording to evaluate
        Returns:
            bool: True if all evaluations passed, False otherwise
        """
        response = requests.post(
            f"https://api.fixa.dev/v1/upload-call",
            json={
                "callId": uuid.uuid4(),
                "scenario": scenario,
                "transcript": transcript,
                "stereoRecordingUrl": stereo_recording_url,
            },
            headers={
                "Authorization": f"Bearer {self.api_key}"
            }
        )
