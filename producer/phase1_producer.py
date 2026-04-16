import json
from datetime import datetime
import pytz
import yfinance as yf
import pandas as pd

IST = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(IST)

OUTPUT_PATH = "snapshots/market_phase1.json"

def fetch_nifty():
    t = yf.Ticker("^NSEI")
    info = t.fast_info
    spot = info["lastPrice"]
    prev = info["previousClose"]
    change = round(spot - prev, 2)
    pct = round((change / prev) * 100, 2)
    return spot, change, pct

def fetch_global():
    symbols = {
        "GIFT NIFTY": "^NSEI",
        "DOW FUTURES": "YM=F",
        "NIKKEI": "^N225",
        "DAX": "^GDAXI",
        "SHANGHAI": "000001.SS"
    }

    data = []
    for name, sym in symbols.items():
        try:
            t = yf.Ticker(sym)
            chg = round(t.fast_info["lastPrice"] - t.fast_info["previousClose"])
            data.append({
                "name": name,
                "value": chg,
                "direction": "UP" if chg >= 0 else "DOWN"
            })
        except:
            continue
    return data

def fetch_intraday():
    df = yf.download("^NSEI", interval="5m", period="1d", progress=False)
    df.dropna(inplace=True)
    return df

def calc_atr(df, period=14):
    hl = df["High"] - df["Low"]
    hc = abs(df["High"] - df["Close"].shift())
    lc = abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return round(tr.rolling(period).mean().iloc[-1], 2)

def calc_vwap(df):
    pv = (df["Close"] * df["Volume"]).cumsum()
    vol = df["Volume"].cumsum()
    vwap_series = pv / vol
    return float(vwap_series.iloc[-1])


def main():
    spot, change, pct = fetch_nifty()
    globals_ = fetch_global()
    df = fetch_intraday()

    atr = calc_atr(df)
    vwap = calc_vwap(df)
    last_price = df["Close"].iloc[-1]

    vwap_pos = (
        "STRONG ABOVE" if last_price > vwap * 1.005 else
        "ABOVE" if last_price > vwap else
        "BELOW"
    )

    snapshot = {
        "meta": {
            "date": NOW.strftime("%Y-%m-%d"),
            "last_updated": NOW.strftime("%H:%M:%S"),
            "timezone": "IST",
            "session_status": "OPEN"
        },
        "nifty": {
            "spot": round(spot, 2),
            "change_points": change,
            "change_percent": pct
        },
        "global_markets": globals_,
        "volatility": {
            "atr": atr,
            "state": "EXPANDING"
        },
        "vwap": {
            "position": vwap_pos,
            "expansion_range": round(df["High"].iloc[-1] - df["Low"].iloc[-1], 2),
            "midline": "RISING"
        }
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    main()
