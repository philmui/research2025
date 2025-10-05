from inspect import getframeinfo
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import asyncio
import os

# OpenAI Agents
from agents import (
    Agent, 
    Runner, 
    WebSearchTool, 
    set_tracing_disabled
)

set_tracing_disabled(disabled=True)

async def main():
    spanish_agent = Agent(
        name="Spanish Agent",
        instructions="You are a helpful assistant that can take questions in English and respond in Spanish.",
        model="gpt-5-mini",
        output_type=str,
    )
    german_agent = Agent(
        name="German Agent",
        instructions="You are a helpful assistant that can take questions in English and respond in German.",
        model="gpt-5-mini",
        output_type=str,
    )
    concierge_agent = Agent(
        name="My Agent",
        instructions="You are a helpful assistant that can answer questions and help with tasks.",
        model="gpt-5-mini",
        tools=[
            WebSearchTool(),
            spanish_agent.as_tool(
                tool_name="spanish_agent",
                tool_description="A helpful assistant that can take questions in English and respond in Spanish.",
            ),
            german_agent.as_tool(
                tool_name="german_agent",
                tool_description="A helpful assistant that can take questions in English and respond in German.",
            ),
        ],
        output_type=str,
    )

    user_input = input("Hello, how can I help you today? ")

    while user_input != "":
        response  = await Runner.run(concierge_agent, user_input)
        print(response.final_output)
        user_input = input("What else can I do for you? ")

# ---------------------------
# Main driver
# ---------------------------
if __name__ == "__main__":
    asyncio.run(main())