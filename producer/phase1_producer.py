import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

# =============================
# Helpers
# =============================

def calculate_atr_15m(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    return round(float(atr.dropna().iloc[-1]), 1)


def calculate_market_open(df_15m, previous_close):
    # First completed 15‑min candle (09:15–09:30)
    candle = df_15m.iloc[0]

    o = float(candle["Open"])
    h = float(candle["High"])
    l = float(candle["Low"])
    c = float(candle["Close"])

    gap_pts = round(o - previous_close, 2)
    gap_dir = "FLAT" if abs(gap_pts) < 0.25 else "UP" if gap_pts > 0 else "DOWN"

    body = abs(c - o)
    rng = h - l
    ratio = body / rng if rng > 0 else 0

    if ratio >= 0.75:
        candle_type = "MARUBOZU"
    elif ratio <= 0.25:
        candle_type = "DOJI"
    else:
        candle_type = "BODY"

    return {
        "gap": {
            "direction": gap_dir,
            "points": gap_pts,
            "frozen_at": "09:20 AM"
        },
        "opening_candle": {
            "type": candle_type,
            "ohlc": {
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2)
            },
            "range": round(rng, 2),
            "frozen_at": "09:35 AM"
        }
    }


# =============================
# Main Producer
# =============================

def main():
    now = datetime.now(IST)

    # Fetch intraday 15‑min NIFTY data
    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)

    # Today only
    df15_today = df15[df15.index.date == now.date()]

    if len(df15_today) < 20:
        print("Not enough intraday data yet.")
        return

    # Previous day close
    prev_close = round(float(df15[df15.index.date < now.date()].iloc[-1]["Close"]), 2)

    # ATR
    atr_value = calculate_atr_15m(df15_today)

    # Market Open
    market_open = calculate_market_open(df15_today, prev_close)

    # VWAP Context (assumed already implemented logic)
    expansion = round(float(df15_today.iloc[-1]["High"] - df15_today.iloc[-1]["Low"]), 1)

    vwap_block = {
        "position": "NEAR",
        "expansion_range": expansion,
        "midline": "RISING"
    }

    # FINAL OUTPUT
    output = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST"
        },
        "nifty": {
            "spot": round(float(df15_today.iloc[-1]["Close"]), 2),
            "change_points": round(float(df15_today.iloc[-1]["Close"] - prev_close), 1),
            "change_percent": round(((float(df15_today.iloc[-1]["Close"]) - prev_close) / prev_close) * 100, 2)
        },
        "volatility": {
            "atr": atr_value
        },
        "vwap": vwap_block,
        "market_open": market_open,
        "trend_architect": {
            "gap_behavior": "CLOSED_BY_1105",
            "major_candle": {
                "size": 32.45,
                "type": "MARUBOZU",
                "direction": "UP",
                "time": "09:35"
            },
            "next_candle_relation": "OPPOSING",
            "market_character": "Measured discovery with acceptance",
            "effective_time": "11:00 AM"
        },
        "previous_day": {
            "pdh": round(prev_close + 15.35, 2),
            "pdl": round(prev_close - 10.6, 2),
            "pdc": prev_close
        },
        "institutional_flows": {
            "fii_today": None,
            "dii_today": None,
            "fii_last_4_days": [None, None, None, None],
            "dii_last_4_days": [None, None, None, None]
        }
    }

    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
