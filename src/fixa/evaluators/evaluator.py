import os
import uuid
import requests
from enum import Enum
from typing import List
from dataclasses import dataclass
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from pydantic import BaseModel

class Evaluation:
    def __init__(self, name: str, prompt: str):
        self.name = name
        self.prompt = prompt

class Scenario:
    def __init__(self, name: str, prompt: str, evaluations: List[Evaluation]):
        self.name = name
        self.prompt = prompt
        self.evaluations = evaluations

class EvaluationResult(BaseModel):
    name: str
    passed: bool
    reason: str

class EvaluationResults(BaseModel):
    results: List[EvaluationResult]
class Evaluator:
    def __init__(self, api_key: str | None = None):
        """Initialize an Evaluator.
        Args:
            type (EvaluatorType): Type of evaluator (local or fixa-observe)
            api_key (str, optional): API key required for fixa-observe evaluator
        """
    
    

        
        

        



        



