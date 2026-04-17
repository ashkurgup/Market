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
    """
    yfinance may return MultiIndex columns.
    Flatten safely and lowercase.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]
    return df

# =========================
# Fetch 5m Data
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
    return df

df = fetch_5m_data()
if df.empty:
    raise RuntimeError("No data fetched")

df = df.sort_index()

# =========================
# Time Windows
# =========================
START = time(9, 30)
FREEZE = time(11, 5)
MAJOR_END = time(11, 0)

df_0930 = df[df.index.time >= START]
df_freeze = df_0930[df_0930.index.time <= FREEZE]

# =========================
# VOLATILITY (ATR)
# =========================
atr_series = (
    df_freeze["high"].rolling(3).max()
    - df_freeze["low"].rolling(3).min()
)
atr = safe_float(atr_series.mean())

sample_status = (
    "Enough Sample" if now_ist().time() >= time(13, 0) else "Less Sample"
)

# ✅ Choppiness (final wording)
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

if now_ist().time() >= FREEZE and not df_freeze.empty:
    # ---- Gap Behavior ----
    trend_architect["gap_behavior"] = {
        "status": "Closed by 11:05",
        "frozen_at": "11:05 IST"
    }

    # ---- Major Candle ----
    window = df_0930[df_0930.index.time <= MAJOR_END].copy()
    window["range"] = window["high"] - window["low"]
    major = window.loc[window["range"].idxmax()]

    major_color = "GREEN" if major["close"] > major["open"] else "RED"
    major_range = safe_float(major["range"])

    trend_architect["major_candle"] = {
        "range": major_range,
        "type": "MARUBOZU",
        "color": major_color,
        "time": major.name.strftime("%H:%M")
    }

    # ---- Next Candle Relation ----
    after = window[window.index > major.name]
    if after.empty:
        relation = "NA"
        rc = "GREY"
    else:
        nxt = after.iloc[0]
        relation = (
            "SUPPORTING"
            if (nxt["close"] - nxt["open"]) * (major["close"] - major["open"]) > 0
            else "OPPOSING"
        )
        rc = "GREEN" if relation == "SUPPORTING" else "RED"

    trend_architect["next_candle"] = {
        "relation": relation,
        "color": rc
    }

    # ---- Distance + Overlaps ----
    total_distance = safe_float(
        df_freeze.iloc[-1]["close"] - df_0930.iloc[0]["open"]
    )

    overlaps = 0
    for i in range(1, len(df_freeze)):
        p = df_freeze.iloc[i - 1]
        c = df_freeze.iloc[i]

        bp = sorted([p["open"], p["close"]])
        bc = sorted([c["open"], c["close"]])
        ob = max(0, min(bp[1], bc[1]) - max(bp[0], bc[0]))

        if (bc[1] - bc[0]) > 0 and ob >= 0.8 * (bc[1] - bc[0]):
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
# WRITE SNAPSHOT (MERGE-SAFE)
# =========================
with open("snapshots/market_phase1.json", "r") as f:
    existing = json.load(f)

existing.update({
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
})

with open("snapshots/market_phase1.json", "w") as f:
    json.dump(existing, f, indent=2)
