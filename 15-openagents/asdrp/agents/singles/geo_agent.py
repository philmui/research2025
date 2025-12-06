"""
Geo Agent Module

Specialized agent for geographic information and geocoding.
Uses dependency injection for configuration (instructions from config file).

Design Principles:
- Single Responsibility: Handles only geographic/location queries
- Open/Closed: Configurable via agents.yaml
- Dependency Inversion: Instructions injected from configuration
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Any, Dict, Optional
import asyncio

from agents import Agent, Runner, SQLiteSession
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)

from asdrp.agents.base import AgentBuilder
from asdrp.actions.geo.geo_tools import get_coordinates_by_address, get_address_by_coordinates

# Default instructions (used only when not provided via config)
DEFAULT_INSTRUCTIONS = """
You are a geographic information specialist that can convert addresses
to coordinates and coordinates to addresses using ArcGIS geocoding.

Capabilities:
- Get latitude/longitude coordinates for any address
- Get the address for any coordinates

Provide accurate location information when asked about places.
""".strip()

# Tools available to this agent
GEO_TOOLS = [
    get_coordinates_by_address,
    get_address_by_coordinates,
]

# agent session state
session = SQLiteSession(session_id="1234")


def create_geo_agent(
    model: str = "gpt-4.1-mini",
    temperature: Optional[float] = 0.0,
    instructions: Optional[str] = None
) -> Agent:
    """
    Create a Geo Agent with the specified configuration.
    
    Supports dependency injection - instructions can be provided from
    external configuration (agents.yaml) rather than being hardcoded.
    
    Args:
        model: The LLM model to use. Default: "gpt-4.1-mini".
        temperature: Temperature setting (0.0-2.0). None for reasoning models.
        instructions: System prompt. If None, uses DEFAULT_INSTRUCTIONS.
    
    Returns:
        Configured Agent instance
    """
    return AgentBuilder.create(
        name="Geo Agent",
        instructions=instructions or DEFAULT_INSTRUCTIONS,
        tools=GEO_TOOLS,
        model=model,
        temperature=temperature,
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
