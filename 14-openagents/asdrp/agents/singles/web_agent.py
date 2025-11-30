import asyncio

from agents import Runner, SQLiteSession
from agents.tracing import set_tracing_disabled
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
set_tracing_disabled(disabled=True)

from agents import Agent, WebSearchTool

# agent session state
session = SQLiteSession(session_id="1234")

def create_web_agent():
    return Agent(
        name="Web Agent",
        instructions="A agent that can search the web for information",
        tools=[WebSearchTool()],
    )

# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

async def main():
    agent = create_web_agent()
    result = await Runner.run(agent, input="What is the weather in Tokyo?", session=session)
    print(result.final_output)
    
    user_input = input("Ask Web Agent: ")
    while user_input.strip() != "":
        result = await Runner.run(agent, input=user_input, session=session)
        print(result.final_output)
        user_input = input("Ask Web Agent: ")

if __name__ == "__main__":
    asyncio.run(main())