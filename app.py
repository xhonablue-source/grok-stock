import streamlit as st
import pandas as pd
import yfinance as yf
from ta.trend import ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from datetime import datetime, timedelta

st.set_page_config(page_title="Pre-Explosion Signal Scanner", layout="wide")
st.title("🚨 Day-Before Explosion Signal Scanner")

# Define a sample ticker list (replace with Russell, NYSE, etc.)
sp500_url = "https://datahub.io/core/s-and-p-500-companies/r/data.csv"
tickers_df = pd.read_csv(sp500_url)
tickers = tickers_df["Symbol"].tolist()

# Scanner thresholds
min_price, max_price = 3, 15
min_volume = 500000
min_adx = 40

scan_results = []

st.info("Scanning tickers...")

for ticker in tickers:
    try:
        df = yf.download(ticker, period="2mo", interval="1d", progress=False)
        if len(df) < 20:
            continue

        df["RSI"] = RSIIndicator(df["Close"]).rsi()
        adx = ADXIndicator(df["High"], df["Low"], df["Close"])
        df["ADX"] = adx.adx()
        df["+DI"] = adx.plus_di()
        df["-DI"] = adx.minus_di()
        stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
        df["%K"] = stoch.stoch()
        df["%D"] = stoch.stoch_signal()
        df["Vol10Avg"] = df["Volume"].rolling(window=10).mean()

        yesterday = df.iloc[-2]

        # Match specs seen in ABVX day prior
        if (
            min_price <= yesterday["Close"] <= max_price
            and yesterday["Volume"] > min_volume
            and yesterday["ADX"] >= min_adx
            and (yesterday["+DI"] - yesterday["-DI"]) >= 10
            and 60 <= yesterday["RSI"] <= 75
            and yesterday["%K"] > 70
            and yesterday["%K"] > yesterday["%D"]
            and yesterday["Volume"] > 2 * yesterday["Vol10Avg"]
        ):
            scan_results.append({
                "Ticker": ticker,
                "Price": round(yesterday["Close"], 2),
                "ADX": round(yesterday["ADX"], 2),
                "+DI": round(yesterday["+DI"], 2),
                "-DI": round(yesterday["-DI"], 2),
                "RSI": round(yesterday["RSI"], 2),
                "%K": round(yesterday["%K"], 2),
                "%D": round(yesterday["%D"], 2),
                "Volume": int(yesterday["Volume"]),
            })

    except Exception:
        continue

if scan_results:
    st.success(f"✅ Found {len(scan_results)} potential explosion setups.")
    st.dataframe(pd.DataFrame(scan_results))
else:
    st.warning("No valid tickers matched the explosion preconditions.")
