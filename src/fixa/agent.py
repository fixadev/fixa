class Agent:
    def __init__(self, *, prompt: str, voice_id: str):
        """Initialize an Agent.
        
        Args:
            prompt (str): The system prompt for the agent
            voice_id (str): The cartesia voice id for the agent
        """
        self.prompt = prompt
        self.voice_id = voice_id 