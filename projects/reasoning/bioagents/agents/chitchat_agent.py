#------------------------------------------------------------------------------
# chitchat_agent.py
# 
# This is a "Chit Chat Agent" that can answer simple questions and provide
# a friendly conversational interface.
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------
from agents import Agent
from bioagents.agents.reasoner import ReasoningAgent
from bioagents.models.llms import LLM

class ChitChatAgent(ReasoningAgent):
    """
    This agent can answer simple questions and provide a friendly conversational interface.
    """
    def __init__(
        self, name: str, 
        model_name: str=LLM.GPT_4_1_MINI, 
        instructions = (
            "You are a friendly conversational assistant but you should be very brief and to the point."
            "You should not ask the user any questions"
        )
    ):
        super().__init__(name, model_name, instructions)
        self._agent = self._create_agent(name, model_name)

    def _create_agent(self, agent_name: str, model_name: str=LLM.GPT_4_1_MINI):
        agent = Agent(
            name=agent_name,
            model=model_name,
            instructions=self.instructions,
            handoffs=[],
            tools=[],
        )
        return agent

#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio

    agent = ChitChatAgent(name="Chit Chat Agent")
    response = asyncio.run(agent.achat("How are you?"))
    print(str(response))

