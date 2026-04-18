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

def fetch_intraday_5m(symbol, days=5):
    df = yf.download(symbol, interval="5m", period=f"{days}d", progress=False)
    if df.empty:
        return None

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
    now = now_ist().time()

    if now > time(13, 0) and "trend_architect_1300" in previous:
        return previous["trend_architect_1300"]

    win = day_df[
        (day_df.index.time >= time(9, 30)) &
        (day_df.index.time <= min(now, time(13, 0)))
    ]

    if len(win) < 6:
        return previous.get("trend_architect_1300")

    win = win.copy()
    win["body"] = (win["close"] - win["open"]).abs()

    major = win.loc[win["body"].idxmax()]
    major_color = "GREEN" if major["close"] > major["open"] else "RED"

    overlaps, small_c = 0, 0
    for i in range(1, len(win)):
        p, c = win.iloc[i - 1], win.iloc[i]
        bp, bc = sorted([p["open"], p["close"]]), sorted([c["open"], c["close"]])
        overlap = max(0, min(bp[1], bc[1]) - max(bp[0], bc[0]))
        body = bc[1] - bc[0]
        if body > 0 and overlap >= 0.8 * body:
            overlaps += 1
        if (c["high"] - c["low"]) < 25:
            small_c += 1

    dist = round(win.iloc[-1]["close"] - win.iloc[0]["open"], 2)

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
        "distance_travelled": {
            "points": dist,
            "overlaps": overlaps,
            "small_candles": small_c
        },
        "market_character": mc,
        "computed_at": now_ist().isoformat()
    }

# ==============================
# MOMENTUM EVENTS (5m)
# ==============================

def detect_momentum_events_5m(df):
    events = []
    if df is None or len(df) < 40:
        return events

    recent = df.tail(40)
    avg_body = (recent["close"] - recent["open"]).abs().mean()
    avg_range = (recent["high"] - recent["low"]).mean()
    avg_vol = recent["volume"].mean()

    last, prev = recent.iloc[-1], recent.iloc[-2]
    body = abs(last["close"] - last["open"])
    rng = last["high"] - last["low"]
    wick_ratio = 1 - (body / rng if rng > 0 else 1)

    ts = last.name.isoformat()

    if body >= 1.4 * avg_body and body >= 0.65 * rng:
        events.append({
            "description": "Strong bullish 5m impulse candle" if last["close"] > last["open"]
                           else "Strong bearish 5m impulse candle",
            "severity": "High",
            "timeframe": "5m",
            "timestamp": ts
        })

    if last["volume"] >= 1.7 * avg_vol and rng >= avg_range:
        events.append({
            "description": "High‑volume breakout detected (5m)",
            "severity": "High",
            "timeframe": "5m",
            "timestamp": ts
        })

    if body >= avg_body and wick_ratio >= 0.6:
        events.append({
            "description": "Momentum exhaustion candle (5m)",
            "severity": "Medium",
            "timeframe": "5m",
            "timestamp": ts
        })

    return events

# ==============================
# GLOBAL INDICES (30‑min %)
# ==============================

def compute_global_indices_30m():
    indices = {
        "Dow Futures": "YM=F",
        "DAX": "^GDAXI",
        "Nikkei": "^N225",
        "Hang Seng": "^HSI"
    }

    out, now = [], now_ist()

    for name, symbol in indices.items():
        df = fetch_intraday_5m(symbol, days=2)
        if df is None or len(df) < 7:
            continue

        pct = round(
            ((df.iloc[-1]["close"] - df.iloc[-7]["close"]) / df.iloc[-7]["close"]) * 100,
            2
        )

        is_open = (now - df.index[-1]).total_seconds() <= 2400

        out.append({
            "name": name,
            "pct_change_30m": pct,
            "is_open": is_open
        })

    return out

# ==============================
# PRE‑MARKET GLOBAL BIAS (0–10)
# ==============================

def compute_premarket_global_bias(global_indices):
    weights = {
        "Dow Futures": 0.40,
        "DAX": 0.25,
        "Nikkei": 0.20,
        "Hang Seng": 0.15
    }

    raw = 0.0
    for g in global_indices:
        pct = g["pct_change_30m"]
        direction = 1 if pct > 0.20 else -1 if pct < -0.20 else 0
        open_wt = 1.0 if g["is_open"] else 0.5
        raw += direction * weights[g["name"]] * open_wt

    raw = max(-1, min(1, raw))
    return round((raw + 1) * 5)

# ==============================
# MAIN
# ==============================

def run_phase2():
    previous = {}
    if os.path.exists(SNAPSHOT_PATH):
        with open(SNAPSHOT_PATH, "r") as f:
            previous = json.load(f)

    df = fetch_intraday_5m(SYMBOL, days=5)
    if df is None:
        return

    # ✅ FIXED: get latest trading day correctly
    day = df.index.date.max()
    day_df = df[df.index.date == day]

    trend_architect = compute_trend_architect_1300(day_df, previous)
    momentum_events = detect_momentum_events_5m(day_df)
    global_indices = compute_global_indices_30m()
    premarket_bias = compute_premarket_global_bias(global_indices)

    snapshot = previous.copy()
    snapshot.update({
        "phase": 2,
        "symbol": "NIFTY",
        "trend_architect_1300": trend_architect,
        "momentum_events": momentum_events,
        "global_indices": global_indices,
        "premarket_global_bias": premarket_bias,
        "computed_at": now_ist().isoformat()
    })

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    run_phase2()
