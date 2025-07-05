from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import argparse
import asyncio
from datetime import datetime
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import (
    Memory, InsertMethod
)
from llama_index.llms.openai import OpenAI

llm = OpenAI(model="gpt-4.1-mini")

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_current_weather(city: str):
    return f"The weather in {city} is sunny."

tools = [get_current_time, get_current_weather]

memory = Memory.from_defaults(
    session_id="simple_agent",
    token_limit=50,
    chat_history_token_ratio=0.7,
    token_flush_size=10,
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
    while user_input.strip() != "":
        response = asyncio.run(process(user_input))
        print(f"Response: {response}")
        user_input = input("Enter your input: ")
        
    print("Thank you for chatting with me!")
