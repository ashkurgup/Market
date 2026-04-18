import json
import requests
import pandas as pd
import pytz
from datetime import datetime, time
import yfinance as yf

IST = pytz.timezone("Asia/Kolkata")

# ============================================================
# Helpers
# ============================================================
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

def write_snapshot(obj):
    obj["meta"]["last_updated"] = now_ist().strftime("%H:%M:%S")
    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(obj, f, indent=2)

# ============================================================
# Load existing snapshot (for safe fallback)
# ============================================================
with open("snapshots/market_phase1.json", "r") as f:
    previous = json.load(f)

# Make sure containers exist
previous.setdefault("institutional_flows", None)
previous.setdefault("pcr", None)
previous.setdefault("trend_architect", previous.get("trend_architect"))
previous.setdefault("market_open", previous.get("market_open"))

# ============================================================
# Fetch recent NIFTY data (used ONLY to detect last trading day
# and compute frozen blocks if missing; otherwise preserved)
# ============================================================
df = yf.download("^NSEI", interval="5m", period="5d", progress=False)
df = fix_index(df)
df = norm_cols(df)
df = df.sort_index()

# Identify last trading day with sufficient candles
day_groups = df.groupby(df.index.date)
valid_days = [d for d, g in day_groups if len(g) >= 10]

# If absolutely no data, keep snapshot unchanged
if not valid_days:
    write_snapshot(previous)
    raise SystemExit(0)

last_day = valid_days[-1]
day_df = day_groups.get_group(last_day)

# ============================================================
# MARKET OPEN (FROZEN) — compute ONLY if missing
# ============================================================
if not previous.get("market_open"):
    oc_window = day_df[(day_df.index.time >= time(9, 15)) & (day_df.index.time <= time(9, 35))]
    if not oc_window.empty:
        r = oc_window.iloc[0]
        body = abs(r["close"] - r["open"])
        rng = r["high"] - r["low"]

        # Gap vs previous day close (PDC already frozen in snapshot)
        pdc = previous.get("previous_day", {}).get("pdc")
        gap_pts = round(r["open"] - pdc, 2) if pdc is not None else None

        previous["market_open"] = {
            "gap": {
                "direction": "UP" if gap_pts and gap_pts > 0 else "DOWN",
                "points": gap_pts,
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

# ============================================================
# TREND ARCHITECT (FROZEN) — compute ONLY if missing/empty
# ============================================================
if not previous.get("trend_architect"):
    win = day_df[(day_df.index.time >= time(9, 30)) & (day_df.index.time <= time(11, 0))]
    if len(win) >= 6:
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
        close_1100 = win[win.index.time == time(11, 0)]["close"].iloc[0]
        dist = round(close_1100 - open_0930, 2)

        if overlaps <= 2 and small_c <= 3:
            mc = "Steady move with buyer acceptance"
        elif overlaps >= 4 or small_c >= 5:
            mc = "Upward movement with frequent overlap — be cautious"
        else:
            mc = "Directional bias intact, but higher risk of deep pullback"

        previous["trend_architect"] = {
            "gap_behavior": {"status": "Closed by 11:05", "frozen_at": "11:05 IST"},
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

# ============================================================
# INSTITUTIONAL FLOWS (Moneycontrol — FINAL, CI‑SAFE)
# ============================================================
try:
    mc_url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/homepage/json"
    mc = requests.get(mc_url, timeout=10).json()

    rows = mc.get("data", [])
    if rows:
        # rows are latest-first
        latest = rows[0]

        as_of = latest["date"]  # e.g., "17-Apr-2026"

        fii_vals = [float(r["fii"]) for r in rows[:4]]
        dii_vals = [float(r["dii"]) for r in rows[:4]]

        previous["institutional_flows"] = {
            "as_of": as_of,
            "today": {
                "fii": fii_vals[0],
                "dii": dii_vals[0]
            },
            "history_4d": {
                "fii": [
                    {"day": f"Day-{i+1}", "value": fii_vals[i]}
                    for i in range(len(fii_vals))
                ],
                "dii": [
                    {"day": f"Day-{i+1}", "value": dii_vals[i]}
                    for i in range(len(dii_vals))
                ]
            }
        }
except Exception:
    # Network / holiday / site issue → keep last stored flows
    pass

# ============================================================
# PCR (NSE Option Chain JSON) — SAFE FALLBACK
# ============================================================
try:
    headers = {"User-Agent": "Mozilla/5.0"}
    oc = requests.get(
        "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
        headers=headers, timeout=10
    ).json()

    if isinstance(oc, dict) and "records" in oc:
        call_oi = sum(r.get("CE", {}).get("openInterest", 0) for r in oc["records"]["data"])
        put_oi = sum(r.get("PE", {}).get("openInterest", 0) for r in oc["records"]["data"])
        previous["pcr"] = {
            "index": "NIFTY",
            "type": "OI_PCR",
            "value": round(put_oi / call_oi, 2) if call_oi > 0 else None,
            "as_of": oc["records"].get("timestamp")
        }
except Exception:
    # Keep previous PCR untouched
    pass

# ============================================================
# WRITE SNAPSHOT
# ============================================================
write_snapshot(previous)
