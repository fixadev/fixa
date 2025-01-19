class Evaluation:
    def __init__(self, *, name: str, prompt: str):
        """Initialize an Evaluation.
        
        Args:
            name (str): Name of the evaluation criterion
            prompt (str): Prompt to evaluate the scenario
        """
        self.name = name
        self.prompt = prompt

    def to_dict(self):
        return {
            "name": self.name,
            "prompt": self.prompt
        }
