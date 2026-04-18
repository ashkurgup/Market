import json
import os
from datetime import datetime, time
import pytz
import pandas as pd

IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASE1_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase1.json")
PHASE2_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

def load_phase1_candles():
    """
    Expected Phase‑1 candle format:
    candles: [
      { "timestamp": "...", "open": , "high": , "low": , "close": , "volume":  }
    ]
    """
    with open(PHASE1_PATH, "r") as f:
        phase1 = json.load(f)

    df = pd.DataFrame(phase1["candles"])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert(IST)
    return df

def compute_previous_week_levels(df):
    df["week"] = df["timestamp"].dt.to_period("W")
    today = datetime.now(IST).date()

    completed = df[df["timestamp"].dt.date < today]
    last_week = completed["week"].max()
    week_df = completed[completed["week"] == last_week]

    return {
        "previous_week_high": float(week_df["high"].max()),
        "previous_week_low": float(week_df["low"].min()),
        "week_start": week_df["timestamp"].min().date().isoformat(),
        "week_end": week_df["timestamp"].max().date().isoformat()
    }

def compute_session_levels(df):
    today = datetime.now(IST).date()
    session_start = datetime.combine(today, time(9, 15), IST)
    session_end = datetime.combine(today, time(15, 30), IST)

    session_df = df[
        (df["timestamp"] >= session_start) &
        (df["timestamp"] <= session_end)
    ]

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

    return {
        "high": float(candles_15m["high"].max()),
        "low": float(candles_15m["low"].min()),
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }

def run_phase2_producer():
    df = load_phase1_candles()

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",

        "session": {
            "start": "09:15",
            "end": "15:30",
            "timezone": "IST"
        },

        "weekly_levels": compute_previous_week_levels(df),
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

    with open(PHASE2_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    run_phase2_producer()
