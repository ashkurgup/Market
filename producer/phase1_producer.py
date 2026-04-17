import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# -----------------------------
# CONFIG
# -----------------------------
IST = pytz.timezone("Asia/Kolkata")
ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

# -----------------------------
# ATR (15‑min, 14 period)
# -----------------------------
def calculate_atr_15m(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
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

# -----------------------------
# VWAP (TradingView‑consistent)
# -----------------------------
def calculate_vwap_15m(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    vol = df["Volume"]
    vwap = (tp * vol).sum() / vol.sum()
    return round(float(vwap), 2)

# -----------------------------
# MARKET OPEN (FROZEN)
# -----------------------------
def calculate_market_open(df_today_15m, prev_close):
    first = df_today_15m.iloc[0]

    o = round(float(first["Open"]), 2)
    h = round(float(first["High"]), 2)
    l = round(float(first["Low"]), 2)
    c = round(float(first["Close"]), 2)

    range_pts = round(h - l, 2)
    body_pts = round(abs(c - o), 2)

    # Candle colour
    if body_pts <= range_pts * 0.25:
        candle_color = "NEUTRAL"
        candle_type = "DOJI"
    elif body_pts >= range_pts * 0.70:
        candle_type = "MARUBOZU"
        candle_color = "GREEN" if c > o else "RED"
    else:
        candle_type = "BODY"
        candle_color = "GREEN" if c > o else "RED"

    # Gap
    gap_pts = round(o - prev_close, 2)
    if abs(gap_pts) < 0.25:
        gap_dir = "FLAT"
    elif gap_pts > 0:
        gap_dir = "UP"
    else:
        gap_dir = "DOWN"

    return {
        "gap": {
            "direction": gap_dir,
            "points": gap_pts,
            "frozen_at": "09:20 IST"
        },
        "opening_candle": {
            "type": candle_type,
            "color": candle_color,
            "size": body_pts,
            "ohlc": {
                "open": o,
                "high": h,
                "low": l,
                "close": c
            },
            "range": range_pts,
            "frozen_at": "09:35 IST"
        }
    }

# -----------------------------
# MAIN
# -----------------------------
def main():
    now = datetime.now(IST)

    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)

    df_today = df15[df15.index.date == now.date()]
    if len(df_today) < 5:
        return

    prev_day_close = round(
        float(df15[df15.index.date < now.date()].iloc[-1]["Close"]), 2
    )

    # ATR
    atr_value = calculate_atr_15m(df_today)
    atr_sample_status = (
        "Enough Sample" if len(df_today) >= ATR_PERIOD + 1 else "Less Sample"
    )

    # VWAP
    vwap_value = calculate_vwap_15m(df_today)
    last_close = float(df_today.iloc[-1]["Close"])
    expansion = round(float(df_today.iloc[-1]["High"] - df_today.iloc[-1]["Low"]), 1)

    distance = last_close - vwap_value
    threshold = expansion * 0.15

    if abs(distance) <= threshold:
        vwap_position = "NEAR"
    elif distance > 0:
        vwap_position = "ABOVE"
    else:
        vwap_position = "BELOW"

    basis_time = df_today.index[-1].strftime("%H:%M")

    # Choppiness
    if atr_sample_status == "Less Sample":
        choppiness = {
            "state": "Not Classified",
            "message": "Insufficient Volatility Sample"
        }
    else:
        if atr_value <= 18:
            choppiness = {
                "state": "High",
                "message": "Rotational / Mean‑Reversion Likely"
            }
        elif atr_value <= 25:
            choppiness = {
                "state": "Moderate",
                "message": "Expansion Needs Confirmation"
            }
        else:
            choppiness = {
                "state": "Low",
                "message": "Continuation‑Friendly Environment"
            }

    market_open_block = calculate_market_open(df_today, prev_day_close)

    output = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST"
        },
        "nifty": {
            "spot": round(last_close, 2),
