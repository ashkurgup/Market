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

def norm_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    return df

# =========================
# LOAD EXISTING SNAPSHOT
# =========================
with open("snapshots/market_phase1.json", "r") as f:
    previous = json.load(f)

# =========================
# FETCH NIFTY 5‑MIN DATA
# =========================
df = yf.download("^NSEI", interval="5m", period="5d", progress=False)
df = fix_index(df)
df = norm_cols(df)
df = df.sort_index()

# Detect last trading day with enough candles
day_groups = df.groupby(df.index.date)
valid_days = [d for d, g in day_groups if len(g) >= 10]

if not valid_days:
    # No market data → keep everything frozen
    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(previous, f, indent=2)
    exit(0)

last_day = valid_days[-1]
day_df = day_groups.get_group(last_day)

# =========================
# MARKET OPEN (FROZEN)
# =========================
if "market_open" not in previous:
    oc_window = day_df[(day_df.index.time >= time(9, 15)) & (day_df.index.time <= time(9, 35))]
    if not oc_window.empty:
        r = oc_window.iloc[0]
        body = abs(r["close"] - r["open"])
        rng = r["high"] - r["low"]

        previous["market_open"] = {
            "gap": {
                "direction": "DOWN",
                "points": round(r["open"] - previous["previous_day"]["pdc"], 2),
                "frozen_at": "09:20 IST"
            },
            "opening_candle": {
                "type": "OTHER",
                "color": "GREEN" if r["close"] > r["open"] else "RED",
                "size": round(body, 2),
                "body_pct": round((body / rng) * 100, 1) if rng > 0 else 0,
                "range": round(rng, 2),
                "ohlc": {
                    "open": round(r["open"], 2),
                    "high": round(r["high"], 2),
                    "low": round(r["low"], 2),
                    "close": round(r["close"], 2),
                },
                "frozen_at": "09:35 IST"
            }
        }

# =========================
# TREND ARCHITECT (FROZEN)
# =========================
if "trend_architect" not in previous or not previous["trend_architect"]:
    win = day_df[(day_df.index.time >= time(9, 30)) & (day_df.index.time <= time(11, 0))]

    if len(win) >= 6:
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
        close_1100 = win[win.index.time == time(11, 0)]["close"].iloc[0]
        dist = round(close_1100 - open_0930, 2)

        if overlaps <= 2 and small_c <= 3:
            mc = "Steady move with buyer acceptance"
        elif overlaps >= 4 or small_c >= 5:
            mc = "Upward movement with frequent overlap — be cautious"
        else:
            mc = "Directional bias intact, but higher risk of deep pullback"

        previous["trend_architect"] = {
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
            "next_candle": {
                "relation": "SUPPORTING" if major_color == "GREEN" else "OPPOSING"
            },
            "distance_travelled": {
                "points": dist,
                "direction": "UP" if dist > 0 else "DOWN",
                "overlaps": overlaps,
                "small_candles": small_c
            },
            "market_character": mc
        }

# =========================
# PCR (SAFE)
# =========================
try:
    headers = {"User-Agent": "Mozilla/5.0"}
    oc = requests.get(
        "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
        headers=headers, timeout=10
    ).json()

    if "records" in oc:
        call_oi = sum(r.get("CE", {}).get("openInterest", 0) for r in oc["records"]["data"])
        put_oi = sum(r.get("PE", {}).get("openInterest", 0) for r in oc["records"]["data"])
        previous["pcr"] = {
            "index": "NIFTY",
            "type": "OI_PCR",
            "value": round(put_oi / call_oi, 2) if call_oi > 0 else None,
            "as_of": oc["records"]["timestamp"]
        }
except Exception:
    pass

# =========================
# META UPDATE
# =========================
previous["meta"]["last_updated"] = now_ist().strftime("%H:%M:%S")

with open("snapshots/market_phase1.json", "w") as f:
    json.dump(previous, f, indent=2)
