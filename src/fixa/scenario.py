from typing import List
from .evaluation import Evaluation

class Scenario:
    def __init__(self, *, system_prompt: str, evaluations: List[Evaluation] = []):
        """Initialize a Scenario.
        
        Args:
            system_prompt (str): The system prompt for the scenario
            evaluations (List[Evaluation], optional): List of evaluations for this scenario
        """
        self.system_prompt = system_prompt
        self.evaluations = evaluations