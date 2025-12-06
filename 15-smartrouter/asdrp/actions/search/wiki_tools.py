import asyncio
from typing import Any, Dict, List, Optional

from agents import function_tool
import json
import wikipedia

# Configure Wikipedia settings
wikipedia.set_lang("en")


@function_tool
async def search_wikipedia(
    query: str,
    results: int = 10,
    suggestion: bool = True
) -> Dict[str, Any]:
    """
    Search Wikipedia for pages matching a query.
    
    Searches Wikipedia and returns a list of page titles that match the query.
    Optionally includes a suggested correction if the query has a typo.
    
    Args:
        query (str): The search query string.
        results (int): Maximum number of results to return. Default: 10. Max: 500.
        suggestion (bool): Whether to include a suggested correction. Default: True.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'query': The original search query
            - 'results': List of matching page titles
            - 'suggestion': Suggested correction (if suggestion=True and one exists)
    
    Raises:
        ValueError: If query is empty or None.
        Exception: If the Wikipedia API call fails.
    
    Example:
        >>> await search_wikipedia("Python programming")
        {'query': 'Python programming', 'results': ['Python (programming language)', ...], 'suggestion': None}
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        
        if suggestion:
            # search returns (results_list, suggestion) when suggestion=True
            search_result = await loop.run_in_executor(
                None,
                lambda: wikipedia.search(query.strip(), results=results, suggestion=True)
            )
            titles, suggested = search_result
        else:
            titles = await loop.run_in_executor(
                None,
                lambda: wikipedia.search(query.strip(), results=results, suggestion=False)
            )
            suggested = None
        
        return {
            'query': query.strip(),
            'results': titles,
            'suggestion': suggested
        }
    except Exception as e:
        raise Exception(f"Failed to search Wikipedia for '{query}': {e}")


@function_tool
async def get_page_summary(
    title: str,
    sentences: int = 0,
    chars: int = 0,
    auto_suggest: bool = True
) -> Dict[str, Any]:
    """
    Get a summary of a Wikipedia page.
    
    Retrieves the summary (introductory text) of a Wikipedia page. Can limit
    the summary by number of sentences or characters.
    
    Args:
        title (str): The title of the Wikipedia page.
        sentences (int): Number of sentences to return. 0 = all sentences. Default: 0.
        chars (int): Maximum number of characters. 0 = no limit. Default: 0.
        auto_suggest (bool): Auto-suggest a valid page title if not found. Default: True.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'title': The page title (may differ from input if auto-suggested)
            - 'summary': The summary text
    
    Raises:
        ValueError: If title is empty or None.
        wikipedia.exceptions.PageError: If the page doesn't exist.
        wikipedia.exceptions.DisambiguationError: If the title is ambiguous.
        Exception: If the Wikipedia API call fails.
    
    Example:
        >>> await get_page_summary("Albert Einstein", sentences=3)
        {'title': 'Albert Einstein', 'summary': 'Albert Einstein was a German-born...'}
    """
    if not title or not title.strip():
        raise ValueError("Title cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        
        summary = await loop.run_in_executor(
            None,
            lambda: wikipedia.summary(
                title.strip(),
                sentences=sentences if sentences > 0 else 0,
                chars=chars if chars > 0 else 0,
                auto_suggest=auto_suggest
            )
        )
        
        return {
            'title': title.strip(),
            'summary': summary
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Return the disambiguation options
        return {
            'title': title.strip(),
            'summary': None,
            'disambiguation': True,
            'options': e.options[:20]  # Limit to first 20 options
        }
    except wikipedia.exceptions.PageError as e:
        return {
            'title': title.strip(),
            'summary': None,
            'error': f"Page not found: {e}"
        }
    except Exception as e:
        raise Exception(f"Failed to get summary for '{title}': {e}")


@function_tool
async def get_page_content(
    title: str,
    auto_suggest: bool = True
) -> Dict[str, Any]:
    """
    Get the full content of a Wikipedia page.
    
    Retrieves comprehensive information about a Wikipedia page including
    the full content, URL, categories, links, and references.
    
    Args:
        title (str): The title of the Wikipedia page.
        auto_suggest (bool): Auto-suggest a valid page title if not found. Default: True.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'title': The canonical page title
            - 'page_id': The Wikipedia page ID
            - 'url': The page URL
            - 'summary': The page summary/introduction
            - 'content': The full page content (plain text)
            - 'categories': List of page categories
            - 'links': List of linked Wikipedia page titles
            - 'references': List of external reference URLs
            - 'images': List of image URLs on the page
    
    Raises:
        ValueError: If title is empty or None.
        wikipedia.exceptions.PageError: If the page doesn't exist.
        wikipedia.exceptions.DisambiguationError: If the title is ambiguous.
        Exception: If the Wikipedia API call fails.
    """
    if not title or not title.strip():
        raise ValueError("Title cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        
        page = await loop.run_in_executor(
            None,
            lambda: wikipedia.page(title.strip(), auto_suggest=auto_suggest)
        )
        
        return {
            'title': page.title,
            'page_id': page.pageid,
            'url': page.url,
            'summary': page.summary,
            'content': page.content,
            'categories': page.categories,
            'links': page.links[:100],  # Limit to first 100 links
            'references': page.references[:50],  # Limit to first 50 references
            'images': page.images[:20]  # Limit to first 20 images
        }
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            'title': title.strip(),
            'error': 'disambiguation',
            'message': f"'{title}' may refer to multiple pages",
            'options': e.options[:20]
        }
    except wikipedia.exceptions.PageError as e:
        return {
            'title': title.strip(),
            'error': 'not_found',
            'message': str(e)
        }
    except Exception as e:
        raise Exception(f"Failed to get page content for '{title}': {e}")


@function_tool
async def get_geosearch(
    latitude: float,
    longitude: float,
    title: Optional[str] = None,
    results: int = 10,
    radius: int = 1000
) -> Dict[str, Any]:
    """
    Search for Wikipedia pages near a geographic location.
    
    Finds Wikipedia articles about places near the specified coordinates
    or near the location of a specified Wikipedia article.
    
    Args:
        latitude (float): Latitude coordinate.
        longitude (float): Longitude coordinate.
        title (Optional[str]): Search near the coordinates of this page instead.
        results (int): Maximum number of results. Default: 10. Max: 500.
        radius (int): Search radius in meters. Default: 1000. Max: 10000.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'latitude': The search latitude
            - 'longitude': The search longitude
            - 'radius': The search radius in meters
            - 'results': List of nearby page titles
    
    Raises:
        ValueError: If coordinates are invalid or radius is out of range.
        Exception: If the Wikipedia API call fails.
    """
    if radius < 10 or radius > 10000:
        raise ValueError("Radius must be between 10 and 10000 meters.")
    
    try:
        loop = asyncio.get_running_loop()
        
        if title:
            pages = await loop.run_in_executor(
                None,
                lambda: wikipedia.geosearch(
                    title=title.strip(),
                    results=results,
                    radius=radius
                )
            )
        else:
            pages = await loop.run_in_executor(
                None,
                lambda: wikipedia.geosearch(
                    latitude=latitude,
                    longitude=longitude,
                    results=results,
                    radius=radius
                )
            )
        
        return {
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius,
            'results': pages
        }
    except Exception as e:
        raise Exception(f"Failed to perform geosearch: {e}")


# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

def _parse_result(result) -> Any:
    """Parse result - handles both dict and JSON string returns."""
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"_error": result}
    return result


async def main():
    """Smoke tests for all Wikipedia tools."""
    
    # Test 1: search_wikipedia
    print("=" * 60)
    print("Test 1: search_wikipedia")
    print("=" * 60)
    result = await search_wikipedia.on_invoke_tool(
        ctx=None,
        input=json.dumps({"query": "Python programming language", "results": 5})
    )
    parsed = _parse_result(result)
    print(f"Query: {parsed.get('query')}")
    print(f"Results: {parsed.get('results')}")
    print(f"Suggestion: {parsed.get('suggestion')}")
    print()
    
    # Test 2: get_page_summary
    print("=" * 60)
    print("Test 2: get_page_summary")
    print("=" * 60)
    result = await get_page_summary.on_invoke_tool(
        ctx=None,
        input=json.dumps({"title": "Python (programming language)", "sentences": 3})
    )
    parsed = _parse_result(result)
    print(f"Title: {parsed.get('title')}")
    summary = parsed.get('summary', '')
    print(f"Summary: {summary[:200]}..." if summary and len(summary) > 200 else f"Summary: {summary}")
    print()
    
    # Test 3: get_page_content
    print("=" * 60)
    print("Test 3: get_page_content")
    print("=" * 60)
    result = await get_page_content.on_invoke_tool(
        ctx=None,
        input=json.dumps({"title": "Albert Einstein"})
    )
    parsed = _parse_result(result)
    print(f"Title: {parsed.get('title')}")
    print(f"Page ID: {parsed.get('page_id')}")
    print(f"URL: {parsed.get('url')}")
    print(f"Categories count: {len(parsed.get('categories', []))}")
    print(f"Links count: {len(parsed.get('links', []))}")
    print(f"References count: {len(parsed.get('references', []))}")
    print()
    
    # Test 4: get_geosearch
    print("=" * 60)
    print("Test 4: get_geosearch")
    print("=" * 60)
    result = await get_geosearch.on_invoke_tool(
        ctx=None,
        input=json.dumps({"latitude": 37.7749, "longitude": -122.4194, "radius": 5000})
    )
    parsed = _parse_result(result)
    print(f"Latitude: {parsed.get('latitude')}")
    print(f"Longitude: {parsed.get('longitude')}")
    print(f"Radius: {parsed.get('radius')}m")
    print(f"Nearby places: {parsed.get('results')}")
    print()

    print("=" * 60)
    print("All 4 smoke tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

