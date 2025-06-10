import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from datetime import datetime
import os
import time
import re
from typing import List
from pydantic import BaseModel, Field
from loguru import logger

import requests
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# Create server
mcp = FastMCP("BioMCP Server")
mcp.settings.port = os.environ.get("BIOMCP_PORT", 8131)

#--------------------------------
# Tools
#--------------------------------

@mcp.tool()
async def list_tools() -> list[str]:
    # Configure the BioMCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--with", "biomcp-python", "biomcp", "run"]
    )
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session
    ):
        await session.initialize()

        response_str = ""
        try:
            tool_result = await session.list_tools()
            response_str = f"Available tools: {[t.name for t in tool_result.tools]}"
        except Exception as e:
            logger.error(f"Error: {e}")
            response_str = f"list_tools: {e}"
        return response_str

@mcp.tool()
async def get_variant_details(variant_id: str) -> str:
    # Configure the BioMCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--with", "biomcp-python", "biomcp", "run"]
    )
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session
    ):
        # Initialize the session
        await session.initialize()

        response_str = ""
        try:
            result = await session.call_tool(
                "variant_details",
                {
                    "call_benefit": "Understand the variant details",
                    "variant_id": variant_id
                }
            )
            if not result.isError and result.content:
                # Access the text content from the first content block
                response_str = result.content[0].text
        except Exception as e:
            logger.error(f"Error: {e}")
            response_str = f"get_variant_details: {e}"
        return response_str

@mcp.tool()
async def get_article_details(pmid: str) -> str:
    # Configure the BioMCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--with", "biomcp-python", "biomcp", "run"]
    )
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session
    ):
        # Initialize the session
        await session.initialize()

        response_str = ""
        try:
            result = await session.call_tool(
                "article_details",
                {
                    "call_benefit": "SGet details of a PubMed article",
                    "pmid": pmid
                }
            )
            if not result.isError and result.content:
                response_str = result.content[0].text
        except Exception as e:
            logger.error(f"Error: {e}")
            response_str = f"get_article_details: {e}"
        return response_str

@mcp.tool()
async def get_articles(diseases:List[str] = [], keywords:List[str] = [], genes:List[str] = []) -> str:
    # Configure the BioMCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--with", "biomcp-python", "biomcp", "run"]
    )
    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session
    ):
        # Initialize the session
        await session.initialize()

        response_str = ""
        try:
            result = await session.call_tool(
                "article_searcher",
                {
                    "call_benefit": "Search PubMed articles using structured criteria",
                    "diseases": diseases,
                    "keywords": keywords,
                    "genes": genes,
                }
            )
            if not result.isError and result.content:
                response_str = result.content[0].text
        except Exception as e:
            logger.error(f"Error: {e}")
            response_str = f"get_articles: {e}"
        return response_str


class PubMedArticle(BaseModel):
    pmid: str = Field(description="The PubMed ID of the article")
    pmcid: str = Field(default="", description="The PubMed Central ID of the article")
    title: str = Field(default="", description="The title of the article")
    journal: str = Field(default="", description="The journal of the article")
    conference: str = Field(default="", description="The conference of the article")
    year: int = Field(default=0, description="The year of the article")
    authors: List[str] = Field(default=[], description="The authors of the article")
    abstract: str = Field(default="", description="The abstract of the article")
    url: str = Field(default="", description="The URL of the article")
    doi: str = Field(default="", description="The DOI of the article")

class PubMedArticleDetails(BaseModel):
    pmid: str = Field(description="The PubMed ID of the article")
    title: str = Field(default="", description="The title of the article")
    journal: str = Field(default="", description="The journal of the article")
    conference: str = Field(default="", description="The conference of the article")
    year: int = Field(default=0, description="The year of the article")
    authors: List[str] = Field(default=[], description="The authors of the article")
    abstract: str = Field(default="", description="The abstract of the article")
    full_text: str = Field(default="", description="The full text of the article")
    pubmed_url: str = Field(default="", description="The URL of the article on PubMed")
    pmc_url: str = Field(default="", description="The URL of the article on PubMed Central")


