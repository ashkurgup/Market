import json
import os
from datetime import datetime, time
import pandas as pd
import pytz

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

# -------------------------------------------------------------------
# DATA LOADER (same pattern as phase1)
# -------------------------------------------------------------------

def load_ohlcv():
    """
    Expected columns:
    timestamp, open, high, low, close, volume
    Timezone naive or aware; will be localized to IST.
    """
    df = pd.read_csv(
        os.path.join(BASE_DIR, "data", "ohlcv_5m.csv"),
        parse_dates=["timestamp"]
    )
    df["timestamp"] = df["timestamp"].dt.tz_localize(IST, nonexistent="shift_forward")
    return df

# -------------------------------------------------------------------
# WEEKLY LEVELS
# -------------------------------------------------------------------

def compute_previous_week_levels(df):
    today = datetime.now(IST).date()
    df["week"] = df["timestamp"].dt.to_period("W")

    completed_weeks = df[df["timestamp"].dt.date < today]
    last_week = completed_weeks["week"].max()

    week_df = completed_weeks[completed_weeks["week"] == last_week]

    if week_df.empty:
        return dict.fromkeys(
            ["previous_week_high", "previous_week_low", "week_start", "week_end"]
        )

    return {
        "previous_week_high": float(week_df["high"].max()),
        "previous_week_low": float(week_df["low"].min()),
        "week_start": week_df["timestamp"].min().date().isoformat(),
        "week_end": week_df["timestamp"].max().date().isoformat()
    }

# -------------------------------------------------------------------
# SESSION LEVELS (15‑MIN, CLOSE ONLY)
# -------------------------------------------------------------------

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
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        })
        .dropna()
    )

    return {
        "high": float(candles_15m["high"].max()),
        "low": float(candles_15m["low"].min()),
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }

# -------------------------------------------------------------------
# MAIN PRODUCER
# -------------------------------------------------------------------

def run_phase2_producer():
    print(">>> Phase‑2 producer started")

    df = load_ohlcv()

    weekly_levels = compute_previous_week_levels(df)
    session_levels = compute_session_levels(df)

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",

        "session": {
            "start": "09:15",
            "end": "15:30",
            "timezone": "IST"
        },

        "weekly_levels": weekly_levels,

        "key_levels": {
            "nearest_resistance": None,
            "nearest_support": None
        },

        "session_levels": session_levels,

        "structure_events": [],
        "momentum_events": [],

        "global_indices": {
            "time_window_minutes": 30,
            "indices": [
                {"name": "Dow Futures", "percent_change": None},
                {"name": "Nikkei", "percent_change": None},
                {"name": "Hang Seng", "percent_change": None},
                {"name": "DAX", "percent_change": None}
            ]
        },

        "bias": {
            "day": None,
            "h4": None,
            "h1": None
        },

        "computed_at": datetime.now(IST).isoformat()
    }

    print(f">>> Writing snapshot → {SNAPSHOT_PATH}")

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(">>> Phase‑2 snapshot written successfully")

if __name__ == "__main__":
    run_phase2_producer()
