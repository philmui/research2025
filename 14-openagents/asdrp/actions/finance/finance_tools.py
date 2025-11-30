import asyncio
from typing import Any, List, Optional, Tuple

from agents import function_tool
import yfinance as yf
from datetime import datetime, timedelta
import json
import re

@function_tool
async def search_finance(query: str) -> str:
    """Search for financial information including stock prices, financial news, and other financial data.
    
    This function uses yfinance to get stock information, prices, news, and other financial data.
    It can handle queries about stock symbols, company names, or general financial queries.
    
    Args:
        query: A search query string (can be a stock symbol like "AAPL", company name, or financial question)
    
    Returns:
        Financial information including stock prices, news, and other relevant data
    """
    try:
        # Try to extract stock symbol from query (common ticker symbols are 1-5 uppercase letters)
        # Look for patterns like "AAPL", "MSFT", "GOOGL", etc.
        ticker_pattern = r'\b([A-Z]{1,5})\b'
        matches = re.findall(ticker_pattern, query.upper())
        
        # Common stock ticker symbols to check
        potential_tickers = matches if matches else []
        
        # If no ticker found, try to extract from common phrases
        if not potential_tickers:
            # Try to find stock symbols in common phrases
            query_upper = query.upper()
            # Check for common patterns like "stock price of AAPL" or "AAPL stock"
            ticker_match = re.search(r'(?:stock|price|ticker|symbol).*?([A-Z]{1,5})|([A-Z]{1,5}).*?(?:stock|price|ticker|symbol)', query_upper)
            if ticker_match:
                potential_tickers = [ticker_match.group(1) or ticker_match.group(2)]
        
        # If we found potential tickers, try to get stock information
        if potential_tickers:
            ticker_symbol = potential_tickers[0]
            try:
                stock = yf.Ticker(ticker_symbol)
                info = stock.info
                
                # Get current price data
                hist = stock.history(period="1d")
                current_price = hist['Close'].iloc[-1] if not hist.empty else None
                
                # Get recent news
                try:
                    news = stock.news[:5]
                except Exception:
                    news = []
                
                # Format the response
                result_parts = []
                result_parts.append(f"Stock Information for {ticker_symbol}:")
                result_parts.append(f"Company Name: {info.get('longName', 'N/A')}")
                
                if current_price is not None:
                    result_parts.append(f"Current Price: ${current_price:.2f}")
                
                # Add key financial metrics
                if 'marketCap' in info:
                    market_cap = info['marketCap']
                    if market_cap:
                        result_parts.append(f"Market Cap: ${market_cap:,.0f}")
                
                if 'previousClose' in info:
                    result_parts.append(f"Previous Close: ${info['previousClose']:.2f}")
                
                if '52WeekHigh' in info and '52WeekLow' in info:
                    result_parts.append(f"52 Week Range: ${info['52WeekLow']:.2f} - ${info['52WeekHigh']:.2f}")
                
                if 'dividendYield' in info and info['dividendYield']:
                    result_parts.append(f"Dividend Yield: {info['dividendYield'] * 100:.2f}%")
                
                # Add recent news
                if news:
                    result_parts.append("\nRecent News:")
                    for i, article in enumerate(news[:3], 1):
                        title = article.get('title', 'N/A')
                        publisher = article.get('publisher', 'N/A')
                        pub_date = article.get('providerPublishTime', '')
                        if pub_date:
                            pub_date = datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d")
                        result_parts.append(f"{i}. {title} ({publisher}, {pub_date})")
                
                return "\n".join(result_parts)
                
            except Exception as e:
                # If ticker lookup fails, try general search
                return f"Could not find stock information for '{ticker_symbol}'. Error: {str(e)}"
        
        # If no ticker found or ticker lookup failed, try to search for general financial information
        # For now, return a message suggesting to use a stock ticker
        return (
            f"Please provide a stock ticker symbol (e.g., AAPL, MSFT, GOOGL) to get financial information.\n"
            f"Query received: {query}\n"
            f"Example queries: 'What is the stock price of AAPL?', 'MSFT financial news', 'GOOGL stock information'"
        )
        
    except Exception as e:
        return f"Error searching financial information: {str(e)}"


# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

async def main():
    result = await search_finance.on_invoke_tool(
        ctx=None,
        input=json.dumps({"query": "TSLA"})
    )
    print(result)
    
if __name__ == "__main__":
    asyncio.run(main())