from dataclasses import dataclass

from .agent import Agent
from .scenario import Scenario

@dataclass
class Test:
    """A test represents a scenario and an agent to test the scenario with

    Attributes:
        scenario (Scenario): The scenario to test
        agent (Agent): The agent to test with
    """
    scenario: Scenario
    agent: Agent