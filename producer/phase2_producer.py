import json
import os
from datetime import datetime, time
import pandas as pd
import pytz

IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "ohlcv_5m.csv")
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

# ------------------------------------------------
# Load OHLCV data (same source philosophy as Phase‑1)
# ------------------------------------------------

def load_ohlcv():
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df["timestamp"] = df["timestamp"].dt.tz_localize(IST)
    return df

# ------------------------------------------------
# Weekly Levels (previous completed week)
# ------------------------------------------------

def compute_weekly_levels(df):
    df["week"] = df["timestamp"].dt.to_period("W")

    current_week = datetime.now(IST).date().isocalendar().week
    completed = df[df["timestamp"].dt.isocalendar().week < current_week]

    last_week = completed["week"].max()
    week_df = completed[completed["week"] == last_week]

    return {
        "previous_week_high": float(week_df["high"].max()),
        "previous_week_low": float(week_df["low"].min()),
        "week_start": week_df["timestamp"].min().date().isoformat(),
        "week_end": week_df["timestamp"].max().date().isoformat()
    }

# ------------------------------------------------
# Session Levels (15m, candle‑close only)
# ------------------------------------------------

def compute_session_levels(df):
    today = datetime.now(IST).date()

    start = datetime.combine(today, time(9, 15), IST)
    end = datetime.combine(today, time(15, 30), IST)

    session_df = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)]

    candles_15m = (
        session_df
        .set_index("timestamp")
        .resample("15T", closed="right", label="right")
        .agg({"high": "max", "low": "min"})
        .dropna()
    )

    return {
        "high": float(candles_15m["high"].max()) if not candles_15m.empty else None,
        "low": float(candles_15m["low"].min()) if not candles_15m.empty else None,
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }

# ------------------------------------------------
# Main Producer
# ------------------------------------------------

def run_phase2_producer():
    print(">>> Phase‑2 producer started (real data)")

    df = load_ohlcv()

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
