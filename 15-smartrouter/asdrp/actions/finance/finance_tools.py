import asyncio
from typing import Any, Dict, List, Optional, Union

from agents import function_tool
from datetime import datetime, timedelta
from functools import partial
import json
import pandas as pd
from pandas import DataFrame, notna
import yfinance as yf

from asdrp.util.dict_utils import DictUtils

@function_tool
async def get_ticker_info(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a ticker symbol.
    
    Retrieves company information including business summary, financial metrics,
    key statistics, and other relevant data from Yahoo Finance.
    
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL').
            Can be a single symbol or multiple symbols separated by spaces.
        
    Returns:
        Dict[str, Any]: Dictionary containing ticker information including:
            - Company name, sector, industry
            - Market cap, enterprise value
            - Financial metrics (P/E ratio, EPS, revenue, etc.)
            - Key statistics
            - Business summary
            - And many more fields
        
    Raises:
        ValueError: If symbol is empty or None.
        Exception: If the yfinance API call fails.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        info = await loop.run_in_executor(None, lambda: ticker.info)
        return info if info else {}
    except Exception as e:
        raise Exception(f"Failed to get ticker info for '{symbol}': {e}")

@function_tool
async def get_historical_data(
    symbol: str,
    period: Optional[str] = "1mo",
    interval: Optional[str] = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    prepost: bool = False,
    auto_adjust: bool = True,
    actions: bool = True,
    repair: bool = False
) -> Dict[str, Any]:
    """
    Get historical market data for a ticker symbol.
    
    Retrieves historical price data including open, high, low, close, volume,
    and optionally dividends and splits.
    
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL').
        period (Optional[str]): Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max.
            Default: "1mo"
        interval (Optional[str]): Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo.
            Default: "1d"
        start (Optional[str]): Download start date string (YYYY-MM-DD) or datetime.
            If specified, period is ignored.
        end (Optional[str]): Download end date string (YYYY-MM-DD) or datetime.
            If specified, period is ignored.
        prepost (bool): Include pre and post market data. Default: False
        auto_adjust (bool): Adjust all OHLC automatically. Default: True
        actions (bool): Download dividends and stock splits data. Default: True
        repair (bool): Repair obvious price errors. Default: False
    
    Returns:
        Dict[str, Any]: Dictionary containing historical data with keys:
            - 'data': DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
            - 'symbol': The ticker symbol
            - 'period': The period used
            - 'interval': The interval used
    
    Raises:
        ValueError: If symbol is empty or invalid parameters provided.
        Exception: If the yfinance API call fails.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")
    
    # Validate period if provided
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    if period and period not in valid_periods:
        raise ValueError(f"Period must be one of {valid_periods}, got '{period}'.")
    
    # Validate interval if provided
    valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    if interval and interval not in valid_intervals:
        raise ValueError(f"Interval must be one of {valid_intervals}, got '{interval}'.")
    
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        
        # Build parameters for history call
        history_params = DictUtils.build_params(
            period=period,
            interval=interval,
            start=start,
            end=end,
            prepost=prepost,
            auto_adjust=auto_adjust,
            actions=actions,
            repair=repair
        )
        
        # Get historical data
        history_func = partial(ticker.history, **history_params)
        hist_data = await loop.run_in_executor(None, history_func)
        
        # Convert DataFrame to dict for JSON serialization
        if hist_data is not None and not hist_data.empty:
            # Convert DataFrame to dict with proper formatting
            data_dict = hist_data.to_dict(orient='index')
            # Convert index (dates) to strings
            result = {
                'data': {str(idx): {k: (float(v) if pd.notna(v) else None) for k, v in row.items()} 
                        for idx, row in data_dict.items()},
                'symbol': symbol.strip(),
                'period': period,
                'interval': interval,
                'start': start,
                'end': end
            }
        else:
            result = {
                'data': {},
                'symbol': symbol.strip(),
                'period': period,
                'interval': interval,
                'start': start,
                'end': end
            }
        
        return result
    except Exception as e:
        raise Exception(f"Failed to get historical data for '{symbol}': {e}")

@function_tool
async def get_financials(symbol: str) -> Dict[str, Any]:
    """
    Get financial statements (income statement, balance sheet, cash flow) for a ticker.
    
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL').
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'income_stmt': Income statement data
            - 'balance_sheet': Balance sheet data
            - 'cashflow': Cash flow statement data
    
    Raises:
        ValueError: If symbol is empty or None.
        Exception: If the yfinance API call fails.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        
        # Get all financial statements
        financials = await loop.run_in_executor(None, lambda: ticker.financials)
        balance_sheet = await loop.run_in_executor(None, lambda: ticker.balance_sheet)
        cashflow = await loop.run_in_executor(None, lambda: ticker.cashflow)
        
        result = {
            'symbol': symbol.strip(),
            'income_stmt': financials.to_dict(orient='index') if financials is not None and not financials.empty else {},
            'balance_sheet': balance_sheet.to_dict(orient='index') if balance_sheet is not None and not balance_sheet.empty else {},
            'cashflow': cashflow.to_dict(orient='index') if cashflow is not None and not cashflow.empty else {}
        }
        
        return result
    except Exception as e:
        raise Exception(f"Failed to get financials for '{symbol}': {e}")

@function_tool
async def get_recommendations(symbol: str) -> Dict[str, Any]:
    """
    Get analyst recommendations for a ticker.
    
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL').
    
    Returns:
        Dict[str, Any]: Dictionary containing recommendation data.
    
    Raises:
        ValueError: If symbol is empty or None.
        Exception: If the yfinance API call fails.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        recommendations = await loop.run_in_executor(None, lambda: ticker.recommendations)
        
        if recommendations is not None and not recommendations.empty:
            return {
                'symbol': symbol.strip(),
                'recommendations': recommendations.to_dict(orient='index')
            }
        else:
            return {'symbol': symbol.strip(), 'recommendations': {}}
    except Exception as e:
        raise Exception(f"Failed to get recommendations for '{symbol}': {e}")

@function_tool
async def get_calendar(symbol: str) -> Dict[str, Any]:
    """
    Get earnings calendar for a ticker.
    
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL').
    
    Returns:
        Dict[str, Any]: Dictionary containing calendar data including earnings dates.
    
    Raises:
        ValueError: If symbol is empty or None.
        Exception: If the yfinance API call fails.
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        calendar = await loop.run_in_executor(None, lambda: ticker.calendar)
        
        if calendar is not None:
            # Handle both DataFrame and dict return types (yfinance API varies)
            if isinstance(calendar, dict):
                return {
                    'symbol': symbol.strip(),
                    'calendar': calendar
                }
            elif hasattr(calendar, 'empty') and not calendar.empty:
                return {
                    'symbol': symbol.strip(),
                    'calendar': calendar.to_dict(orient='index')
                }
        return {'symbol': symbol.strip(), 'calendar': {}}
    except Exception as e:
        raise Exception(f"Failed to get calendar for '{symbol}': {e}")

@function_tool
async def get_news(symbol: str) -> List[Dict[str, Any]]:
    """
    Get news articles related to a ticker.
    
    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL').
    
    Returns:
        List[Dict[str, Any]]: List of news article dictionaries. Each article contains:
            - id: Article identifier
            - content: Dictionary containing:
                - title: Article title
                - summary: Article summary
                - pubDate: Publication date (ISO format)
                - displayTime: Display time
                - provider: Dictionary with displayName and url
                - canonicalUrl: Dictionary with article URL
                - thumbnail: Dictionary with image URLs and metadata
                - And other metadata fields
    
    Raises:
        ValueError: If symbol is empty or None.
        Exception: If the yfinance API call fails.
    
    Note:
        The news structure from yfinance has a nested format where article details
        are contained within a 'content' key. This method returns the raw structure
        as provided by yfinance. To access the title, use: news[0]['content']['title']
    """
    if not symbol or not symbol.strip():
        raise ValueError("Symbol cannot be empty or None.")
    
    try:
        loop = asyncio.get_running_loop()
        ticker = await loop.run_in_executor(None, yf.Ticker, symbol.strip())
        news = await loop.run_in_executor(None, lambda: ticker.news)
        
        return news if news else []
    except Exception as e:
        raise Exception(f"Failed to get news for '{symbol}': {e}")


@function_tool
async def download_market_data(
    symbols: Union[str, List[str]],
    period: Optional[str] = "1mo",
    interval: Optional[str] = "1d",
    start: Optional[str] = None,
    end: Optional[str] = None,
    prepost: bool = False,
    auto_adjust: bool = True,
    actions: bool = True,
    repair: bool = False,
    group_by: str = "ticker",
    progress: bool = False
) -> Dict[str, Any]:
    """
    Download historical market data for one or more ticker symbols.
    
    This is a convenience method that wraps yfinance.download() for downloading
    data for multiple tickers at once.
    
    Args:
        symbols (Union[str, List[str]]): Single ticker symbol or list of symbols.
        period (Optional[str]): Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max.
            Default: "1mo"
        interval (Optional[str]): Valid intervals: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo.
            Default: "1d"
        start (Optional[str]): Download start date string (YYYY-MM-DD) or datetime.
        end (Optional[str]): Download end date string (YYYY-MM-DD) or datetime.
        prepost (bool): Include pre and post market data. Default: False
        auto_adjust (bool): Adjust all OHLC automatically. Default: True
        actions (bool): Download dividends and stock splits data. Default: True
        repair (bool): Repair obvious price errors. Default: False
        group_by (str): Group by 'ticker' or 'column'. Default: "ticker"
        progress (bool): Show download progress. Default: False
    
    Returns:
        Dict[str, Any]: Dictionary containing downloaded market data.
    
    Raises:
        ValueError: If symbols is empty or invalid parameters provided.
        Exception: If the yfinance API call fails.
    """
    if not symbols:
        raise ValueError("Symbols cannot be empty or None.")
    
    # Convert single symbol to list
    if isinstance(symbols, str):
        symbols = [symbols]
    
    # Validate period if provided
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    if period and period not in valid_periods:
        raise ValueError(f"Period must be one of {valid_periods}, got '{period}'.")
    
    # Validate interval if provided
    valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    if interval and interval not in valid_intervals:
        raise ValueError(f"Interval must be one of {valid_intervals}, got '{interval}'.")
    
    try:
        loop = asyncio.get_running_loop()
        
        # Build parameters for download call
        download_params = DictUtils.build_params(
            period=period,
            interval=interval,
            start=start,
            end=end,
            prepost=prepost,
            auto_adjust=auto_adjust,
            actions=actions,
            repair=repair,
            group_by=group_by,
            progress=progress
        )
        
        # Download data
        download_func = partial(yf.download, symbols, **download_params)
        data = await loop.run_in_executor(None, download_func)
        
        # Convert DataFrame to dict
        if data is not None and not data.empty:
            return {
                'symbols': symbols,
                'data': data.to_dict(orient='index'),
                'period': period,
                'interval': interval
            }
        else:
            return {
                'symbols': symbols,
                'data': {},
                'period': period,
                'interval': interval
            }
    except Exception as e:
        raise Exception(f"Failed to download market data for '{symbols}': {e}")



# ------------------------------------------------------------
# Main tests
# ------------------------------------------------------------

def _parse_result(result) -> Any:
    """Parse result - handles both dict and JSON string returns."""
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # Tool returned an error string
            return {"_error": result}
    return result


async def main():
    """Smoke tests for all finance tools."""
    
    test_symbol = "AAPL"
    
    # Test 1: get_ticker_info
    print("=" * 60)
    print("Test 1: get_ticker_info")
    print("=" * 60)
    result = await get_ticker_info.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbol": test_symbol})
    )
    parsed = _parse_result(result)
    print(f"Symbol: {test_symbol}")
    print(f"Company: {parsed.get('longName', 'N/A')}")
    print(f"Sample keys: {list(parsed.keys())[:10]}...")
    print()

    # Test 2: get_historical_data
    print("=" * 60)
    print("Test 2: get_historical_data")
    print("=" * 60)
    result = await get_historical_data.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbol": test_symbol, "period": "5d", "interval": "1d"})
    )
    parsed = _parse_result(result)
    print(f"Symbol: {parsed.get('symbol')}")
    print(f"Period: {parsed.get('period')}, Interval: {parsed.get('interval')}")
    print(f"Data points: {len(parsed.get('data', {}))}")
    print()

    # Test 3: get_financials
    print("=" * 60)
    print("Test 3: get_financials")
    print("=" * 60)
    result = await get_financials.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbol": test_symbol})
    )
    parsed = _parse_result(result)
    print(f"Symbol: {parsed.get('symbol')}")
    print(f"Has income_stmt: {bool(parsed.get('income_stmt'))}")
    print(f"Has balance_sheet: {bool(parsed.get('balance_sheet'))}")
    print(f"Has cashflow: {bool(parsed.get('cashflow'))}")
    print()

    # Test 4: get_recommendations
    print("=" * 60)
    print("Test 4: get_recommendations")
    print("=" * 60)
    result = await get_recommendations.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbol": test_symbol})
    )
    parsed = _parse_result(result)
    print(f"Symbol: {parsed.get('symbol')}")
    print(f"Recommendation entries: {len(parsed.get('recommendations', {}))}")
    print()

    # Test 5: get_calendar
    print("=" * 60)
    print("Test 5: get_calendar")
    print("=" * 60)
    result = await get_calendar.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbol": test_symbol})
    )
    parsed = _parse_result(result)
    print(f"Symbol: {parsed.get('symbol')}")
    print(f"Calendar entries: {len(parsed.get('calendar', {}))}")
    print()

    # Test 6: get_news
    print("=" * 60)
    print("Test 6: get_news")
    print("=" * 60)
    result = await get_news.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbol": test_symbol})
    )
    parsed = _parse_result(result)
    print(f"News articles: {len(parsed)}")
    if parsed:
        first_article = parsed[0]
        title = first_article.get('content', {}).get('title', 'N/A')
        print(f"First article title: {title[:60]}..." if len(title) > 60 else f"First article title: {title}")
    print()

    # Test 7: download_market_data
    print("=" * 60)
    print("Test 7: download_market_data")
    print("=" * 60)
    result = await download_market_data.on_invoke_tool(
        ctx=None,
        input=json.dumps({"symbols": ["AAPL", "MSFT"], "period": "5d", "interval": "1d"})
    )
    parsed = _parse_result(result)
    print(f"Symbols: {parsed.get('symbols')}")
    print(f"Period: {parsed.get('period')}, Interval: {parsed.get('interval')}")
    print(f"Data points: {len(parsed.get('data', {}))}")
    print()

    print("=" * 60)
    print("All 7 smoke tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())