"""
Web Agent Module

Specialized agent for web search and real-time information retrieval.
Uses dependency injection for configuration (instructions from config file).

Design Principles:
- Single Responsibility: Handles only web search queries
- Open/Closed: Configurable via agents.yaml
- Dependency Inversion: Instructions injected from configuration
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Any, Dict, Optional
import asyncio

from agents import Agent, Runner, SQLiteSession, WebSearchTool
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)

from asdrp.agents.base import AgentBuilder

# Default instructions (used only when not provided via config)
DEFAULT_INSTRUCTIONS = """
You are a web search agent that can search the internet for current information.

You have access to web search capabilities to find:
- Current news and events
- Weather information
- Real-time data
- General web content

Use the web search tool to find up-to-date information that may not be
available in other specialized agents.
""".strip()

# Tools available to this agent
WEB_TOOLS = [
    WebSearchTool(),
]

# agent session state
session = SQLiteSession(session_id="1234")


def create_web_agent(
    model: str = "gpt-4.1-mini",
    temperature: Optional[float] = 0.0,
    instructions: Optional[str] = None
) -> Agent:
    """
    Create a Web Agent with the specified configuration.
    
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
        name="Web Agent",
        instructions=instructions or DEFAULT_INSTRUCTIONS,
        tools=WEB_TOOLS,
        model=model,
        temperature=temperature,
    )


# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

async def main():
    agent = create_web_agent()
    result = await Runner.run(agent, input="How is the weather in Tokyo?", session=session)
    print(result.final_output)
    
    user_input = input("Ask Web Agent: ")
    while user_input.strip() != "":
        result = await Runner.run(agent, input=user_input, session=session)
        print(result.final_output)
        user_input = input("Ask Web Agent: ")

if __name__ == "__main__":
    asyncio.run(main())
