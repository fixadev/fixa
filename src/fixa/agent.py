from dataclasses import dataclass

@dataclass
class Agent:
    """An agent represents a conversational entity with a name, system prompt, and voice configuration.

    Attributes:
        name (str): The name of the agent
        prompt (str): The system prompt that defines the agent's behavior and role
        voice_id (str): The cartesia voice id for the agent (defaults to a british lady)
    """
    name: str
    prompt: str
    voice_id: str = "79a125e8-cd45-4c13-8a67-188112f4dd22"