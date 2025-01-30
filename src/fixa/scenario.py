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

    # def __init__(self, *, name: str, prompt: str, evaluations: List[Evaluation] = []):
    #     """Initialize a Scenario.
        
    #     Args:
    #         name (str): The name of the scenario
    #         prompt (str): The system prompt for the scenario
    #         evaluations (List[Evaluation], optional): List of evaluations for this scenario
    #     """
    #     self.name = name
    #     self.prompt = prompt
    #     self.evaluations = evaluations

    # def to_dict(self):
    #     return {
    #         "name": self.name,
    #         "prompt": self.prompt,
    #         "evaluations": [e.to_dict() for e in self.evaluations]
    #     }

    # def __repr__(self):
    #     return f"Scenario(name='{self.name}', prompt='{self.prompt}', evaluations={self.evaluations})"
