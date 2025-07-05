#############################################################################
# summary_agent.py
#
# agent for reductive reasoning by inferring propositions from conversation
# and then summarizing the conversation
#
# @author Theodore Mui
# @email  theodoremui@gmail.com
# Fri Jul 04 11:30:53 PDT 2025
#############################################################################

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import argparse
import asyncio
from datetime import datetime
from typing import List

from llama_index.core.agent.workflow import FunctionAgent, AgentOutput
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.tools import FunctionTool
from llama_index.core.llms import LLM
from llama_index.core.memory import (
    Memory, InsertMethod
)
from llama_index.llms.openai import OpenAI

from asdrp.agent.base import AgentReply
from asdrp.memory.proposition_extraction_memory import PropositionExtractionMemoryBlock

class ReductiveAgent:
    def __init__(
        self,
        llm: LLM = OpenAI(model="gpt-4.1-mini"),
        memory: Memory = None,
        tools: List[FunctionTool] = [],
    ):
        self.llm = llm
        self.memory = memory
        self.agent = self._create_agent(memory, tools)

    async def achat(self, user_msg: str) -> AgentReply:
        try:
            # Prepend known propositions to the user message if available, with explicit instruction
            propositions = ""
            if self.memory and hasattr(self.memory, "memory_blocks"):
                for block in self.memory.memory_blocks:
                    if isinstance(block, PropositionExtractionMemoryBlock):
                        props = await block._aget()
                        if props:
                            propositions = (
                                "Known propositions from conversation so far:\n"
                                f"{props}\n"
                                "When answering, reference the known propositions above if relevant.\n"
                            )
            full_msg = propositions + user_msg
            response = await self.agent.run(user_msg=full_msg, memory=self.memory)
            if isinstance(response, AgentOutput):
                return AgentReply(response_str=response.response.content)
            elif isinstance(response, ChatMessage):
                return AgentReply(response_str=response.content)
            else:
                return AgentReply(response_str=str(response))
        except Exception as e:
            print(f"Error in ReductiveAgent: {e}")
            return AgentReply(response_str="I'm sorry, I'm having trouble processing your request. Please try again.")

    def _create_agent(self, memory: Memory, tools: List[FunctionTool]) -> FunctionAgent:
        return FunctionAgent(
            llm=self.llm,
            memory=memory,
            tools=tools,
        )
        
    def _create_memory(self) -> Memory:
        proposition_extraction_memory = PropositionExtractionMemoryBlock(
            name="proposition_extraction_memory",
            llm=self.llm,
            max_propositions=50,
        )
        return Memory.from_defaults(
            session_id="proposition_agent",
            token_limit=50,                       # size of the entire working memory 
            chat_history_token_ratio=0.7,         # ratio of chat history to total tokens
            token_flush_size=10,                  # number of tokens to flush when memory is full
            insert_method=InsertMethod.SYSTEM,
            memory_blocks=[proposition_extraction_memory]
        )
    

#-----------------------------------------
# Main: proposition extraction smoke tests
#-----------------------------------------

def print_result(test_name, passed):
    print(f"{test_name}: {'PASSED' if passed else 'FAILED'}")

async def smoke_test_proposition_extraction():
    """Test that propositions are extracted and stored from user input."""
    memory = ReductiveAgent()._create_memory()
    agent = ReductiveAgent(memory=memory)
    await agent.achat("I believe the sky is blue.")
    # Find the proposition block
    block = None
    for b in getattr(memory, "memory_blocks", []):
        if isinstance(b, PropositionExtractionMemoryBlock):
            block = b
            break
    props = await block._aget() if block else ""
    passed = ("sky is blue" in props) or ("Sky is blue" in props)
    print_result("Proposition extraction", passed)
    print(f"Extracted propositions: {props}")

async def smoke_test_proposition_deduplication():
    """Test that duplicate propositions are not stored multiple times."""
    memory = ReductiveAgent()._create_memory()
    agent = ReductiveAgent(memory=memory)
    await agent.achat("I believe the sky is blue.")
    await agent.achat("I believe the sky is blue.")
    block = None
    for b in getattr(memory, "memory_blocks", []):
        if isinstance(b, PropositionExtractionMemoryBlock):
            block = b
            break
    props = await block._aget() if block else ""
    count = props.count("sky is blue") + props.count("Sky is blue")
    passed = count == 1
    print_result("Proposition deduplication", passed)
    print(f"Extracted propositions: {props}")

async def smoke_test_multiple_propositions():
    """Test that multiple distinct propositions are extracted and stored."""
    memory = ReductiveAgent()._create_memory()
    agent = ReductiveAgent(memory=memory)
    await agent.achat("The sky is blue. Water is wet.")
    block = None
    for b in getattr(memory, "memory_blocks", []):
        if isinstance(b, PropositionExtractionMemoryBlock):
            block = b
            break
    props = await block._aget() if block else ""
    props_lower = props.lower()
    passed = ("sky is blue" in props_lower and "water is wet" in props_lower)
    print_result("Multiple proposition extraction", passed)
    print(f"Extracted propositions: {props}")

async def smoke_test_proposition_limit():
    """Test that the max_propositions limit is respected."""
    block = PropositionExtractionMemoryBlock(
        name="proposition_extraction_memory",
        llm=OpenAI(model="gpt-4.1-mini"),
        max_propositions=2,
    )
    memory = Memory.from_defaults(
        session_id="test_session",
        token_limit=50,
        memory_blocks=[block],
    )
    agent = ReductiveAgent(memory=memory)
    await agent.achat("It is a fact that the sky is blue.")
    print("After 1st achat:", await block._aget())
    await agent.achat("It is a fact that water is wet.")
    print("After 2nd achat:", await block._aget())
    await agent.achat("It is a fact that grass is green.")
    props = await block._aget()
    print("After 3rd achat:", props)
    count = props.count("<proposition>")
    passed = count == 2
    print_result("Proposition limit respected", passed)
    print(f"Extracted propositions: {props}")

async def smoke_test_agent_reply_includes_propositions():
    """Test that the agent can reference extracted propositions in its reply."""
    memory = ReductiveAgent()._create_memory()
    agent = ReductiveAgent(memory=memory)
    await agent.achat("I believe the sky is blue.")
    reply = await agent.achat("What do you know about the sky?")
    passed = ("sky is blue" in reply.response_str) or ("Sky is blue" in reply.response_str)
    print_result("Agent reply references proposition", passed)
    print(f"Agent reply: {reply.response_str}")

async def main():
    await smoke_test_proposition_extraction()
    await smoke_test_proposition_deduplication()
    await smoke_test_multiple_propositions()
    await smoke_test_proposition_limit()
    await smoke_test_agent_reply_includes_propositions()
    print("All proposition extraction smoke tests completed.")

if __name__ == "__main__":
    asyncio.run(main())
    
