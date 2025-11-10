##########################################################################################
# search_agent.py
# ----------------
# This module provides an AgentFactory that creates web search agents using LangChain v1.0.
# The factory returns a configured agent that can search the web using OpenAI's web search.
##########################################################################################

from langchain.agents import create_agent
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())


def search_web(query: str) -> str:
    """Search the web using OpenAI's web search capabilities.
    
    This function uses OpenAI's Responses API with web search tool enabled.
    The web search is built into OpenAI models that support it (e.g., gpt-5, gpt-4o).
    
    Args:
        query: A search query string (can be a phrase or question).
    
    Returns:
        Search results from the web.
    """
    try:
        client = OpenAI()
        
        # Use OpenAI's Responses API with web search tool
        # The Responses API handles the web search automatically
        response = client.responses.create(
            model="gpt-5-mini",
            input=query,
            tools=[{"type": "web_search"}],
        )
        
        # The Responses API returns output_text directly
        # Or we can access the output array for more detailed information
        if hasattr(response, 'output_text') and response.output_text:
            return response.output_text
        
        # If output_text is not available, extract from output array
        if hasattr(response, 'output') and response.output:
            # Find the message output item
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    if hasattr(item, 'content') and item.content:
                        # Extract text from content array
                        for content_item in item.content:
                            if hasattr(content_item, 'type') and content_item.type == 'output_text':
                                if hasattr(content_item, 'text'):
                                    return content_item.text
                            elif hasattr(content_item, 'text'):
                                return content_item.text
                elif hasattr(item, 'text'):
                    return item.text
        
        # Fallback: return string representation
        return str(response) if response else "No results found"
        
    except Exception as e:
        return f"Error performing web search: {str(e)}"


def create_websearch_agent(
    model: str = "openai:gpt-5",
    system_prompt: str = "You are a helpful assistant that can search the web for information.",
) -> object:
    """AgentFactory that creates and returns a web search agent using OpenAI's web search.
    
    This implementation uses a function tool that calls OpenAI's Responses API
    with web search enabled. The Responses API handles web search automatically.
    
    Args:
        model: The language model identifier to use for the agent. Defaults to "openai:gpt-5".
            Note: Web search requires models that support it (e.g., gpt-5, gpt-4o).
        system_prompt: The system prompt for the agent. Defaults to a websearch-focused prompt.
    
    Returns:
        A configured LangChain agent that can search the web using OpenAI's web search.
    """
    return create_agent(
        model=model,
        tools=[search_web],
        system_prompt=system_prompt,
    )
    
#----------------------------------------------
# Simple smoke test
#----------------------------------------------

if __name__ == "__main__":
    agent = create_websearch_agent()
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "What is the latest news about tariffs?"}]}
    )
    print(response["messages"][-1].content)