async def parse_articles(text: str) -> List[PubMedArticle]:
    """Given a markdown output with `Pmid` PubMed IDs, return a list of PubMedArticle objects.

    Args:
        text (str): Markdown output with `Pmid` PubMed IDs

    Returns:
        List[PubMedArticle]: List of parsed PubMed articles
    """
    articles = []
    
    # Split text into individual records using "# Record" as delimiter
    record_pattern = r'# Record \d+\s*\n'
    records = re.split(record_pattern, text)
    
    for record in records:
        if not record.strip():
            continue
            
        # Skip if no Pmid found
        if 'Pmid:' not in record:
            continue
            
        try:
            # Extract PMID
            pmid_match = re.search(r'Pmid:\s*(\d+)', record)
            pmid = pmid_match.group(1) if pmid_match else ""
            
            # Extract Pmcid (often empty)
            pmcid_match = re.search(r'Pmcid:\s*(\w+)', record)
            pmcid = pmcid_match.group(1) if pmcid_match else ""

            # Extract Title (can be multi-line)
            title_match = re.search(r'Title:\s*\n?(.*?)(?=\n(?:Journal|Conference):)', record, re.DOTALL)
            title = title_match.group(1).strip().replace('\n', ' ') if title_match else ""
            
            # Extract Journal or Conference (separate fields)
            journal_match = re.search(r'Journal:\s*(.*?)(?=\n)', record)
            conference_match = re.search(r'Conference:\s*(.*?)(?=\n)', record)
            journal = journal_match.group(1).strip() if journal_match else ""
            conference = conference_match.group(1).strip() if conference_match else ""
            
            # Extract Date and parse year
            date_match = re.search(r'Date:\s*(.*?)(?=\n)', record)
            year = 0
            if date_match:
                date_str = date_match.group(1).strip()
                year_match = re.search(r'(\d{4})', date_str)
                if year_match:
                    year = int(year_match.group(1))
            
            # Extract DOI
            doi_match = re.search(r'Doi:\s*(.*?)(?=\n)', record)
            doi = doi_match.group(1).strip() if doi_match else ""
            
            # Extract Abstract (can be multi-line)
            abstract_match = re.search(r'Abstract:\s*\n?(.*?)(?=\nPubmed Url:|$)', record, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else ""
            
            # Extract PubMed URL
            url_match = re.search(r'Pubmed Url:\s*(.*?)(?=\n)', record)
            url = url_match.group(1).strip() if url_match else ""
            
            # Extract Authors
            authors_match = re.search(r'Authors:\s*(.*?)(?=\n|$)', record)
            authors = []
            if authors_match:
                authors_str = authors_match.group(1).strip()
                # Split by comma and clean up
                authors = [author.strip() for author in authors_str.split(',') if author.strip() and author.strip() != '...']
            
            # Create PubMedArticle object
            article = PubMedArticle(
                pmid=pmid,
                pmcid=pmcid,
                title=title,
                journal=journal,
                conference=conference,
                year=year,
                authors=authors,
                abstract=abstract,
                url=url,
                doi=doi
            )
            articles.append(article)
            
        except Exception as e:
            logger.error(f"Error parsing article record: {e}")
            continue
    
    return articles


async def parse_article_details(text: str) -> PubMedArticleDetails:
    """Parse article details text into a PubMedArticleDetails Pydantic object.
    
    This function robustly parses detailed article information from text format,
    handling multi-line fields, missing fields, and various formatting edge cases.
    
    Args:
        text (str): Raw text containing article details with fields like Pmid, Title, etc.
        
    Returns:
        PubMedArticleDetails: Parsed article details object
        
    Raises:
        ValueError: If required PMID field is missing or invalid
        Exception: For other parsing errors with detailed error message
        
    Example:
        >>> text = "Pmid: 12345\\nTitle: Sample Title\\n..."
        >>> article = await parse_article_details(text)
        >>> print(article.pmid)  # "12345"
    """
    try:
        # Initialize default values
        article_data = {
            "pmid": "",
            "title": "",
            "journal": "",
            "conference": "",
            "year": 0,
            "authors": [],
            "abstract": "",
            "full_text": "",
            "pubmed_url": "",
            "pmc_url": ""
        }
        
        # Clean and normalize the input text
        text = text.strip()
        if not text:
            raise ValueError("Input text is empty")
        
        # Extract PMID (required field)
        pmid_match = re.search(r'Pmid:\s*(\d+)', text, re.IGNORECASE)
        if not pmid_match:
            raise ValueError("Required PMID field not found in text")
        article_data["pmid"] = pmid_match.group(1)
        
        # Extract Title (can be multi-line)
        title_match = re.search(
            r'Title:\s*\n?(.*?)(?=\n(?:Abstract|Journal|Conference|Date|Pmid|Authors|Full Text|$))', 
            text, 
            re.DOTALL | re.IGNORECASE
        )
        if title_match:
            # Clean up title: strip whitespace, normalize line breaks
            title = title_match.group(1).strip()
            title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
            article_data["title"] = title
        
        # Extract Journal or Conference (separate fields)
        journal_match = re.search(r'Journal:\s*(.*?)(?=\n)', text, re.IGNORECASE)
        if journal_match:
            article_data["journal"] = journal_match.group(1).strip()
        else:
            conference_match = re.search(r'Conference:\s*(.*?)(?=\n)', text, re.IGNORECASE)
            if conference_match:
                article_data["conference"] = conference_match.group(1).strip()
        
        # Extract Date and parse year
        date_match = re.search(r'Date:\s*(.*?)(?=\n)', text, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1).strip()
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                try:
                    article_data["year"] = int(year_match.group(1))
                except ValueError:
                    logger.warning(f"Invalid year format in date: {date_str}")
        
        # Extract Abstract (can be multi-line)
        abstract_match = re.search(
            r'Abstract:\s*\n?(.*?)(?=\n(?:Full Text|Pubmed Url|Pmc Url|Authors|$))', 
            text, 
            re.DOTALL | re.IGNORECASE
        )
        if abstract_match:
            abstract = abstract_match.group(1).strip()
            # Clean up abstract formatting
            abstract = re.sub(r'\n\s*\n', '\n\n', abstract)  # Normalize paragraph breaks
            article_data["abstract"] = abstract
        
        # Extract Full Text (can be very long and multi-line)
        full_text_match = re.search(
            r'Full Text:\s*\n?(.*?)(?=\n(?:Pubmed Url|Pmc Url|Authors|$))', 
            text, 
            re.DOTALL | re.IGNORECASE
        )
        if full_text_match:
            full_text = full_text_match.group(1).strip()
            # Basic cleanup while preserving structure
            full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)  # Normalize paragraph breaks
            article_data["full_text"] = full_text
        
        # Extract PubMed URL
        pubmed_url_match = re.search(r'Pubmed Url:\s*(https?://[^\s\n]+)', text, re.IGNORECASE)
        if pubmed_url_match:
            article_data["pubmed_url"] = pubmed_url_match.group(1).strip()
        
        # Extract PMC URL
        pmc_url_match = re.search(r'Pmc Url:\s*(https?://[^\s\n]+)', text, re.IGNORECASE)
        if pmc_url_match:
            article_data["pmc_url"] = pmc_url_match.group(1).strip()
        
        # Extract Authors
        authors_match = re.search(r'Authors:\s*(.*?)(?=\n|$)', text, re.IGNORECASE)
        if authors_match:
            authors_str = authors_match.group(1).strip()
            if authors_str:
                # Split by comma and clean up each author
                authors = []
                for author in authors_str.split(','):
                    author = author.strip()
                    # Skip empty strings and ellipsis
                    if author and author != '...' and author != '...':
                        authors.append(author)
                article_data["authors"] = authors
        
        # Create and validate the Pydantic object
        article = PubMedArticleDetails(**article_data)
        return article
        
    except ValueError as ve:
        logger.error(f"Validation error in parse_article_details: {ve}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in parse_article_details: {e}")
        raise Exception(f"Failed to parse article details: {str(e)}") from e
    
