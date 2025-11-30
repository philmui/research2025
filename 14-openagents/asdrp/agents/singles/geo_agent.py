from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Any, Dict
import asyncio

from agents import Agent, Runner, SQLiteSession
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)

from asdrp.actions.geo.geo_tools import get_coordinates_by_address, get_address_by_coordinates

# agent session state
session = SQLiteSession(session_id="1234")

def create_geo_agent():
    return Agent(
        name="Geo Agent",
        instructions=(
            "A agent that can get the coordinates of an address "
            "and the address of a set of coordinates"
        ),
        tools=[get_coordinates_by_address, get_address_by_coordinates],
    )


# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

async def main():
    agent = create_geo_agent()
    print("Finding coordinates of Coit Tower, San Francisco, CA ...")
    result = await Runner.run(agent, input="What are the coordinates of Coit Tower, San Francisco, CA?",
                              session=session)
    print(result.final_output)
    
    user_input = input("Ask Geo Agent: ")
    while user_input.strip() != "":
        result = await Runner.run(agent, input=user_input, session=session)
        print(result.final_output)
        user_input = input("Ask Geo Agent: ")
    
if __name__ == "__main__":
    asyncio.run(main())
