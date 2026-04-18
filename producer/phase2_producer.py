import json
from datetime import datetime, time
import pandas as pd
import pytz

IST = pytz.timezone("Asia/Kolkata")

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def load_ohlcv():
    """
    Load OHLCV data.
    Expected columns:
    ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    Timestamp must be timezone-aware (IST).
    """
    # Placeholder: replace with your actual data source
    return pd.read_csv(
        "data/ohlcv_5m.csv",
        parse_dates=["timestamp"]
    )


def get_previous_completed_week(df):
    df["week"] = df["timestamp"].dt.to_period("W")
    current_week = datetime.now(IST).date().isocalendar()[1]

    df["week_number"] = df["timestamp"].dt.isocalendar().week
    completed_weeks = df[df["week_number"] < current_week]

    last_week_number = completed_weeks["week_number"].max()
    return completed_weeks[completed_weeks["week_number"] == last_week_number]


def compute_weekly_levels(df):
    return {
        "previous_week_high": float(df["high"].max()),
        "previous_week_low": float(df["low"].min()),
        "week_start": df["timestamp"].min().date().isoformat(),
        "week_end": df["timestamp"].max().date().isoformat()
    }


def compute_session_levels(df):
    today = datetime.now(IST).date()

    session_start = datetime.combine(today, time(9, 15), IST)
    session_end = datetime.combine(today, time(15, 30), IST)

    session_df = df[
        (df["timestamp"] >= session_start) &
        (df["timestamp"] <= session_end)
    ]

    # Resample to 15-minute candles (candle-close based)
    session_15m = (
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
        .reset_index()
    )

    return {
        "high": float(session_15m["high"].max()) if not session_15m.empty else None,
        "low": float(session_15m["low"].min()) if not session_15m.empty else None,
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }


# ------------------------------------------------------------------------------
# Main Producer
# ------------------------------------------------------------------------------

def run_phase2_producer():
    df = load_ohlcv()
    df["timestamp"] = df["timestamp"].dt.tz_localize(IST)

    # Weekly Levels
    prev_week_df = get_previous_completed_week(df)
    weekly_levels = compute_weekly_levels(prev_week_df)

    # Session Levels
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

    with open("snapshots/market_phase2.json", "w") as f:
        json.dump(snapshot, f, indent=2)


if __name__ == "__main__":
    run_phase2_producer()
