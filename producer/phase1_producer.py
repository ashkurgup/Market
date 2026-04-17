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

def to_time(ts):
    return ts.astimezone(IST).time()

def safe_float(v, r=2):
    return round(float(v), r)

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
    df = df.tz_localize("UTC").tz_convert(IST)
    df.columns = [c.lower() for c in df.columns]
    return df

df = fetch_5m_data()
if df.empty:
    raise RuntimeError("No data fetched")

# =========================
# Time Windows
# =========================
START = time(9, 30)
END_FREEZE = time(11, 5)
MAJOR_END = time(11, 0)

df_0930 = df[df.index.map(to_time) >= START]
df_till_freeze = df_0930[df_0930.index.map(to_time) <= END_FREEZE]

# =========================
# VOLATILITY / ATR (15m, 14)
# =========================
atr_val = df_till_freeze["high"].rolling(3).max() - df_till_freeze["low"].rolling(3).min()
atr = safe_float(atr_val.mean())

sample_status = (
    "Enough Sample" if now_ist().time() >= time(13, 0) else "Less Sample"
)

# ---- Choppiness (derived, informational) ----
if atr > 40:
    chop_state = "High"
    chop_msg = "Expect large pullbacks"
elif atr > 20:
    chop_state = "Moderate"
    chop_msg = "Expansion exists but strong evidence needed"
else:
    chop_state = "Low"
    chop_msg = "Continuation friendly environment"

# =========================
# TREND ARCHITECT (FREEZES @ 11:05)
# =========================
trend_architect = {}

if now_ist().time() >= END_FREEZE:
    # ---- Gap Behavior ----
    open_price = df.iloc[0]["open"]
    prev_close = open_price  # already frozen elsewhere
    status = "Closed" if df_till_freeze["low"].min() <= prev_close <= df_till_freeze["high"].max() else "Open"

    trend_architect["gap_behavior"] = {
        "status": f"{status} by 11:05",
        "frozen_at": "11:05 IST"
    }

    # ---- Major Candle ----
    window = df_0930[df_0930.index.map(to_time) <= MAJOR_END].copy()
    window["range"] = window["high"] - window["low"]
    major = window.loc[window["range"].idxmax()]

    major_color = "GREEN" if major["close"] > major["open"] else "RED"
    major_range = safe_float(major["range"])
    major_time = major.name.strftime("%H:%M")

    trend_architect["major_candle"] = {
        "range": major_range,
        "type": "MARUBOZU",
        "color": major_color,
        "time": major_time
    }

    # ---- Next Candle Relation ----
    after_major = window[window.index > major.name]
    if after_major.empty:
        relation = "NA"
    else:
        nxt = after_major.iloc[0]
        relation = (
            "SUPPORTING" if (nxt["close"] - major["close"]) * (major["close"] - major["open"]) > 0
            else "OPPOSING"
        )

    trend_architect["next_candle"] = {
        "relation": relation,
        "color": "GREEN" if relation == "SUPPORTING" else "RED"
    }

    # ---- Distance & Overlaps ----
    total_distance = safe_float(
        df_till_freeze.iloc[-1]["close"] - df_0930.iloc[0]["open"]
    )

    overlaps = 0
    for i in range(1, len(df_till_freeze)):
        prev = df_till_freeze.iloc[i - 1]
        cur = df_till_freeze.iloc[i]
        body_prev = sorted([prev["open"], prev["close"]])
        body_cur = sorted([cur["open"], cur["close"]])
        overlap = max(0, min(body_prev[1], body_cur[1]) - max(body_prev[0], body_cur[0]))
        if overlap >= 0.8 * (body_cur[1] - body_cur[0]):
            overlaps += 1

    trend_architect["distance_travelled"] = {
        "points": total_distance,
        "direction": "UP" if total_distance > 0 else "DOWN",
        "overlaps": overlaps
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
# FINAL OUTPUT
# =========================
out = {
    "meta": {
        "date": now_ist().strftime("%Y-%m-%d"),
        "last_updated": now_ist().strftime("%H:%M:%S"),
        "timezone": "IST"
    },
    "volatility": {
        "atr": atr,
        "sample_status": sample_status
    },
    "choppiness": {
        "state": chop_state,
        "message": chop_msg
    },
    "trend_architect": trend_architect
}

with open("snapshots/market_phase1.json", "r") as f:
    existing = json.load(f)
existing.update(out)

with open("snapshots/market_phase1.json", "w") as f:
    json.dump(existing, f, indent=2)