#--------------------------------
# Streamable HTTPMCP Server
#--------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http")


#--------------------------------
# Testing code
#--------------------------------
    

def print_response(tag: str, response_str: str, start_time: float, end_time: float, max_length: int = 250):
    print(f"[[\033[1;93m{tag}\033[0m]]: {end_time - start_time:.2f}s\n{response_str[:max_length]} ...\n")

def test_tools():
    start_time = time.time()
    response_str = asyncio.run(list_tools())
    end_time = time.time()
    print_response("list_tools", response_str, start_time, end_time)

    start_time = time.time()
    response_str = asyncio.run(get_variant_details(variant_id="rs113488022"))
    end_time = time.time()
    print_response("get_variant_details", response_str, start_time, end_time)
    
    start_time = time.time()
    response_str = asyncio.run(get_articles(
        diseases=["Alzheimer's disease"])
    )
    end_time = time.time()
    print_response("get_articles:diseases", response_str, start_time, end_time, -1)
    
    start_time = time.time()
    response_str = asyncio.run(get_articles(
        keywords=["measles", "texas"])
    )
    end_time = time.time()
    print_response("get_articles:keywords", response_str, start_time, end_time, -1)
    
    # Test the parsing function
    start_time = time.time()
    parsed_articles = asyncio.run(parse_articles(response_str))
    end_time = time.time()
    
    print(f"[[\033[1;93mparse_article\033[0m]]: {end_time - start_time:.2f}s")
    print(f"Parsed {len(parsed_articles)} articles:")
    for i, article in enumerate(parsed_articles[-3:], 1):  # Show first 3 articles
        print(f"\n  {i}. PMID: {article.pmid}")
        print(f"     PMCID: {article.pmcid}")
        print(f"     Title: {article.title[:100]}{'...' if len(article.title) > 100 else ''}")
        if article.journal:
            print(f"     Journal: {article.journal}")
        if article.conference:
            print(f"     Conference: {article.conference}")
        print(f"     Year: {article.year}")
        print(f"     Authors: {', '.join(article.authors[:3])}{'...' if len(article.authors) > 3 else ''}")
        print(f"     DOI: {article.doi}")
    
    if len(parsed_articles) > 3:
        print(f"     ... and {len(parsed_articles) - 3} more articles")
    print()
    
    start_time = time.time()
    response_str = asyncio.run(get_article_details(
        pmid="37351900")
    )
    end_time = time.time()
    print_response("get_article_details", response_str[:100], start_time, end_time, -1)
    
    # Test the article details parsing function
    start_time = time.time()
    try:
        parsed_article_details = asyncio.run(parse_article_details(response_str))
        end_time = time.time()
        
        print(f"[[\033[1;93mparse_article_details\033[0m]]: {end_time - start_time:.2f}s")
        print("Parsed article details:")
        print(f"  PMID: {parsed_article_details.pmid}")
        print(f"  Title: {parsed_article_details.title[:100]}{'...' if len(parsed_article_details.title) > 100 else ''}")
        if parsed_article_details.journal:
            print(f"  Journal: {parsed_article_details.journal}")
        if parsed_article_details.conference:
            print(f"  Conference: {parsed_article_details.conference}")
        print(f"  Year: {parsed_article_details.year}")
        print(f"  Authors: {', '.join(parsed_article_details.authors[:3])}{'...' if len(parsed_article_details.authors) > 3 else ''}")
        print(f"  PubMed URL: {parsed_article_details.pubmed_url}")
        print(f"  PMC URL: {parsed_article_details.pmc_url}")
        print(f"  Abstract length: {len(parsed_article_details.abstract)} chars")
        print(f"  Full text length: {len(parsed_article_details.full_text)} chars")
        print()
    except Exception as e:
        end_time = time.time()
        print(f"[[\033[1;93mparse_article_details\033[0m]]: {end_time - start_time:.2f}s - ERROR: {e}")
        print()
