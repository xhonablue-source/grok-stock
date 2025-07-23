import streamlit as st
import pandas as pd
import yfinance as yf
from ta.trend import ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Pre-Explosion Signal Scanner", layout="wide")
st.title("🚨 Day-Before Explosion Signal Scanner")

# Load tickers with better error handling
@st.cache_data
def load_tickers():
    try:
        # Try primary source
        sp500_url = "https://datahub.io/core/s-and-p-500-companies/r/data.csv"
        tickers_df = pd.read_csv(sp500_url)
        tickers = tickers_df["Symbol"].tolist()
        st.success(f"✅ Loaded {len(tickers)} tickers from datahub.io")
        return tickers
    except Exception as e:
        st.warning(f"Primary source failed: {e}")
        try:
            # Fallback to Wikipedia
            sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            sp500_table = pd.read_html(sp500_url)[0]
            tickers = sp500_table['Symbol'].tolist()
            tickers = [t.replace('.', '-') for t in tickers]
            st.success(f"✅ Loaded {len(tickers)} tickers from Wikipedia")
            return tickers
        except Exception as e2:
            st.error(f"Fallback failed: {e2}")
            # Ultimate fallback
            tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'ADBE', 'CRM', 'PYPL', 'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO',
                'ORCL', 'IBM', 'NOW', 'INTU', 'MU', 'AMAT', 'ADI', 'LRCX',
                'KLAC', 'MCHP', 'SNPS', 'CDNS', 'FTNT', 'PANW', 'CRWD', 'ZS',
                'DDOG', 'NET', 'SNOW', 'PLTR', 'COIN', 'SQ', 'SHOP', 'ROKU',
                'ZM', 'DOCU', 'OKTA', 'TWLO', 'SPLK', 'WORK', 'DBX', 'BOX'
            ]
            st.info(f"Using {len(tickers)} sample tickers")
            return tickers

# Load tickers
tickers = load_tickers()

# Scanner thresholds (IDENTICAL to original)
min_price, max_price = 3, 15
min_volume = 500000
min_adx = 40

# Display criteria
st.subheader("🎯 Explosion Detection Criteria")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Price Range", f"${min_price} - ${max_price}")
    st.metric("Min Volume", f"{min_volume:,}")
with col2:
    st.metric("Min ADX", min_adx)
    st.metric("DI Spread", "≥ 10")
with col3:
    st.metric("RSI Range", "60-75")
    st.metric("Stoch %K", "> 70 & > %D")

# Add scan button
if st.button("🚀 Start Explosion Scan", type="primary"):
    scan_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_tickers = len(tickers)
    
    for i, ticker in enumerate(tickers):
        try:
            # Update progress
            progress = (i + 1) / total_tickers
            progress_bar.progress(progress)
            status_text.text(f"Scanning {ticker}... ({i+1}/{total_tickers})")
            
            # Download data
            df = yf.download(ticker, period="2mo", interval="1d", progress=False)
            if len(df) < 20:
                continue
            
            # Calculate indicators (IDENTICAL to original)
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
            
            # IDENTICAL explosion criteria
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
                    "DI_Diff": round(yesterday["+DI"] - yesterday["-DI"], 2),
                    "RSI": round(yesterday["RSI"], 2),
                    "%K": round(yesterday["%K"], 2),
                    "%D": round(yesterday["%D"], 2),
                    "Volume": int(yesterday["Volume"]),
                    "Vol_Ratio": round(yesterday["Volume"] / yesterday["Vol10Avg"], 2),
                })
        except Exception:
            continue
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display results
    if scan_results:
        st.success(f"✅ Found {len(scan_results)} potential explosion setups!")
        
        results_df = pd.DataFrame(scan_results)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Setups Found", len(results_df))
        with col2:
            st.metric("Avg Price", f"${results_df['Price'].mean():.2f}")
        with col3:
            st.metric("Avg ADX", f"{results_df['ADX'].mean():.1f}")
        with col4:
            st.metric("Avg Vol Ratio", f"{results_df['Vol_Ratio'].mean():.1f}x")
        
        # Display table
        st.dataframe(
            results_df,
            use_container_width=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Symbol", width="small"),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Volume": st.column_config.NumberColumn("Volume", format="%d"),
                "Vol_Ratio": st.column_config.NumberColumn("Vol Ratio", format="%.1fx"),
            }
        )
        
        # Download button
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Results",
            data=csv,
            file_name=f"explosion_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
        
    else:
        st.warning("🚫 No valid tickers matched the explosion preconditions.")
        st.info("💡 These are very strict criteria designed to catch rare setups.")

# Add footer with criteria explanation
st.markdown("---")
st.markdown("""
### 🚨 About Explosion Signals
These criteria are designed to identify stocks positioned for potential significant moves:
- **Price Range ($3-$15)**: Sweet spot for explosive moves
- **High ADX (≥40)**: Strong trending momentum  
- **DI Spread (≥10)**: Clear directional bias
- **RSI (60-75)**: Strong but not overbought
- **Stoch %K >70**: Near resistance breakout
- **Volume Surge**: 2x+ average volume confirmation
""")

st.markdown("⚠️ **Disclaimer**: These are technical signals only. Always perform additional analysis before trading.")
