from dataclasses import dataclass

@dataclass
class Evaluation:
    """An evaluation represents a criterion for evaluating a scenario.

    Attributes:
        name (str): Name of the evaluation criterion
        prompt (str): Prompt to evaluate the scenario
    """
    name: str
    prompt: str