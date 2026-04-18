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

def fetch_intraday_5m(days=5):
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
# TREND ARCHITECT @ 13:00
# ==============================

def compute_trend_architect_1300(day_df, previous):
    current_time = now_ist().time()

    # Freeze after 13:00
    if current_time > time(13, 0) and "trend_architect_1300" in previous:
        return previous["trend_architect_1300"]

    win = day_df[
        (day_df.index.time >= time(9, 30)) &
        (day_df.index.time <= min(current_time, time(13, 0)))
    ]

    if len(win) < 6:
        return previous.get("trend_architect_1300")

    win = win.copy()
    win["body"] = (win["close"] - win["open"]).abs()

    major = win.loc[win["body"].idxmax()]
    major_color = "GREEN" if major["close"] > major["open"] else "RED"

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

    open_0930 = win.iloc[0]["open"]
    close_latest = win.iloc[-1]["close"]
    dist = round(close_latest - open_0930, 2)

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
# MOMENTUM EVENTS (5m) + SEVERITY
# ==============================

def detect_momentum_events_5m(df_5m):
    events = []

    if len(df_5m) < 40:
        return events

    recent = df_5m.tail(40)

    avg_body = (recent["close"] - recent["open"]).abs().mean()
    avg_range = (recent["high"] - recent["low"]).mean()
    avg_vol = recent["volume"].mean()

    last = recent.iloc[-1]
    prev = recent.iloc[-2]

    body = abs(last["close"] - last["open"])
    rng = last["high"] - last["low"]
    wick_ratio = 1 - (body / rng if rng > 0 else 1)

    ts = last.name.isoformat()

    # HIGH severity
    if body >= 1.4 * avg_body and body >= 0.65 * rng:
        if last["close"] > last["open"]:
            events.append(("BullishImpulse", "Strong bullish 5m impulse candle", "High", ts))
        else:
            events.append(("BearishImpulse", "Strong bearish 5m impulse candle", "High", ts))

    if last["volume"] >= 1.7 * avg_vol and rng >= avg_range:
        events.append(("HighVolumeBreakout", "High‑volume breakout detected (5m)", "High", ts))

    if rng >= avg_range and wick_ratio >= 0.6:
        events.append(("FailedBreakout", "Failed breakout – momentum rejection", "High", ts))

    # MEDIUM severity
    if body >= avg_body and wick_ratio >= 0.6:
        events.append(("Exhaustion", "Momentum exhaustion candle (5m)", "Medium", ts))

    if rng >= 1.5 * avg_range and abs(prev["close"] - last["close"]) < 0.3 * rng:
        events.append(("NoFollowThrough", "Expansion without follow‑through", "Medium", ts))

    # LOW severity
    if last["close"] > last["open"] and prev["close"] > prev["open"] and last["close"] > prev["high"]:
        events.append(("BullishContinuation", "Bullish momentum continuation", "Low", ts))

    if last["close"] < last["open"] and prev["close"] < prev["open"] and last["close"] < prev["low"]:
        events.append(("BearishContinuation", "Bearish momentum continuation", "Low", ts))

    return events

# ==============================
# MAIN
# ==============================

def run_phase2():
    previous = {}
    if os.path.exists(SNAPSHOT_PATH):
        with open(SNAPSHOT_PATH, "r") as f:
            previous = json.load(f)

    df5 = fetch_intraday_5m(days=5)

    # Latest trading day
    day_groups = df5.groupby(df5.index.date)
    valid_days = [d for d, g in day_groups if len(g) >= 10]
    if not valid_days:
        return

    last_day = valid_days[-1]
    day_df = day_groups.get_group(last_day)

    # Trend Architect
    ta_1300 = compute_trend_architect_1300(day_df, previous)

    # Momentum Events (intraday)
    now = now_ist()
    prev_events = previous.get("momentum_events", [])

    # Reset next day at 08:40 IST
    if now.time() >= time(8, 40):
        prev_events = []

    raw_events = detect_momentum_events_5m(day_df)

    for etype, desc, severity, ts in raw_events:
        if not any(e["timestamp"] == ts and e["type"] == etype for e in prev_events):
            prev_events.append({
                "type": etype,
                "timeframe": "5m",
                "description": desc,
                "severity": severity,
                "timestamp": ts
            })

    momentum_events = prev_events[-5:]

    snapshot = previous.copy()
    snapshot.update({
        "phase": 2,
        "symbol": "NIFTY",
        "trend_architect_1300": ta_1300,
        "momentum_events": momentum_events,
        "computed_at": now.isoformat()
    })

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    run_phase2()
