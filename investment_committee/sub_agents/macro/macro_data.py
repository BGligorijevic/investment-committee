import yfinance as yf


def get_market_overview() -> dict:
    """
    Retrieves a snapshot of the current macro market environment.
    Returns key indices for Equities, Rates, and Volatility.
    """
    indices = {
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
        "10Y Treasury Yield": "^TNX",
        "VIX (Volatility)": "^VIX",
    }

    data = {}
    for name, ticker in indices.items():
        try:
            t = yf.Ticker(ticker)
            # Fetch 2 days to get previous close if current is unavailable (e.g. weekend)
            hist = t.history(period="2d")
            if not hist.empty:
                latest = hist.iloc[-1]
                # Format nicely
                price = latest["Close"]
                data[name] = f"{price:.2f}"
            else:
                data[name] = "Data Unavailable"
        except Exception as e:
            data[name] = f"Error: {str(e)}"

    return data
