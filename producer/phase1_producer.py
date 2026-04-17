import json
from datetime import datetime, time
import pytz
import pandas as pd
import yfinance as yf

IST = pytz.timezone("Asia/Kolkata")

# =========================
# Helpers
# =========================
def now_ist():
    return datetime.now(IST)

def safe_float(v, r=2):
    return round(float(v), r)

def ensure_ist_index(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(IST)
    else:
        df.index = df.index.tz_convert(IST)
    return df

def normalize_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]
    return df

# =========================
# Fetch Data
# =========================
def fetch_5m_data(symbol="^NSEI"):
    df = yf.download(
        symbol,
        interval="5m",
        period="1d",
        progress=False
    )
    if df.empty:
        return df
    df = ensure_ist_index(df)
    df = normalize_columns(df)
    return df.sort_index()

df = fetch_5m_data()
if df.empty:
    raise RuntimeError("No data fetched")

# =========================
# Time Windows
# =========================
START = time(9, 30)
END = time(11, 0)
FREEZE = time(11, 5)

df_window = df[(df.index.time >= START) & (df.index.time <= END)]

# =========================
# TREND ARCHITECT (FREEZES)
# =========================
trend_architect = {}

if now_ist().time() >= FREEZE and not df_window.empty:
    # ---- Gap Behavior (unchanged) ----
    trend_architect["gap_behavior"] = {
        "status": "Closed by 11:05",
        "frozen_at": "11:05 IST"
    }

    # ---- Major Candle (BODY) ----
    df_window["body"] = (df_window["close"] - df_window["open"]).abs()
    major = df_window.loc[df_window["body"].idxmax()]

    major_color = "GREEN" if major["close"] > major["open"] else "RED"

    trend_architect["major_candle"] = {
        "range": safe_float(major["body"]),
        "type": "MARUBOZU",
        "color": major_color,
        "time": major.name.strftime("%H:%M")
    }

    # ---- Next Candle Relation ----
    after_major = df_window[df_window.index > major.name]
    if after_major.empty:
        relation = "NA"
    else:
        nxt = after_major.iloc[0]
        relation = (
            "SUPPORTING"
            if (nxt["close"] - nxt["open"]) * (major["close"] - major["open"]) > 0
            else "OPPOSING"
        )

    trend_architect["next_candle"] = {
        "relation": relation
    }

    # ---- Total Distance (09:30 → 11:00) ----
    open_0930 = df_window.iloc[0]["open"]
    close_1100 = df_window[df_window.index.time == END]["close"].iloc[0]

    total_distance = safe_float(close_1100 - open_0930)

    # ---- Overlaps + Small Candles ----
    overlaps = 0
    small_candles = 0

    for i in range(1, len(df_window)):
        prev = df_window.iloc[i - 1]
        cur = df_window.iloc[i]

        # Body overlap
        bp = sorted([prev["open"], prev["close"]])
        bc = sorted([cur["open"], cur["close"]])

        overlap = max(0, min(bp[1], bc[1]) - max(bp[0], bc[0]))
        body_size = bc[1] - bc[0]

        if body_size > 0 and overlap >= 0.8 * body_size:
            overlaps += 1

        # Small candle (high-low)
        if (cur["high"] - cur["low"]) < 25:
            small_candles += 1

    trend_architect["distance_travelled"] = {
        "points": total_distance,
        "direction": "UP" if total_distance > 0 else "DOWN",
        "overlaps": overlaps,
        "small_candles": small_candles
    }

    # ---- Market Character ----
    if overlaps <= 2 and major_color == "GREEN":
        mc = "Steady move with buyer acceptance"
    elif overlaps >= 4:
        mc = "Upward movement with frequent overlap — be cautious"
    else:
        mc = "Directional bias intact, but higher risk of deep pullback"

    trend_architect["market_character"] = mc

# =========================
# WRITE SNAPSHOT (MERGE SAFE)
# =========================
with open("snapshots/market_phase1.json", "r") as f:
    existing = json.load(f)

existing["trend_architect"] = trend_architect

with open("snapshots/market_phase1.json", "w") as f:
    json.dump(existing, f, indent=2)
