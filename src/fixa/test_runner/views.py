from dataclasses import dataclass
from typing import List, Optional
from fixa.test import Test
from fixa.evaluators.evaluator import EvaluationResponse
from openai.types.chat import ChatCompletionMessageParam

@dataclass
class TestResult():
    """Result of a test.

    Attributes:
        test (Test): The test that was run
        evaluation_results (Optional[EvaluationResponse]): The evaluation results of the test
        transcript (List[ChatCompletionMessageParam]): The transcript of the test
        stereo_recording_url (str): The URL of the stereo recording of the test
        error (str | None): The error that occurred during the test
    """
    test: Test
    evaluation_results: Optional[EvaluationResponse]
    transcript: List[ChatCompletionMessageParam]
    stereo_recording_url: str
    error: str | None = None