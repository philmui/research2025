"""
Wikipedia Agent Module

Specialized agent for Wikipedia research and information retrieval.
Uses dependency injection for configuration (instructions from config file).

Design Principles:
- Single Responsibility: Handles only Wikipedia/knowledge queries
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
from asdrp.actions.search.wiki_tools import (
    search_wikipedia,
    get_page_summary,
    get_page_content,
    get_geosearch,
)

# Default instructions (used only when not provided via config)
DEFAULT_INSTRUCTIONS = """
You are a knowledgeable research assistant that can search and retrieve
information from Wikipedia.

You have access to the following capabilities:
- Search Wikipedia for pages matching a query
- Get concise summaries of Wikipedia articles
- Retrieve full page content including categories, links, and references
- Find Wikipedia articles about places near geographic coordinates

When asked about topics, use the appropriate tools to provide accurate
information from Wikipedia. Start with a search if you're unsure of the
exact page title, then retrieve summaries or full content as needed.

Tips:
- Use search_wikipedia first to find the correct page title
- Use get_page_summary for quick overviews (can limit by sentences)
- Use get_page_content for comprehensive information with references
- Use get_geosearch to find articles about nearby places
""".strip()

# Tools available to this agent
WIKI_TOOLS = [
    search_wikipedia,
    get_page_summary,
    get_page_content,
    get_geosearch,
]

# agent session state
session = SQLiteSession(session_id="1234")


def create_wiki_agent(
    model: str = "gpt-4.1-mini",
    temperature: Optional[float] = 0.0,
    instructions: Optional[str] = None
) -> Agent:
    """
    Create a Wikipedia Agent with the specified configuration.
    
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
        name="Wikipedia Agent",
        instructions=instructions or DEFAULT_INSTRUCTIONS,
        tools=WIKI_TOOLS,
        model=model,
        temperature=temperature,
    )


# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

async def main():
    agent = create_wiki_agent()
    print("Searching Wikipedia for information about Python programming ...")
    result = await Runner.run(agent, input="Tell me about Python programming language",
                              session=session)
    print(result.final_output)
    
    user_input = input("Ask Wikipedia Agent: ")
    while user_input.strip() != "":
        result = await Runner.run(agent, input=user_input, session=session)
        print(result.final_output)
        user_input = input("Ask Wikipedia Agent: ")
    
if __name__ == "__main__":
    asyncio.run(main())
