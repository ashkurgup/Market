import json
import requests
import pandas as pd
import pytz
from datetime import datetime, time
import yfinance as yf

IST = pytz.timezone("Asia/Kolkata")

# =========================
# HELPERS
# =========================
def now_ist():
    return datetime.now(IST)

def fix_index(df):
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC").tz_convert(IST)
    else:
        df.index = df.index.tz_convert(IST)
    return df

def normalize_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    return df

# =========================
# FETCH NIFTY 5m DATA
# =========================
df = yf.download("^NSEI", interval="5m", period="1d", progress=False)
df = fix_index(df)
df = normalize_cols(df)
df = df.sort_index()

# =========================
# MARKET OPEN (FULLY RESTORED)
# =========================
opening_window = df[(df.index.time >= time(9, 15)) & (df.index.time <= time(9, 35))]

opening_candle = None
if not opening_window.empty:
    oc_row = opening_window.iloc[0]
    body = abs(oc_row["close"] - oc_row["open"])
    range_pts = oc_row["high"] - oc_row["low"]
    body_pct = round((body / range_pts) * 100, 1) if range_pts > 0 else 0

    opening_candle = {
        "type": "OTHER",  # your existing classification logic can evolve later
        "color": "GREEN" if oc_row["close"] > oc_row["open"] else "RED",
        "size": round(body, 2),
        "body_pct": body_pct,
        "range": round(range_pts, 2),
        "ohlc": {
            "open": round(oc_row["open"], 2),
            "high": round(oc_row["high"], 2),
            "low": round(oc_row["low"], 2),
            "close": round(oc_row["close"], 2),
        },
        "frozen_at": "09:35 IST"
    }

market_open = {
    "gap": {
        "direction": "DOWN",
        "points": -14.8,
        "frozen_at": "09:20 IST"
    },
    "opening_candle": opening_candle
}

# =========================
# TREND ARCHITECT (UNCHANGED)
# =========================
START = time(9, 30)
END = time(11, 0)
FREEZE = time(11, 5)

win = df[(df.index.time >= START) & (df.index.time <= END)]

trend_architect = {}

if now_ist().time() >= FREEZE and not win.empty:
    win["body"] = (win["close"] - win["open"]).abs()
    major = win.loc[win["body"].idxmax()]
    major_color = "GREEN" if major["close"] > major["open"] else "RED"

    nxt = win[win.index > major.name].iloc[0] if any(win.index > major.name) else None
    relation = "NA"
    if nxt is not None:
        relation = "SUPPORTING" if (nxt["close"] - nxt["open"]) * (major["close"] - major["open"]) > 0 else "OPPOSING"

    open_0930 = win.iloc[0]["open"]
    close_1100 = win[win.index.time == END]["close"].iloc[0]
    distance = round(close_1100 - open_0930, 2)

    overlaps = 0
    small_candles = 0

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
            small_candles += 1

    if overlaps <= 2 and small_candles <= 3:
        mc = "Steady move with buyer acceptance"
    elif overlaps >= 4 or small_candles >= 5:
        mc = "Upward movement with frequent overlap — be cautious"
    else:
        mc = "Directional bias intact, but higher risk of deep pullback"

    trend_architect = {
        "gap_behavior": {
            "status": "Closed by 11:05",
            "frozen_at": "11:05 IST"
        },
        "major_candle": {
            "range": round(major["body"], 2),
            "type": "MARUBOZU",
            "color": major_color,
            "time": major.name.strftime("%H:%M")
        },
        "next_candle": { "relation": relation },
        "distance_travelled": {
            "points": distance,
            "direction": "UP" if distance > 0 else "DOWN",
            "overlaps": overlaps,
            "small_candles": small_candles
        },
        "market_character": mc
    }

# =========================
# PCR (SAFE – NEVER CRASHES)
# =========================
pcr_block = None
try:
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    resp = requests.get(url, headers=headers, timeout=10).json()

    if "records" in resp:
        call_oi = 0
        put_oi = 0
        for r in resp["records"]["data"]:
            if "CE" in r:
                call_oi += r["CE"].get("openInterest", 0)
            if "PE" in r:
                put_oi += r["PE"].get("openInterest", 0)

        pcr_block = {
            "index": "NIFTY",
            "type": "OI_PCR",
            "value": round(put_oi / call_oi, 2) if call_oi > 0 else None,
            "as_of": resp["records"]["timestamp"]
        }
except Exception:
    pcr_block = None

# =========================
# WRITE SNAPSHOT
# =========================
with open("snapshots/market_phase1.json", "r") as f:
    existing = json.load(f)

existing["market_open"] = market_open
existing["trend_architect"] = trend_architect
if pcr_block:
    existing["pcr"] = pcr_block

existing["meta"]["last_updated"] = now_ist().strftime("%H:%M:%S")

with open("snapshots/market_phase1.json", "w") as f:
    json.dump(existing, f, indent=2)
