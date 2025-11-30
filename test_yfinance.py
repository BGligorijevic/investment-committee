import yfinance as yf


def test_history():
    ticker = "AAPL"
    stock = yf.Ticker(ticker)
    # Get 1 month of history
    hist = stock.history(period="1mo")
    print(hist.head())
    print(hist.tail())

    # Check if we can get a simple string representation for the LLM
    print("\nString Representation:")
    # We probably only need Date and Close, maybe Volume
    subset = hist[["Close", "Volume"]]
    print(subset.to_string())


if __name__ == "__main__":
    test_history()
