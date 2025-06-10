#------------------------------------------------------------------------------
# webreasoner.py
# 
# This agent can lookup real time web and the latest information & news about general topics.
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------

from agents import (
    Agent, ModelSettings, Runner, Tool,
    trace, gen_trace_id
)
from agents.tool import WebSearchTool
from agents.tracing import set_tracing_disabled
from loguru import logger
import datetime

from bioagents.models.llms import LLM
from bioagents.agents.base_agent import ReasoningAgent
from bioagents.agents.common import AgentResponse
set_tracing_disabled(disabled=True)

WEB_REASONING_INSTRUCTIONS = f"""
You are an expert about the real time web and the latest information & news about general topics.
Your response should include relevant inline citations.\n
Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')}.\n
Respond in the same language as the question.
"""

class WebReasoningAgent(ReasoningAgent):
    """
    This agent can lookup real time web and the latest information & news about general topics.
    """
    def __init__(
        self, name: str, 
        model_name: str=LLM.GPT_4_1_MINI, 
    ):
        self.instructions = WEB_REASONING_INSTRUCTIONS
        super().__init__(name, model_name, self.instructions)
        self._agent = self._create_agent(name, model_name)

    def _create_agent(self, agent_name: str, model_name: str=LLM.GPT_4_1_MINI):
        agent = Agent(
            name=agent_name,
            model=model_name,
            instructions=self.instructions,
            handoff_description="You are an expert about the real time web and the latest information & news about general topics.",
            tools=[WebSearchTool(
                search_context_size="low"
            )],
            model_settings=ModelSettings(
                tool_choice="required",
            ),
            tool_use_behavior="stop_on_first_tool",
        )
        return agent
    
    async def achat(self, query_str: str) -> AgentResponse:
        logger.info(f"-> {self.name}: {query_str}")

        run_result = await Runner.run(
            starting_agent=self._agent,
            input=query_str,
            max_turns=3,
        )
        
        return self._construct_response(run_result, "", "web")


#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio
    
    agent = WebReasoningAgent(name="Web Reasoning Agent")
    response = asyncio.run(agent.achat("What can you tell me about the disease measles?"))
    print(str(response))
    