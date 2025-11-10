##########################################################################################
# arxiv_agent.py
# --------------
# This module provides an AgentFactory that creates ArXiv search agents using LangChain v1.0.
# The factory returns a configured agent that can search ArXiv for any query string.
##########################################################################################

from langchain.agents import create_agent
from dotenv import load_dotenv, find_dotenv
import arxiv

_ = load_dotenv(find_dotenv())


def search_arxiv(query: str) -> str:
    """Search ArXiv for the given query string and return information about the most relevant papers.
    
    Args:
        query: A search query string (can be a phrase or question, not just a single term)
    
    Returns:
        Information about the most relevant ArXiv papers found for the query
    """
    try:
        # Create a client for ArXiv API
        client = arxiv.Client()
        
        # Search ArXiv for papers matching the query
        search = arxiv.Search(
            query=query,
            max_results=3,  # Get top 3 results
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        # Use Client.results() instead of deprecated Search.results()
        results = list(client.results(search))
        
        if not results:
            return f"No ArXiv papers found for the query: {query}"
        
        # Format the results
        formatted_results = []
        for i, paper in enumerate(results, 1):
            # Extract key information
            title = paper.title
            authors = ", ".join([author.name for author in paper.authors])
            published = paper.published.strftime("%Y-%m-%d") if paper.published else "Unknown"
            summary = paper.summary[:500] if len(paper.summary) > 500 else paper.summary
            arxiv_id = paper.entry_id.split('/')[-1] if paper.entry_id else "Unknown"
            arxiv_url = paper.entry_id if paper.entry_id else "Unknown"
            
            formatted_result = (
                f"Paper {i}:\n"
                f"Title: {title}\n"
                f"Authors: {authors}\n"
                f"Published: {published}\n"
                f"ArXiv ID: {arxiv_id}\n"
                f"URL: {arxiv_url}\n"
                f"Summary: {summary}\n"
            )
            formatted_results.append(formatted_result)
        
        return "\n\n".join(formatted_results)
        
    except arxiv.ArxivError as e:
        return f"ArXiv API error: {str(e)}"
    
    except Exception as e:
        return f"Error searching ArXiv: {str(e)}"


def create_arxiv_agent(
    model: str = "openai:gpt-5-mini",
    system_prompt: str = "You are a helpful assistant that can search ArXiv for academic papers and research articles.",
) -> object:
    """AgentFactory that creates and returns an ArXiv search agent.
    
    Args:
        model: The language model identifier to use for the agent. Defaults to "openai:gpt-5-mini".
        system_prompt: The system prompt for the agent. Defaults to an ArXiv-focused prompt.
    
    Returns:
        A configured LangChain agent that can search ArXiv.
    """
    return create_agent(
        model=model,
        tools=[search_arxiv],
        system_prompt=system_prompt,
    )
    
#----------------------------------------------
# Simple smoke test
#----------------------------------------------

if __name__ == "__main__":
    agent = create_arxiv_agent()
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "What are the latest papers on multi-agent orchestration?"}]}
    )
    print(response["messages"][-1].content)