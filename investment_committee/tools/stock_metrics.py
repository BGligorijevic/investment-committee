import yfinance as yf


def get_stock_metrics(ticker: str) -> dict:
    """
    Retrieves fundamental metrics for a given stock ticker (e.g., 'AAPL', 'GOOG').
    Returns P/E ratio, Market Cap, and recent dividend info.
    """
    try:
        print(f"DEBUG: get_stock_metrics called with '{ticker}'")
        stock = yf.Ticker(ticker)
        info = stock.info

        print(info.keys())

        # Simplified data for the agent to digest
        data = {
            "current_price": info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "free_cash_flow": info.get("freeCashflow"),
            "return_on_equity": info.get("returnOnEquity"),
            "sector": info.get("sector"),
        }
        return data
    except Exception as e:
        return {"error": f"Could not fetch data for {ticker}: {str(e)}"}


def get_stock_history(ticker: str, period: str = "1mo") -> str:
    """
    Retrieves historical stock price data for a given ticker.
    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").
        period: The period of history to fetch (e.g., "1mo", "3mo", "1y").
    Returns:
        A string representation of the stock history (Date, Close, Volume).
    """
    try:
        print(f"DEBUG: get_stock_history called with '{ticker}' for '{period}'")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return f"No history found for {ticker}"

        # Select only relevant columns for the LLM to analyze trends
        subset = hist[["Close", "Volume"]]
        return subset.to_string()
    except Exception as e:
        return f"Error fetching history for {ticker}: {str(e)}"


def find_company_ticker(company_name: str) -> str:
    """
    Searches for the stock ticker symbol associated with a company name.
    Args:
        company_name: The name of the company (e.g., "Microsoft", "Apple").
    Returns:
        The ticker symbol (e.g., "MSFT", "AAPL") if found, or an error message.
    """
    try:
        print(f"DEBUG: find_company_ticker called with '{company_name}'")
        search = yf.Search(company_name, max_results=1, news_count=0)
        if search.quotes:
            ticker = search.quotes[0]["symbol"]
            print(f"DEBUG: find_company_ticker found '{ticker}'")
            return ticker
        print(f"DEBUG: find_company_ticker found nothing for '{company_name}'")
        return f"No ticker found for {company_name}"
    except Exception as e:
        print(f"DEBUG: find_company_ticker error: {e}")
        return f"Error searching for ticker: {str(e)}"
