import yfinance as yf
import pandas as pd
import ta
from ta.trend import ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 🚨 Day-Before Explosion Signal Scanner
print("🚨 Day-Before Explosion Signal Scanner")
print("=" * 50)

# Load S&P 500 tickers with better error handling
print("🔎 Loading S&P 500 tickers...")
try:
    # Try primary source first
    sp500_url = "https://datahub.io/core/s-and-p-500-companies/r/data.csv"
    tickers_df = pd.read_csv(sp500_url)
    tickers = tickers_df["Symbol"].tolist()
    print(f"✅ Loaded {len(tickers)} tickers from datahub.io")
except Exception as e:
    print(f"⚠️ Primary source failed: {e}")
    print("🔄 Using fallback ticker list...")
    # Fallback to Wikipedia source
    try:
        sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        sp500_table = pd.read_html(sp500_url)[0]
        tickers = sp500_table['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]  # Clean for yfinance
        print(f"✅ Loaded {len(tickers)} tickers from Wikipedia")
    except Exception as e2:
        print(f"⚠️ Fallback also failed: {e2}")
        print("🔄 Using sample ticker list...")
        # Ultimate fallback - sample of major S&P 500 stocks
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'ADBE', 'CRM', 'PYPL', 'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO',
            'ORCL', 'IBM', 'NOW', 'INTU', 'MU', 'AMAT', 'ADI', 'LRCX',
            'KLAC', 'MCHP', 'SNPS', 'CDNS', 'FTNT', 'PANW', 'CRWD', 'ZS',
            'DDOG', 'NET', 'SNOW', 'PLTR', 'COIN', 'SQ', 'SHOP', 'ROKU',
            'ZM', 'DOCU', 'OKTA', 'TWLO', 'SPLK', 'WORK', 'DBX', 'BOX'
        ]
        print(f"✅ Using {len(tickers)} sample tickers")

# IDENTICAL Scanner thresholds from your Streamlit app
min_price = 3
max_price = 15
min_volume = 500000
min_adx = 40

print(f"📈 Scanning {len(tickers)} tickers with explosion criteria...")
print("🎯 Criteria:")
print(f"   • Price: ${min_price} - ${max_price}")
print(f"   • Volume: >= {min_volume:,}")
print(f"   • ADX: >= {min_adx}")
print(f"   • +DI - (-DI): >= 10")
print(f"   • RSI: 60-75")
print(f"   • %K > 70 and %K > %D")
print(f"   • Volume > 2x 10-day average")
print()

scan_results = []

for i, ticker in enumerate(tickers):
    try:
        # Show progress every 50 tickers
        if i % 50 == 0:
            print(f"Progress: {i}/{len(tickers)} ({i/len(tickers)*100:.1f}%)")
        
        # Download 2 months of daily data (identical to Streamlit)
        df = yf.download(ticker, period="2mo", interval="1d", progress=False)
        
        if len(df) < 20:  # Need enough data for indicators
            continue
        
        # Calculate technical indicators (IDENTICAL to Streamlit)
        df["RSI"] = RSIIndicator(df["Close"]).rsi()
        
        adx = ADXIndicator(df["High"], df["Low"], df["Close"])
        df["ADX"] = adx.adx()
        df["+DI"] = adx.plus_di()
        df["-DI"] = adx.minus_di()
        
        stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
        df["%K"] = stoch.stoch()
        df["%D"] = stoch.stoch_signal()
        
        df["Vol10Avg"] = df["Volume"].rolling(window=10).mean()
        
        # Get yesterday's data (IDENTICAL logic)
        yesterday = df.iloc[-2]
        
        # IDENTICAL explosion criteria - Match specs seen in ABVX day prior
        if (
            min_price <= yesterday["Close"] <= max_price and
            yesterday["Volume"] > min_volume and
            yesterday["ADX"] >= min_adx and
            (yesterday["+DI"] - yesterday["-DI"]) >= 10 and
            60 <= yesterday["RSI"] <= 75 and
            yesterday["%K"] > 70 and
            yesterday["%K"] > yesterday["%D"] and
            yesterday["Volume"] > 2 * yesterday["Vol10Avg"]
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
                "Vol10Avg": int(yesterday["Vol10Avg"]),
                "Vol_Ratio": round(yesterday["Volume"] / yesterday["Vol10Avg"], 2),
            })
            print(f"✅ EXPLOSION SETUP FOUND: {ticker}")
    
    except Exception as e:
        # Skip problematic tickers silently (like Streamlit)
        continue

print(f"\n🔍 Scan complete!")

# Display results (identical format to Streamlit)
if scan_results:
    print(f"✅ Found {len(scan_results)} potential explosion setups.")
    print("\n📊 EXPLOSION CANDIDATES:")
    print("=" * 120)
    
    # Create DataFrame identical to Streamlit display
    results_df = pd.DataFrame(scan_results)
    print(results_df.to_string(index=False))
    
    # Save results with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"explosion_signals_{timestamp}.csv"
    results_df.to_csv(filename, index=False)
    print(f"\n📁 Results saved to '{filename}'")
    
    # Summary statistics
    print(f"\n📈 Summary:")
    print(f"   • Total scanned: {len(tickers)}")
    print(f"   • Explosion setups found: {len(results_df)}")
    print(f"   • Success rate: {len(results_df)/len(tickers)*100:.3f}%")
    print(f"   • Average price: ${results_df['Price'].mean():.2f}")
    print(f"   • Average ADX: {results_df['ADX'].mean():.1f}")
    print(f"   • Average volume ratio: {results_df['Vol_Ratio'].mean():.1f}x")
    
else:
    print("🚫 No valid tickers matched the explosion preconditions.")
    print("💡 These are very strict criteria designed to catch rare setups.")

print(f"\n🚨 IMPORTANT: These are 'day-before explosion' signals.")
print("📈 Stocks meeting these criteria may be positioned for significant moves.")
print("⚠️ Always perform additional analysis before trading decisions.")
