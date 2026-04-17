import json
import pandas as pd
import pytz
from datetime import datetime, time
import yfinance as yf
import requests
from io import StringIO

IST = pytz.timezone("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

# =========================
# SAFE DATA HELPERS
# =========================
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
# FETCH NIFTY 5M
# =========================
df = yf.download("^NSEI", interval="5m", period="1d", progress=False)
df = fix_index(df)
df = normalize_cols(df)
df = df.sort_index()

START = time(9, 30)
END = time(11, 0)
FREEZE = time(11, 5)

win = df[(df.index.time >= START) & (df.index.time <= END)]

trend_architect = {}

if now_ist().time() >= FREEZE and not win.empty:
    # MAJOR CANDLE (BODY)
    win["body"] = (win["close"] - win["open"]).abs()
    major = win.loc[win["body"].idxmax()]

    major_color = "GREEN" if major["close"] > major["open"] else "RED"

    # NEXT CANDLE RELATION
    nxt = win[win.index > major.name].iloc[0] if any(win.index > major.name) else None
    relation = "NA"
    if nxt is not None:
        relation = "SUPPORTING" if (nxt["close"] - nxt["open"]) * (major["close"] - major["open"]) > 0 else "OPPOSING"

    # TOTAL DISTANCE
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

    # MARKET CHARACTER
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
        "next_candle": {
            "relation": relation
        },
        "distance_travelled": {
            "points": distance,
            "direction": "UP" if distance > 0 else "DOWN",
            "overlaps": overlaps,
            "small_candles": small_candles
        },
        "market_character": mc
    }

# =========================
# FETCH FII / DII (NSE)
# =========================
url = "https://www.nseindia.com/api/fiicompanies"
headers = {"User-Agent": "Mozilla/5.0"}
raw = requests.get(url, headers=headers, timeout=10).json()

df_flow = pd.DataFrame(raw["data"])
df_flow["date"] = pd.to_datetime(df_flow["date"])

df_fii = df_flow[df_flow["category"] == "FII/FPI"].sort_values("date", ascending=False)
df_dii = df_flow[df_flow["category"] == "DII"].sort_values("date", ascending=False)

today_date = df_fii.iloc[0]["date"].strftime("%Y-%m-%d")

fii_vals = df_fii.head(4)["net"].round(2).tolist()
dii_vals = df_dii.head(4)["net"].round(2).tolist()

institutional_flows = {
    "as_of": today_date,
    "unit": "₹ Cr",
    "today": {
        "fii": fii_vals[0],
        "dii": dii_vals[0]
    },
    "history_4d": {
        "fii": [
            {"day": f"Day-{i+1}", "value": fii_vals[i]} for i in range(4)
        ],
        "dii": [
            {"day": f"Day-{i+1}", "value": dii_vals[i]} for i in range(4)
        ]
    }
}

# =========================
# WRITE SNAPSHOT
# =========================
with open("snapshots/market_phase1.json", "r") as f:
    existing = json.load(f)

existing["trend_architect"] = trend_architect
existing["institutional_flows"] = institutional_flows
existing["meta"]["last_updated"] = now_ist().strftime("%H:%M:%S")

with open("snapshots/market_phase1.json", "w") as f:
    json.dump(existing, f, indent=2)
