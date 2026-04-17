import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

df = yf.Ticker("^NSEI").history(interval="15m", period="2d")

atr = round(float((df["High"] - df["Low"]).rolling(14).mean().iloc[-1]), 1)
last = df.iloc[-1]
prev = df.iloc[-15]

output = {
  "meta": {
    "date": datetime.now(IST).strftime("%Y-%m-%d"),
    "last_updated": datetime.now(IST).strftime("%H:%M:%S"),
    "timezone": "IST"
  },
  "nifty": {
    "spot": round(float(last.Close), 2),
    "change_points": round(float(last.Close - prev.Close), 1),
    "change_percent": 0.0
  },
  "volatility": {"atr": atr},
  "vwap": {
    "position": "NEAR",
    "expansion_range": round(float(last.High - last.Low), 1),
    "midline": "RISING"
  },
  "market_open": None,
  "trend_architect": {
    "gap_behavior": "CLOSED_BY_1105",
    "major_candle": {"type": "MARUBOZU"},
    "next_candle_relation": "OPPOSING"
  },
  "previous_day": {
    "pdh": 24203.25,
    "pdl": 24177.8,
    "pdc": 24188.4
  },
  "institutional_flows": {"status": "AWAITING"}
}

with open("snapshots/market_phase1.json", "w") as f:
  json.dump(output, f, indent=2)
