from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Any, Dict
import asyncio

from agents import Agent, Runner, SQLiteSession
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)

from asdrp.actions.finance.finance_tools import search_finance

# agent session state
session = SQLiteSession(session_id="1234")

def create_finance_agent():
    return Agent(
        name="Geo Agent",
        instructions=(
            "A agent that can get the coordinates of an address "
            "and the address of a set of coordinates"
        ),
        tools=[search_finance],
    )


# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

async def main():
    agent = create_finance_agent()
    print("Searching for financial information about TSLA ...")
    result = await Runner.run(agent, input="What is the stock price of TSLA?",
                              session=session)
    print(result.final_output)
    
    user_input = input("Ask Finance Agent: ")
    while user_input.strip() != "":
        result = await Runner.run(agent, input=user_input, session=session)
        print(result.final_output)
        user_input = input("Ask Finance Agent: ")
    
if __name__ == "__main__":
    asyncio.run(main())
