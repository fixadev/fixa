from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from fixa.scenario import Scenario

class EvaluationResult(BaseModel):
    name: str
    passed: bool
    reason: str

class EvaluationResponse(BaseModel):
    evaluation_results: List[EvaluationResult]
    extra_data: Dict[str, Any]

class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam], stereo_recording_url: str) -> Optional[EvaluationResponse]:
        raise NotImplementedError
