import os
from typing import List
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from fixa.evaluators.evaluator import Scenario, EvaluationResults
from dotenv import load_dotenv

load_dotenv(override=True)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "")

class LocalEvaluator():
    def __init__(self):
        pass
    
    def evaluate_call(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam | ChatCompletionToolParam]) -> Scenario:
        """Evaluate a call locally.
        Args:
            scenario (Scenario): Scenario to evaluate
            transcript (List[ChatCompletionMessageParam | ChatCompletionToolParam]): Transcript of the call
        Returns:
            bool: True if all evaluations passed, False otherwise
        """
        messages = [
            {"role": "system", "content": f"Evaluate the following transcript against these criteria:\n{[e.__dict__ for e in scenario.evaluations]}"},
            {"role": "user", "content": f"Transcript:\n{str(transcript)}"}
        ]
        
        response = openai_client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            temperature=0,
            max_tokens=100,
            response_format=EvaluationResults,
        )

        return response.choices[0].message.parsed