from abc import ABC, abstractmethod
import os
import uuid
import requests
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from pydantic import BaseModel

from fixa.scenario import Scenario

class EvaluationResult(BaseModel):
    name: str
    passed: bool
    reason: str

class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(self, scenario: Scenario, transcript: List[ChatCompletionMessageParam], stereo_recording_url: str) -> Optional[List[EvaluationResult]]:
        raise NotImplementedError
