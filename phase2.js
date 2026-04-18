import json
import os
import pytz
import pandas as pd
import yfinance as yf
from datetime import datetime, time

# ==============================
# CONFIG
# ==============================

SYMBOL = "^NSEI"
IST = pytz.timezone("Asia/Kolkata")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

# ==============================
# HELPERS
# ==============================

def now_ist():
    return datetime.now(IST)

def fetch_intraday_5m(days=7):
    df = yf.download(
        SYMBOL,
        interval="5m",
        period=f"{days}d",
        progress=False
    )

    if df.empty:
        raise RuntimeError("No intraday data")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(IST)
    else:
        df.index = df.index.tz_convert(IST)

    return df.sort_index()

# ==============================
# PHASE‑2 TREND ARCHITECT @ 13:00
# ==============================

def compute_trend_architect_1300(day_df, previous_snapshot):
    """
    Window: 09:30 → ≤13:00
    Refresh: until 13:00
    Freeze: after 13:00
    Logic: IDENTICAL to Phase‑1
    """

    current_time = now_ist().time()

    # After 13:00 → freeze
    if current_time > time(13, 0) and "trend_architect_1300" in previous_snapshot:
        return previous_snapshot["trend_architect_1300"]

    # Active computation window
    win = day_df[
        (day_df.index.time >= time(9, 30)) &
        (day_df.index.time <= min(current_time, time(13, 0)))
    ]

    if len(win) < 6:
        return None

    win = win.copy()
    win["body"] = (win["close"] - win["open"]).abs()

    # ----- MAJOR CANDLE (same logic)
    major = win.loc[win["body"].idxmax()]
    major_color = "GREEN" if major["close"] > major["open"] else "RED"

    # ----- OVERLAPS + SMALL CANDLES (same logic)
    overlaps = 0
    small_c = 0

    for i in range(1, len(win)):
        p = win.iloc[i - 1]
        c = win.iloc[i]

        bp = sorted([p["open"], p["close"]])
        bc = sorted([c["open"], c["close"]])
        overlap = max(0, min(bp[1], bc[1]) - max(bp[0], bc[0]))
        body = bc[1] - bc[0]

        if body > 0 and overlap >= 0.8 * body:
            overlaps += 1
        if (c["high"] - c["low"]) < 25:
            small_c += 1

    # ----- DISTANCE (same logic)
    open_0930 = win.iloc[0]["open"]
    close_latest = win.iloc[-1]["close"]
    dist = round(close_latest - open_0930, 2)

    # ----- MARKET CHARACTER (same rules)
    if overlaps <= 2 and small_c <= 3:
        mc = "Steady move with buyer acceptance"
    elif overlaps >= 4 or small_c >= 5:
        mc = "Upward movement with frequent overlap — be cautious"
    else:
        mc = "Directional bias intact, but higher risk of deep pullback"

    return {
        "window": "09:30 → 13:00",
        "freeze_rule": "Frozen after 13:00",
        "major_candle": {
            "range": round(major["body"], 2),
            "type": "MARUBOZU",
            "color": major_color,
            "time": major.name.strftime("%H:%M")
        },
        "next_candle": {
            "relation": "SUPPORTING" if major_color == "GREEN" else "OPPOSING"
        },
        "distance_travelled": {
            "points": dist,
            "direction": "UP" if dist > 0 else "DOWN",
            "overlaps": overlaps,
            "small_candles": small_c
        },
        "market_character": mc,
        "computed_at": now_ist().isoformat()
    }

# ==============================
# MAIN PHASE‑2 PRODUCER
# ==============================

def run_phase2():
    # Load previous Phase‑2 snapshot (for freeze support)
    previous = {}
    if os.path.exists(SNAPSHOT_PATH):
        with open(SNAPSHOT_PATH, "r") as f:
            previous = json.load(f)

    df = fetch_intraday_5m(days=5)

    # Detect latest trading day
    day_groups = df.groupby(df.index.date)
    valid_days = [d for d, g in day_groups if len(g) >= 10]
    if not valid_days:
        return

    last_day = valid_days[-1]
    day_df = day_groups.get_group(last_day)

    # Compute Trend Architect @ 13:00
    ta_1300 = compute_trend_architect_1300(day_df, previous)

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",
        "trend_architect_1300": ta_1300,
        "computed_at": now_ist().isoformat()
    }

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    run_phase2()
