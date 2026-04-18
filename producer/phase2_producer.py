import json
import os
from datetime import datetime, time
import pytz
import pandas as pd
import yfinance as yf

# ==============================
# CONFIG
# ==============================

SYMBOL = "^NSEI"
IST = pytz.timezone("Asia/Kolkata")

LOOKBACK_4H_DAYS = 70
LOOKBACK_1H_DAYS = 22

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

MAX_GAP_POINTS = 300
ACCEPTANCE_POINTS = 20
ACCEPTANCE_1M_CANDLES = 3

# ==============================
# DATA FETCH
# ==============================

def fetch_ohlc(interval, days):
    df = yf.download(
        SYMBOL,
        period=f"{days}d",
        interval=interval,
        progress=False
    )

    if df.empty:
        raise RuntimeError(f"No data for {interval}")

    df = df.reset_index()
    df.rename(columns={
        "Datetime": "timestamp",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close"
    }, inplace=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert(IST)
    return df

# ==============================
# WEEKLY LEVELS
# ==============================

def compute_weekly_levels(df):
    df = df.copy()
    df["weekday"] = df["timestamp"].dt.weekday

    fridays = df[df["weekday"] == 4]
    if fridays.empty:
        return dict.fromkeys(
            ["previous_week_high", "previous_week_low", "week_start", "week_end"]
        )

    friday_last = fridays.groupby(fridays["timestamp"].dt.date)["timestamp"].max()
    df["is_week_close"] = df["timestamp"].isin(friday_last)

    df["week_id"] = df["is_week_close"].cumsum()
    week_df = df[df["week_id"] == df["week_id"].max() - 1]

    if week_df.empty:
        return dict.fromkeys(
            ["previous_week_high", "previous_week_low", "week_start", "week_end"]
        )

    return {
        "previous_week_high": float(week_df["high"].max()),
        "previous_week_low": float(week_df["low"].min()),
        "week_start": week_df["timestamp"].min().date().isoformat(),
        "week_end": week_df["timestamp"].max().date().isoformat()
    }

# ==============================
# SESSION LEVELS (15m)
# ==============================

def compute_session_levels(df_5m):
    today = datetime.now(IST).date()
    start = datetime.combine(today, time(9, 15), IST)
    end = datetime.combine(today, time(15, 30), IST)

    s = df_5m[(df_5m["timestamp"] >= start) & (df_5m["timestamp"] <= end)]
    if s.empty:
        return {
            "high": None,
            "low": None,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        }

    s15 = (
        s.set_index("timestamp")
         .resample("15T", closed="right", label="right")
         .agg({"high": "max", "low": "min"})
         .dropna()
    )

    if s15.empty:
        return {
            "high": None,
            "low": None,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        }

    return {
        "high": float(s15["high"].iloc[-1]),
        "low": float(s15["low"].iloc[-1]),
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }

# ==============================
# SUPPORT / RESISTANCE ENGINE
# ==============================

def count_respects(df_5m, level, lookback=500):
    level = float(level)
    respects = 0
    recent = df_5m.tail(lookback)

    for i in range(1, len(recent) - 1):
        price = float(recent["close"].iloc[i])
        next_price = float(recent["close"].iloc[i + 1])
        if abs(price - level) <= 10 and abs(next_price - price) >= 30:
            respects += 1

    return respects


def detect_structural_levels(df, side, is_high):
    swings = []
    series = df["high"] if is_high else df["low"]

    for i in range(side, len(df) - side):
        center = float(series.iloc[i])
        left = series.iloc[i - side:i].to_numpy()
        right = series.iloc[i + 1:i + side + 1].to_numpy()

        if is_high and center > left.max() and center > right.max():
            swings.append(center)
        if not is_high and center < left.min() and center < right.min():
            swings.append(center)

    return list(set(swings))


def compute_support_resistance(price, weekly, df_5m):
    resistance, support = [], []

    if weekly["previous_week_high"]:
        resistance.append({"price": weekly["previous_week_high"], "strong": True})
    if weekly["previous_week_low"]:
        support.append({"price": weekly["previous_week_low"], "strong": True})

    df4 = fetch_ohlc("4h", LOOKBACK_4H_DAYS)
    for p in detect_structural_levels(df4, 2, True):
        if count_respects(df_5m, p) >= 2:
            resistance.append({"price": p, "strong": True})

    for p in detect_structural_levels(df4, 2, False):
        if count_respects(df_5m, p) >= 2:
            support.append({"price": p, "strong": True})

    resistance = sorted(resistance, key=lambda x: abs(x["price"] - price))
    support = sorted(support, key=lambda x: abs(x["price"] - price))

    def trim(levels):
        out, last = [], price
        for l in levels:
            if abs(l["price"] - last) <= MAX_GAP_POINTS or not out:
                out.append(l)
                last = l["price"]
        return out

    def fmt(levels):
        return [
            f'{l["price"]:.2f} (Strong)' if l["strong"] else f'{l["price"]:.2f}'
            for l in levels
        ]

    return {
        "resistance": fmt(trim([l for l in resistance if l["price"] > price])),
        "support": fmt(trim([l for l in support if l["price"] < price]))
    }

# ==============================
# BOS / CHOCH (1m acceptance)
# ==============================

def detect_5m_structure(df5):
    if len(df5) < 5:
        return None
    h, l = df5["high"].to_numpy(), df5["low"].to_numpy()

    if h[-3] > h[-4] and h[-3] > h[-2]:
        return ("HH", h[-3])
    if l[-3] < l[-4] and l[-3] < l[-2]:
        return ("LL", l[-3])
    if h[-3] < h[-4] and h[-3] < h[-2]:
        return ("LH", h[-3])
    if l[-3] > l[-4] and l[-3] > l[-2]:
        return ("HL", l[-3])
    return None


def accept_1m(df1, level, direction):
    closes = df1["close"].to_numpy()
    if direction == "up":
        return max(closes) >= level + ACCEPTANCE_POINTS or all(
            c > level for c in closes[-ACCEPTANCE_1M_CANDLES:]
        )
    if direction == "down":
        return min(closes) <= level - ACCEPTANCE_POINTS or all(
            c < level for c in closes[-ACCEPTANCE_1M_CANDLES:]
        )
    return False


def detect_bos_choch(df5, df1, key_levels):
    events = []
    struct = detect_5m_structure(df5)
    if not struct:
        return events

    stype, sprice = struct
    levels = [float(v.split()[0]) for side in key_levels.values() for v in side]

    if not any(abs(sprice - l) <= 50 for l in levels):
        return events

    if stype in ["LH", "HH"] and accept_1m(df1, sprice, "up"):
        events.append({"event": "BoS", "direction": "Up", "level": sprice})

    if stype in ["HL", "LL"] and accept_1m(df1, sprice, "down"):
        events.append({"event": "BoS", "direction": "Down", "level": sprice})

    if stype == "LH" and accept_1m(df1, sprice, "up"):
        events.append({"event": "ChoCH", "direction": "Up", "level": sprice})

    if stype == "HL" and accept_1m(df1, sprice, "down"):
        events.append({"event": "ChoCH", "direction": "Down", "level": sprice})

    return events

# ==============================
# MAIN
# ==============================

def run_phase2_producer():
    print(">>> Phase‑2 producer started")

    df5 = fetch_ohlc("5m", 7)
    df1 = fetch_ohlc("1m", 2)

    current_price = float(df5["close"].iloc[-1])

    weekly = compute_weekly_levels(df5)
    session = compute_session_levels(df5)
    key_levels = compute_support_resistance(current_price, weekly, df5)
    structure_events = detect_bos_choch(df5, df1, key_levels)

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",
        "session": {"start": "09:15", "end": "15:30", "timezone": "IST"},
        "weekly_levels": weekly,
        "key_levels": key_levels,
        "session_levels": session,
        "structure_events": structure_events,
        "momentum_events": [],
        "global_indices": {"time_window_minutes": 30, "indices": []},
        "bias": {"day": None, "h4": None, "h1": None},
        "computed_at": datetime.now(IST).isoformat()
    }

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(">>> Phase‑2 snapshot written successfully")


if __name__ == "__main__":
    run_phase2_producer()
