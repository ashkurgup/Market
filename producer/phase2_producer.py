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

LOOKBACK_4H_DAYS = 70   # Strong
LOOKBACK_1H_DAYS = 22   # Moderate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

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
# WEEKLY LEVELS (FRIDAY CLOSE)
# ==============================

def compute_weekly_levels(df):
    df = df.copy()
    df["weekday"] = df["timestamp"].dt.weekday  # Mon=0, Fri=4

    fridays = df[df["weekday"] == 4]
    if fridays.empty:
        return dict.fromkeys(
            ["previous_week_high", "previous_week_low", "week_start", "week_end"]
        )

    friday_last = fridays.groupby(fridays["timestamp"].dt.date)["timestamp"].max()
    df["is_week_close"] = df["timestamp"].isin(friday_last)

    df["week_id"] = df["is_week_close"].cumsum()
    target_week = df["week_id"].max() - 1
    week_df = df[df["week_id"] == target_week]

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
# SWING DETECTION (SAFE)
# ==============================

def detect_swings(df, side, mode):
    swings = []
    series = df["high"] if mode == "high" else df["low"]

    for i in range(side, len(df) - side):
        center = float(series.iloc[i])
        left = series.iloc[i - side:i].to_numpy()
        right = series.iloc[i + 1:i + side + 1].to_numpy()

        if mode == "high" and center > left.max() and center > right.max():
            swings.append(center)

        if mode == "low" and center < left.min() and center < right.min():
            swings.append(center)

    return swings

# ==============================
# KEY LEVELS (FINAL)
# ==============================

def compute_key_levels(price, weekly):
    resistance = None
    support = None

    # ---- WEEKLY (Strong) ----
    if weekly["previous_week_high"] and weekly["previous_week_high"] > price:
        resistance = {
            "price": weekly["previous_week_high"],
            "strength": "Strong",
            "source": "Weekly High"
        }

    if weekly["previous_week_low"] and weekly["previous_week_low"] < price:
        support = {
            "price": weekly["previous_week_low"],
            "strength": "Strong",
            "source": "Weekly Low"
        }

    # ---- 4H (Strong) ----
    df4 = fetch_ohlc("4h", LOOKBACK_4H_DAYS)
    r4 = detect_swings(df4, 2, "high")
    s4 = detect_swings(df4, 2, "low")

    for p in sorted(r4):
        if p > price and resistance is None:
            resistance = {"price": p, "strength": "Strong", "source": "4H Structure"}

    for p in sorted(s4, reverse=True):
        if p < price and support is None:
            support = {"price": p, "strength": "Strong", "source": "4H Structure"}

    # ---- 1H (Moderate) ----
    df1 = fetch_ohlc("1h", LOOKBACK_1H_DAYS)
    r1 = detect_swings(df1, 3, "high")
    s1 = detect_swings(df1, 3, "low")

    for p in sorted(r1):
        if p > price and resistance is None:
            resistance = {"price": p, "strength": "Moderate", "source": "1H Structure"}

    for p in sorted(s1, reverse=True):
        if p < price and support is None:
            support = {"price": p, "strength": "Moderate", "source": "1H Structure"}

    return {
        "nearest_resistance": resistance,
        "nearest_support": support
    }

# ==============================
# MAIN
# ==============================

def run_phase2_producer():
    print(">>> Phase‑2 producer started")

    df5 = fetch_ohlc("5m", 7)
    current_price = float(df5["close"].iloc[-1])

    weekly = compute_weekly_levels(df5)
    session = compute_session_levels(df5)
    key_levels = compute_key_levels(current_price, weekly)

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",
        "session": {"start": "09:15", "end": "15:30", "timezone": "IST"},
        "weekly_levels": weekly,
        "key_levels": key_levels,
        "session_levels": session,
        "structure_events": [],
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
