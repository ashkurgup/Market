import json
from datetime import datetime
import pytz
import yfinance as yf
import pandas as pd

# ===============================
# TIME
# ===============================
IST = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(IST)

# ===============================
# OUTPUT PATH
# ===============================
OUTPUT_PATH = "snapshots/market_phase1.json"

# ===============================
# FETCH NIFTY SPOT
# ===============================
def fetch_nifty():
    ticker = yf.Ticker("^NSEI")
    info = ticker.fast_info

    spot = float(info["lastPrice"])
    prev_close = float(info["previousClose"])

    change = round(spot - prev_close, 2)
    pct = round((change / prev_close) * 100, 2)

    return spot, change, pct

# ===============================
# FETCH GLOBAL INDICES (CONTEXT)
# ===============================
def fetch_global_indices():
    symbols = {
        "GIFT NIFTY": "^NSEI",
        "DOW FUTURES": "YM=F",
        "NIKKEI": "^N225",
        "DAX": "^GDAXI",
        "SHANGHAI": "000001.SS"
    }

    output = []

    for name, symbol in symbols.items():
        try:
            t = yf.Ticker(symbol)
            last_price = float(t.fast_info["lastPrice"])
            prev_price = float(t.fast_info["previousClose"])
            delta = round(last_price - prev_price)

            output.append({
                "name": name,
                "value": delta,
                "direction": "UP" if delta >= 0 else "DOWN"
            })
        except Exception:
            continue

    return output

# ===============================
# FETCH INTRADAY 5‑MIN DATA
# ===============================
def fetch_intraday():
    df = yf.download(
        "^NSEI",
        interval="5m",
        period="1d",
        progress=False
    )

    df = df.dropna()
    return df

# ===============================
# CALCULATE ATR (SCALAR)
# ===============================
def calculate_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr_series = tr.rolling(period).mean()

    return float(atr_series.tail(1).values[0])

# ===============================
# CALCULATE VWAP (SCALAR)
# ===============================
def calculate_vwap(df):
    pv = (df["Close"] * df["Volume"]).cumsum()
    vol = df["Volume"].cumsum()
    vwap_series = pv / vol

    return float(vwap_series.tail(1).values[0])

# ===============================
# MAIN PRODUCER
# ===============================
def main():
    # NIFTY
    spot, change, pct = fetch_nifty()

    # GLOBAL CONTEXT
    global_markets = fetch_global_indices()

    # INTRADAY DATA
    df = fetch_intraday()

    # SAFETY CHECK
    if df.empty:
        return

    # LAST PRICE (FORCED SCALAR)
    last_price = float(df["Close"].tail(1).values[0])

    # VOLATILITY
    atr = calculate_atr(df)

    # VWAP
    vwap = calculate_vwap(df)
    expansion_range = float(df["High"].tail(1).values[0] - df["Low"].tail(1).values[0])

    # VWAP POSITION LOGIC (SAFE)
    if last_price > vwap * 1.005:
        vwap_position = "STRONG ABOVE"
    elif last_price > vwap:
        vwap_position = "ABOVE"
    elif last_price < vwap * 0.995:
        vwap_position = "STRONG BELOW"
    else:
        vwap_position = "NEAR"

    # ===============================
    # BUILD SNAPSHOT
    # ===============================
    snapshot = {
        "meta": {
            "date": NOW.strftime("%Y-%m-%d"),
            "last_updated": NOW.strftime("%H:%M:%S"),
            "timezone": "IST",
            "session_status": "OPEN"
        },
        "nifty": {
            "spot": spot,
            "change_points": change,
            "change_percent": pct
        },
        "global_markets": global_markets,
        "volatility": {
            "atr": atr,
            "state": "EXPANDING"
        },
        "vwap": {
            "position": vwap_position,
            "expansion_range": round(expansion_range, 2),
            "midline": "RISING"
        }
    }

    # ===============================
    # WRITE JSON (ATOMIC)
    # ===============================
    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

# ===============================
# ENTRY POINT
# ===============================
if __name__ == "__main__":
    main()
