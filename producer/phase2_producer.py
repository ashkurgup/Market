import json
import os
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

def run_phase2_producer():
    print(">>> Phase‑2 producer started (CI safe)")

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",

        "session": {
            "start": "09:15",
            "end": "15:30",
            "timezone": "IST"
        },

        "weekly_levels": {
            "previous_week_high": 22500,
            "previous_week_low": 22100,
            "week_start": "2026-04-06",
            "week_end": "2026-04-10"
        },

        "key_levels": {
            "nearest_resistance": None,
            "nearest_support": None
        },

        "session_levels": {
            "high": 22480,
            "low": 22310,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        },

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

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(">>> Phase‑2 snapshot written successfully")

if __name__ == "__main__":
    run_phase2_producer()
