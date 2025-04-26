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
    RunContextWrapper,
    Runner,
    handoff
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from loguru import logger

from bioagents.agents.base import AgentResponse
from bioagents.agents.chitchat_agent import ChitChatAgent
from bioagents.agents.webreasoner import WebReasoningAgent
from bioagents.models.llms import LLM
from bioagents.agents.reasoner import ReasoningAgent

def on_handoff(ctx: RunContextWrapper):
    logger.info(f"handoff: {ctx}")

class BioReasoningAgent(ReasoningAgent):
    def __init__(
        self, name: str, 
        model_name: str=LLM.GPT_4_1_MINI, 
    ):
        self.chit_chat_agent = ChitChatAgent(name="Chit Chat Agent")
        self.web_agent = WebReasoningAgent(name="Web Reasoning Agent")
        
        instructions = (
            "You are an expert about biology, medicine, genetics, and other life sciences."
            f"If the user is chit chatting, you must always pass the conversation to the {self.chit_chat_agent.name}."
            f"If the user is asking about general information, news, or latest updates, "
            f"you must always pass the conversation to the {self.web_agent.name}."
        )

        super().__init__(name, model_name, instructions)
        self._agent = self._create_agent(name, model_name)

    def _create_agent(self, agent_name: str, model_name: str=LLM.GPT_4_1_MINI):
        agent = Agent(
            name=agent_name,
            # instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{self.instructions}",
            handoffs=[
                handoff(agent=self.chit_chat_agent._agent, on_handoff=on_handoff),
                handoff(agent=self.web_agent._agent, on_handoff=on_handoff),
            ],
        )
        return agent

    async def achat(self, query_str: str) -> AgentResponse:
        logger.info(f"-> {self.name}: {query_str}")

        run_result = await Runner.run(
            starting_agent=self._agent,
            input=query_str,
            max_turns=3,
        )
        
        return self._construct_response(run_result, "", "bioreasoner")

#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio
    import time
    
    start_time = time.time()
    agent = BioReasoningAgent(name="Bio")
    response = asyncio.run(agent.achat("How are you?"))
    print(f"{str(response)} ({time.time() - start_time:.1f}s)")
    
    start_time = time.time()
    response = asyncio.run(agent.achat("What is the latest news in the field of genetics?"))
    print(f"{str(response)} ({time.time() - start_time:.1f}s)")

    start_time = time.time()
    response = asyncio.run(agent.achat("How is the weather in Tokyo?"))
    print(f"{str(response)} ({time.time() - start_time:.1f}s)")