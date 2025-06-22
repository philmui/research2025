from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import argparse
import asyncio
from datetime import datetime
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import (
    Memory, StaticMemoryBlock, FactExtractionMemoryBlock, VectorMemoryBlock, InsertMethod
)
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context

llm = OpenAI(model="gpt-4o-mini")

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_current_weather(city: str):
    return f"The weather in {city} is sunny."

tools = [get_current_time, get_current_weather]

static_memory_block = StaticMemoryBlock(
    name="core_info",
    static_content="My name is MemAgent, and I live in San Francisco.  I am here to help ASDRP researhers",
    priority=0,
)

fact_extraction_memory_block = FactExtractionMemoryBlock(
    name="extracted_info",
    llm=llm,
    max_facts=50,
    priority=1,
)

long_term_memory_blocks = [
    static_memory_block,
    fact_extraction_memory_block,
]

memory = Memory.from_defaults(
    session_id="simple_agent",
    token_limit=10000,
    chat_history_token_ratio=0.7,
    token_flush_size=2000,
    memory_blocks=long_term_memory_blocks,
    insert_method=InsertMethod.SYSTEM
)

agent = FunctionAgent(
    llm=llm,
    tools=tools,
)

async def process(user_input: str) -> str:
    response = await agent.run(user_input, memory=memory)
    return response

if __name__ == "__main__":
    
    user_input = input("Enter your input: ")
    while user_input.lower() != "":
        response = asyncio.run(process(user_input))
        print(f"Response: {response}")
        user_input = input("Enter your input: ")
        
    print("Thank you for chatting with me!")