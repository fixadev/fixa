from dataclasses import dataclass, field
from typing import List
from .evaluation import Evaluation

@dataclass
class Scenario:
    """A scenario represents a specific test case with a name, prompt, and associated evaluations.

    Attributes:
        name (str): The name of the scenario
        prompt (str): The system prompt used for this scenario
        evaluations (List[Evaluation]): List of evaluations performed for this scenario
    """
    name: str
    prompt: str
    evaluations: List[Evaluation] = field(default_factory=list)