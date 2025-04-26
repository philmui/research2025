#------------------------------------------------------------------------------
# bioreasoner.py
# 
# This is a "Bio Reasoning Agent" that triage across multiple agents to answer
# a user's question.  This agent orchestrates across the following subagents:
# 
# 1. Chit Chat Agent
# 2. Web Reasoning Agent
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------

from agents import (
    Agent,
    ModelSettings,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from bioagents.agents.chitchat_agent import ChitChatAgent
from bioagents.agents.webreasoner import WebReasoningAgent
from bioagents.models.llms import LLM
from bioagents.agents.reasoner import ReasoningAgent

class BioReasoningAgent(ReasoningAgent):
    def __init__(
        self, name: str, 
        model_name: str=LLM.GPT_4_1_MINI, 
    ):
        self.chit_chat_agent = ChitChatAgent(name="Chit Chat Agent")
        self.web_agent = WebReasoningAgent(name="Web Reasoning Agent")
        
        instructions = (
            "You are an expert about biology, medicine, genetics, and other life sciences."
            f"If the user is chit chatting, you should pass the conversation to the {self.chit_chat_agent.name}."
            f"If the user is asking about general information, news, or latest updates, "
            f"you should pass the conversation to the {self.web_agent.name}."
        )

        super().__init__(name, model_name, instructions)
        self._agent = self._create_agent(name, model_name)

    def _create_agent(self, agent_name: str, model_name: str=LLM.GPT_4_1_MINI):
        agent = Agent(
            name=agent_name,
            model=model_name,
            instructions=RECOMMENDED_PROMPT_PREFIX + self.instructions,
            handoffs=[
                self.chit_chat_agent._agent,
                self.web_agent._agent,
            ],
            tools=[],
        )
        return agent


#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio
    
    agent = BioReasoningAgent(name="Bio Reasoning Agent")
    response = asyncio.run(agent.achat("How are you?"))
    print(str(response))
