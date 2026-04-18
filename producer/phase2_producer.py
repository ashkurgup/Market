import json
import os
from datetime import datetime, time
import pytz
import pandas as pd
import yfinance as yf

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

SYMBOL = "^NSEI"          # NIFTY 50
INTERVAL = "5m"
LOOKBACK_DAYS = 21        # enough for previous completed week

IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

# --------------------------------------------------
# FETCH DATA FROM YAHOO
# --------------------------------------------------

def fetch_ohlcv():
    print(">>> Fetching OHLC from Yahoo Finance")

    df = yf.download(
        SYMBOL,
        period=f"{LOOKBACK_DAYS}d",
        interval=INTERVAL,
        progress=False
    )

    if df.empty:
        raise RuntimeError("Yahoo Finance returned no data")

    df = df.reset_index()
    df.rename(columns={
        "Datetime": "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert(IST)
    return df

# --------------------------------------------------
# WEEKLY LEVELS (PREVIOUS COMPLETED WEEK ONLY)
# --------------------------------------------------

def compute_weekly_levels(df):
    df["week"] = df["timestamp"].dt.to_period("W")

    current_week = datetime.now(IST).isocalendar()[1]
    completed = df[df["timestamp"].dt.isocalendar().week < current_week]

    if completed.empty:
        return {
            "previous_week_high": None,
            "previous_week_low": None,
            "week_start": None,
            "week_end": None
        }

    last_week = completed["week"].max()
    week_df = completed[completed["week"] == last_week]

    if week_df.empty:
        return {
            "previous_week_high": None,
            "previous_week_low": None,
            "week_start": None,
            "week_end": None
        }

    return {
        "previous_week_high": float(week_df["high"].max()),
        "previous_week_low": float(week_df["low"].min()),
        "week_start": week_df["timestamp"].min().date().isoformat(),
        "week_end": week_df["timestamp"].max().date().isoformat()
    }

# --------------------------------------------------
# SESSION LEVELS (15‑MIN, CLOSE‑BASED)
# --------------------------------------------------

def compute_session_levels(df):
    today = datetime.now(IST).date()

    session_start = datetime.combine(today, time(9, 15), IST)
    session_end = datetime.combine(today, time(15, 30), IST)

    session_df = df[
        (df["timestamp"] >= session_start) &
        (df["timestamp"] <= session_end)
    ]

    if session_df.empty:
        return {
            "high": None,
            "low": None,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        }

    candles_15m = (
        session_df
        .set_index("timestamp")
        .resample("15T", closed="right", label="right")
        .agg({
            "high": "max",
            "low": "min"
        })
        .dropna()
    )

    if candles_15m.empty:
        return {
            "high": None,
            "low": None,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        }

    return {
        "high": float(candles_15m["high"].max()),
        "low": float(candles_15m["low"].min()),
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }

# --------------------------------------------------
# MAIN PRODUCER
# --------------------------------------------------

def run_phase2_producer():
    print(">>> Phase‑2 producer started (Yahoo Finance)")

    df = fetch_ohlcv()

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",

        "session": {
            "start": "09:15",
            "end": "15:30",
            "timezone": "IST"
        },

        "weekly_levels": compute_weekly_levels(df),

        "key_levels": {
            "nearest_resistance": None,
            "nearest_support": None
        },

        "session_levels": compute_session_levels(df),

        "structure_events": [],
        "momentum_events": [],

        "global_indices": {
            "time_window_minutes": 30,
            "indices": []
        },

        "bias": {
            "day": None,
            "h4": None,
            "h1": None
        },

        "computed_at": datetime.now(IST).isoformat()
    }

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(">>> Phase‑2 snapshot written successfully")

if __name__ == "__main__":
    run_phase2_producer()
