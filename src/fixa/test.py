from .agent import Agent
from .scenario import Scenario

class Test:
    def __init__(self, scenario: Scenario, agent: Agent):
        """Initialize a Test.
        
        Args:
            scenario (Scenario): The scenario to test
            agent (Agent): The agent to test with
        """
        self.scenario = scenario
        self.agent = agent
    
    def run(self):
        """Run the test scenario with the agent."""
        # Implementation to be added
        pass
