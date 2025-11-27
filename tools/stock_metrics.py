import yfinance as yf

def get_stock_metrics(ticker: str) -> dict:
    """
    Retrieves fundamental metrics for a given stock ticker (e.g., 'AAPL', 'GOOG').
    Returns P/E ratio, Market Cap, and recent dividend info.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Simplified data for the agent to digest
        data = {
            "current_price": info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "free_cash_flow": info.get("freeCashflow"),
            "sector": info.get("sector")
        }
        return data
    except Exception as e:
        return {"error": f"Could not fetch data for {ticker}: {str(e)}"}