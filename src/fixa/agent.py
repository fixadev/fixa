class Agent:
    def __init__(self, *, system_prompt: str, model: str, voice: str):
        """Initialize an Agent.
        
        Args:
            system_prompt (str): The system prompt for the agent
            model (str): The model to use for the agent
            voice (str): The voice identifier for the agent
        """
        self.system_prompt = system_prompt
        self.model = model
        self.voice = voice 