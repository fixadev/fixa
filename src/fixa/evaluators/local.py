import os
from typing import List, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from pydantic import BaseModel
from fixa.evaluators.evaluator import BaseEvaluator, EvaluationResult
from fixa.scenario import Scenario
from dotenv import load_dotenv

load_dotenv(override=True)


class EvaluationResults(BaseModel):
    results: List[EvaluationResult]

class LocalEvaluator(BaseEvaluator):
    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "")
        self.model = model
    
    def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam], stereo_recording_url: str) -> Optional[List[EvaluationResult]]:
        """Evaluate a call locally.
        Args:
            scenario (Scenario): Scenario to evaluate
            transcript (List[ChatCompletionMessageParam]): Transcript of the call
            stereo_recording_url (str): URL of the stereo recording of the call
        Returns:
            Optional[List[EvaluationResult]]: List of evaluation results, or None if the evaluation failed
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": f"Evaluate the following transcript against these criteria:\n{[e.__dict__ for e in scenario.evaluations]}"},
            {"role": "user", "content": f"Transcript:\n{str(transcript)}"}
        ]
        
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            temperature=0,
            max_tokens=100,
            response_format=EvaluationResults,
        )

        parsed = response.choices[0].message.parsed
        if parsed is None:
            return None
        return parsed.results
