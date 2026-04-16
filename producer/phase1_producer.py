import json
import os
from datetime import datetime, time
import pytz

IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase1.json")

# -------------------------------
# NSE HOLIDAYS (MAINTAIN YEARLY)
# -------------------------------
NSE_HOLIDAYS = {
    "2026-01-26",  # Republic Day
    "2026-03-07",  # Holi
    "2026-03-30",  # Ram Navami
    "2026-04-14",  # Dr Ambedkar Jayanti
    "2026-05-01",  # Maharashtra Day
    "2026-08-15",  # Independence Day
    "2026-10-02",  # Gandhi Jayanti
    "2026-11-12",  # Diwali
}

# -------------------------------
# TIME HELPERS
# -------------------------------
def now_ist():
    return datetime.now(IST)

def is_weekend(dt):
    return dt.weekday() >= 5  # Sat / Sun

def is_holiday(dt):
    return dt.strftime("%Y-%m-%d") in NSE_HOLIDAYS

def market_hours_open(dt):
    return time(9, 0) <= dt.time() <= time(15, 35)

def reset_window(dt):
    """Reset sensitive blocks to Data Awaited at 08:40"""
    return dt.time() < time(8, 40)

# -------------------------------
# SAFE SNAPSHOT WRITER
# -------------------------------
def write_snapshot(snapshot):
    tmp_path = SNAPSHOT_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(snapshot, f, indent=2)
    os.replace(tmp_path, SNAPSHOT_PATH)

# -------------------------------
# BASE SNAPSHOT TEMPLATE
# -------------------------------
def base_snapshot(status):
    ts = now_ist()
    return {
        "meta": {
            "date": ts.strftime("%Y-%m-%d"),
            "last_updated": ts.strftime("%H:%M:%S"),
            "timezone": "IST",
            "session_status": status,
        },
        "nifty": {},
        "global_markets": {},
        "volatility": {},
        "market_open": {},
        "trend_architect": {},
        "vwap": {},
        "previous_day": {},
        "institutional_flows": {}
    }

# -------------------------------
# RESET BLOCKS (08:40 IST)
# -------------------------------
def reset_sensitive_blocks(snapshot):
    snapshot["market_open"] = {
        "gap_status": "DATA_AWAITED",
        "open_candle": "DATA_AWAITED"
    }
    snapshot["trend_architect"] = {
        "gap_behavior": "DATA_AWAITED",
        "major_candle": "DATA_AWAITED",
        "next_candle_relation": "DATA_AWAITED",
        "velocity": "DATA_AWAITED"
    }
    return snapshot

# -------------------------------
# MAIN PRODUCER
# -------------------------------
def run():
    ts = now_ist()

    # Weekend / Holiday Safety
    if is_weekend(ts) or is_holiday(ts):
        snapshot = base_snapshot("MARKET_CLOSED")
        write_snapshot(snapshot)
        return

    snapshot = base_snapshot("OPEN" if market_hours_open(ts) else "CLOSED")

    # Reset logic at 08:40
    if reset_window(ts):
        snapshot = reset_sensitive_blocks(snapshot)
        write_snapshot(snapshot)
        return

    # ------------------------------------------------
    # NOTE:
    # Actual data fetch & logic enters here.
    # For Phase 1 foundation, we publish structure.
    # ------------------------------------------------

    snapshot["institutional_flows"] = {
        "fii_today": None,
        "dii_today": None,
        "fii_5day": None,
        "status": "AWAITING_DATA",
        "last_checked": ts.strftime("%H:%M:%S")
    }

    write_snapshot(snapshot)


if __name__ == "__main__":
    run()
