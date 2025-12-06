"""
Finance Agent Module

Specialized agent for financial data and stock market analysis.
Uses dependency injection for configuration (instructions from config file).

Design Principles:
- Single Responsibility: Handles only finance-related queries
- Open/Closed: Configurable via agents.yaml
- Dependency Inversion: Instructions injected from configuration
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Any, Dict, List, Optional
import asyncio

from agents import Agent, Runner, SQLiteSession
from agents.tracing import set_tracing_disabled
set_tracing_disabled(disabled=True)

from asdrp.agents.base import AgentBuilder
from asdrp.actions.finance.finance_tools import (
    get_ticker_info,
    get_historical_data,
    get_financials,
    get_recommendations,
    get_calendar,
    get_news,
    download_market_data,
)

# Default instructions (used only when not provided via config)
DEFAULT_INSTRUCTIONS = """
You are a financial analyst agent that can retrieve and analyze stock market data.

You have access to the following capabilities:
- Get comprehensive ticker information (company details, financials, key stats)
- Retrieve historical price data with customizable periods and intervals
- Access financial statements (income statement, balance sheet, cash flow)
- Get analyst recommendations
- View earnings calendar and upcoming events
- Fetch latest news articles for any ticker
- Download market data for multiple tickers at once

When asked about stocks, use the appropriate tools to provide accurate,
up-to-date information. Always specify the ticker symbol in uppercase (e.g., AAPL, TSLA, MSFT).
""".strip()

# Tools available to this agent
FINANCE_TOOLS = [
    get_ticker_info,
    get_historical_data,
    get_financials,
    get_recommendations,
    get_calendar,
    get_news,
    download_market_data,
]

# agent session state
session = SQLiteSession(session_id="1234")


def create_finance_agent(
    model: str = "gpt-4.1-mini",
    temperature: Optional[float] = 0.0,
    instructions: Optional[str] = None
) -> Agent:
    """
    Create a Finance Agent with the specified configuration.
    
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
        name="Finance Agent",
        instructions=instructions or DEFAULT_INSTRUCTIONS,
        tools=FINANCE_TOOLS,
        model=model,
        temperature=temperature,
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
