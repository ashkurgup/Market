import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import numpy as np

IST = pytz.timezone("Asia/Kolkata")
ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

# =============================
# ATR (15‑min)
# =============================
def calculate_atr_15m(df, period=14):
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(period).mean()
    return round(float(atr.dropna().iloc[-1]), 1)

# =============================
# CANDLE CLASSIFIER (FINAL)
# =============================
def classify_candle(o, h, l, c):
    rng = h - l
    body = abs(c - o)
    if rng == 0:
        return "DOJI", "NEUTRAL", 0

    body_pct = body / rng
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    # DOJI only if exact zero body
    if body == 0:
        return "DOJI", "NEUTRAL", 0

    color = "GREEN" if c > o else "RED"

    if body_pct >= 0.80:
        return "MARUBOZU", color, round(body_pct * 100)

    if lower_wick >= 2 * body and upper_wick <= 0.25 * body:
        return "HAMMER", color, round(body_pct * 100)

    if upper_wick >= 2 * body and lower_wick <= 0.25 * body:
        return "INVERTED HAMMER", color, round(body_pct * 100)

    if 0.15 <= body_pct < 0.40 and upper_wick > body and lower_wick > body:
        return "SPINNING TOP", color, round(body_pct * 100)

    return "OTHER", color, round(body_pct * 100)

# =============================
# PRICE‑CENTRIC VWAP
# =============================
def calculate_price_vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    mid = float(tp.mean())
    sd = float(tp.std()) if len(tp) > 1 else 0.0
    upper = mid + sd
    lower = mid - sd
    expansion = round(upper - lower, 2)
    return round(mid, 2), round(upper, 2), round(lower, 2), expansion

# =============================
# MARKET OPEN (FROZEN)
# =============================
def calculate_market_open(df_today, prev_close):
    first = df_today.iloc[0]
    o, h, l, c = map(float, (first["Open"], first["High"], first["Low"], first["Close"]))
    typ, col, body_pct = classify_candle(o, h, l, c)

    gap_pts = round(o - prev_close, 2)
    gap_dir = "FLAT" if abs(gap_pts) < 0.25 else ("UP" if gap_pts > 0 else "DOWN")

    return {
        "gap": {
            "direction": gap_dir,
            "points": gap_pts,
            "frozen_at": "09:20 IST",
        },
        "opening_candle": {
            "type": typ,
            "color": col,
            "size": round(abs(c - o), 2),
            "body_pct": body_pct,
            "range": round(h - l, 2),
            "ohlc": {
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
            },
            "frozen_at": "09:35 IST",
        },
    }

# =============================
# MAIN
# =============================
def main():
    now = datetime.now(IST)
    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)
    df_today = df15[df15.index.date == now.date()]

    if len(df_today) < 2:
        return

    prev_close = float(df15[df15.index.date < now.date()].iloc[-1]["Close"])
    last_close = float(df_today.iloc[-1]["Close"])

    atr = calculate_atr_15m(df_today)
    atr_sample = "Enough Sample" if len(df_today) >= ATR_PERIOD + 1 else "Less Sample"

    mid, upper, lower, vwap_exp = calculate_price_vwap(df_today)

    if last_close > upper:
        vwap_pos = "STRONG ABOVE"
    elif last_close > mid:
        vwap_pos = "ABOVE"
    elif last_close >= lower:
        vwap_pos = "NEAR"
    elif last_close >= mid - (upper - mid):
        vwap_pos = "BELOW"
    else:
        vwap_pos = "STRONG BELOW"

    if atr_sample == "Less Sample":
        chop = {"state": "Not Classified", "message": "Insufficient Volatility Sample"}
    elif vwap_exp < atr:
        chop = {"state": "High", "message": "Rotational / Mean‑Reversion Likely"}
    elif vwap_exp < atr * 1.5:
        chop = {"state": "Moderate", "message": "Expansion Needs Confirmation"}
    else:
        chop = {"state": "Low", "message": "Continuation‑Friendly Environment"}

    out = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST",
        },
        "nifty": {
            "spot": round(last_close, 2),
            "change_points": round(last_close - prev_close, 1),
            "change_percent": round(((last_close - prev_close) / prev_close) * 100, 2),
        },
        "volatility": {
            "atr": atr,
            "sample_status": atr_sample,
            "reliable_from": ATR_RELIABLE_FROM,
        },
        "choppiness": chop,
        "vwap": {
            "mid": mid,
            "upper": upper,
            "lower": lower,
            "expansion": vwap_exp,
            "position": vwap_pos,
            "midline": "RISING",
            "basis_candle_close": df_today.index[-1].strftime("%H:%M"),
        },
        "market_open": calculate_market_open(df_today, prev_close),
        "previous_day": {
            "pdh": 24203.25,
            "pdl": 24177.8,
            "pdc": 24188.4,
        },
    }

    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
