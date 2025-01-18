import os
from typing import List, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from fixa.evaluators.evaluator import BaseEvaluator, EvaluationResult
from fixa.scenario import Scenario
from dotenv import load_dotenv

load_dotenv(override=True)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "")

class LocalEvaluator(BaseEvaluator):
    def __init__(self):
        pass
    
    def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam | ChatCompletionToolParam], stereo_recording_url: str) -> Optional[List[EvaluationResult]]:
        """Evaluate a call locally.
        Args:
            scenario (Scenario): Scenario to evaluate
            transcript (List[ChatCompletionMessageParam | ChatCompletionToolParam]): Transcript of the call
        Returns:
            Optional[List[EvaluationResult]]: List of evaluation results, or None if the evaluation failed
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": f"Evaluate the following transcript against these criteria:\n{[e.__dict__ for e in scenario.evaluations]}"},
            {"role": "user", "content": f"Transcript:\n{str(transcript)}"}
        ]
        
        response = openai_client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=100,
            response_format=List[EvaluationResult],
        )

        return response.choices[0].message.parsed
