import yfinance as yf
import pandas as pd

def get_technical_analysis(ticker):
    try:
        # Fetch 1 month of daily stock data
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return f"Could not retrieve technical data for {ticker}. Please check the ticker symbol."
        
        # Current price
        current_price = hist['Close'].iloc[-1]
        
        # Calculate 14-day RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Calculate Short-Term Trend (Current price vs 20-day Simple Moving Average)
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        trend = "Bullish (Uptrend)" if current_price > sma_20 else "Bearish (Downtrend)"
        
        # Format the output for the LLM agent
        analysis = (
            f"Technical Analysis for {ticker}:\n"
            f"- Current Price: ${current_price:.2f}\n"
            f"- 14-Day RSI: {current_rsi:.2f} (Note: >70 is overbought, <30 is oversold)\n"
            f"- Short-Term Trend (vs 20-day SMA): {trend}\n"
        )
        return analysis
        
    except Exception as e:
        return f"Error fetching technical data: {str(e)}"
