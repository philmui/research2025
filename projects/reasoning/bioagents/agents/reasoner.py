#------------------------------------------------------------------------------
# reasoner.py
# 
# This is the base class for all reasoning agents. It provides a common interface
# for all reasoning agents.
# 
# Author: Theodore Mui
# Date: 2025-04-26
#------------------------------------------------------------------------------
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from agents import RunResult
from loguru import logger

from bioagents.models.citation import Citation
from bioagents.models.llms import LLM
from bioagents.agents.base import AgentResponse

class ReasoningAgent:
    def __init__(
        self, name: str, 
        model_name: str=LLM.GPT_4_1_MINI, 
        instructions: str="You are a reasoning conversational agent."
    ):
        self.name = name
        self.llm = LLM(model_name)
        self.instructions = instructions

    def _construct_response(
        self, 
        run_result: RunResult,
        judge_response: str = "",
        route: str = ""
    ) -> AgentResponse:
        citations = []
        for item in run_result.new_items:
            if item.type == 'message_output_item':
                for content in item.raw_item.content:
                    if hasattr(content, 'annotations'):
                        for annotation in content.annotations:
                            if annotation.type == 'url_citation':
                                citations.append(Citation(
                                    url=annotation.url,
                                    title=annotation.title,
                                    snippet=content.text[annotation.start_index:annotation.end_index],
                                    source="web"
                                ))
        
        return AgentResponse(
            response_str=run_result.final_output,
            citations=citations,
            judge_response=judge_response,
            route=route
        )
        
    async def achat(self, query_str: str) -> AgentResponse:
        logger.info(f"-> {self.name}: {query_str}")
        prompt = (f"You are {self.name}. {self.instructions}\n\n"
                  f"User query: {query_str}")
        response = await self.llm.achat_completion(query_str=prompt)
        return AgentResponse(response, [], "", "")
    
#------------------------------------------------
# Example usage
#------------------------------------------------
if __name__ == "__main__":
    import asyncio
    
    agent = ReasoningAgent(name="ReasoningAgent")
    response = asyncio.run(agent.achat("What is the capital of the moon?"))
    print(str(response))
    