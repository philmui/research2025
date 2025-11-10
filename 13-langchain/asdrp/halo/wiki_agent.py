##########################################################################################
# wiki_agent.py
# -------------
# This module provides an AgentFactory that creates Wikipedia search agents using LangChain v1.0.
# The factory returns a configured agent that can search Wikipedia for any query string.
##########################################################################################

from langchain.agents import create_agent
from dotenv import load_dotenv, find_dotenv
import wikipedia

_ = load_dotenv(find_dotenv())


def search_wikipedia(query: str) -> str:
    """Search Wikipedia for the given query string and return a summary of the most relevant article.
    
    Args:
        query: A search query string (can be a phrase or question, not just a single term)
    
    Returns:
        A summary of the Wikipedia article found for the query
    """
    try:
        # Search for pages matching the query
        search_results = wikipedia.search(query, results=1)
        
        if not search_results:
            return f"No Wikipedia articles found for the query: {query}"
        
        # Get the most relevant page
        page_title = search_results[0]
        page = wikipedia.page(page_title, auto_suggest=False)
        
        # Return the summary (first 500 characters to keep it concise)
        summary = page.summary[:500] if len(page.summary) > 500 else page.summary
        return f"Wikipedia article '{page_title}': {summary}"
    
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


def create_wikipedia_agent(
    model: str = "openai:gpt-5-mini",
    system_prompt: str = "You are a helpful assistant that can search Wikipedia for information.",
) -> object:
    """AgentFactory that creates and returns a Wikipedia search agent.
    
    Args:
        model: The language model identifier to use for the agent. Defaults to "openai:gpt-5-mini".
        system_prompt: The system prompt for the agent. Defaults to a Wikipedia-focused prompt.
    
    Returns:
        A configured LangChain agent that can search Wikipedia.
    """
    return create_agent(
        model=model,
        tools=[search_wikipedia],
        system_prompt=system_prompt,
    )
    
#----------------------------------------------
# Simple smoke test
#----------------------------------------------

if __name__ == "__main__":
    agent = create_wikipedia_agent()
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "What is San Francisco?"}]}
    )
    print(response["messages"][-1].content)