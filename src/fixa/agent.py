class Agent:
    def __init__(self, *, prompt: str, voice_id: str = "79a125e8-cd45-4c13-8a67-188112f4dd22"):
        """Initialize an Agent.
        
        Args:
            prompt (str): The system prompt for the agent
            voice_id (str): The cartesia voice id for the agent
        """
        self.prompt = prompt
        self.voice_id = voice_id 