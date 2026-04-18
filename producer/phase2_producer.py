import json
import os
from datetime import datetime, time
import pytz
import pandas as pd
import yfinance as yf

# =========================================================
# CONFIG
# =========================================================

SYMBOL = "^NSEI"  # NIFTY 50 (Yahoo Finance)
IST = pytz.timezone("Asia/Kolkata")

LOOKBACK_4H_DAYS = 70
LOOKBACK_1H_DAYS = 22

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "snapshots", "market_phase2.json")

# =========================================================
# DATA FETCH
# =========================================================

def fetch_ohlc(interval, days):
    df = yf.download(
        SYMBOL,
        period=f"{days}d",
        interval=interval,
        progress=False
    )

    if df.empty:
        raise RuntimeError(f"No data fetched for interval {interval}")

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

# =========================================================
# WEEKLY LEVELS (LAST FRIDAY CLOSE)
# =========================================================

def compute_weekly_levels(df):
    df = df.copy()
    df["weekday"] = df["timestamp"].dt.weekday  # Monday=0, Friday=4

    friday_df = df[df["weekday"] == 4]
    if friday_df.empty:
        return {
            "previous_week_high": None,
            "previous_week_low": None,
            "week_start": None,
            "week_end": None
        }

    friday_closes = friday_df.groupby(friday_df["timestamp"].dt.date)["timestamp"].max()
    df["is_week_close"] = df["timestamp"].isin(friday_closes)

    df["week_id"] = df["is_week_close"].cumsum()
    last_completed_week_id = df["week_id"].max() - 1

    week_df = df[df["week_id"] == last_completed_week_id]
    if week_df.empty:
        return {
            "previous_week_high": None,
            "previous_week_low": None,
            "week_start": None,
            "week_end": None
        }

    return {
        "previous_week_high": float(week_df["high"].max()),
        "previous_week_low": float(week_df["low"].min()),
        "week_start": week_df["timestamp"].min().date().isoformat(),
        "week_end": week_df["timestamp"].max().date().isoformat()
    }

# =========================================================
# SESSION LEVELS (15‑MIN, CLOSE‑BASED)
# =========================================================

def compute_session_levels(df_5m):
    today = datetime.now(IST).date()
    start = datetime.combine(today, time(9, 15), IST)
    end = datetime.combine(today, time(15, 30), IST)

    session_df = df_5m[
        (df_5m["timestamp"] >= start) &
        (df_5m["timestamp"] <= end)
    ]

    if session_df.empty:
        return {
            "high": None,
            "low": None,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        }

    candles_15m = (
        session_df
        .set_index("timestamp")
        .resample("15T", closed="right", label="right")
        .agg({"high": "max", "low": "min"})
        .dropna()
    )

    if candles_15m.empty:
        return {
            "high": None,
            "low": None,
            "based_on_timeframe": "15m",
            "update_rule": "on_candle_close"
        }

    return {
        "high": float(candles_15m["high"].max()),
        "low": float(candles_15m["low"].min()),
        "based_on_timeframe": "15m",
        "update_rule": "on_candle_close"
    }

# =========================================================
# SWING DETECTION
# =========================================================

def detect_swings(df, side, is_high=True):
    swings = []
    series = df["high"] if is_high else df["low"]

    for i in range(side, len(df) - side):
        center = series.iloc[i]
        left = series.iloc[i - side:i]
        right = series.iloc[i + 1:i + 1 + side]

        if is_high and center > left.max() and center > right.max():
            swings.append(center)

        if not is_high and center < left.min() and center < right.min():
            swings.append(center)

    return swings

# =========================================================
# KEY LEVELS
# =========================================================

def compute_key_levels(current_price, weekly, session):
    levels = {"resistance": [], "support": []}

    # ---- WEEKLY (STRONG LOCK) ----
    if weekly["previous_week_high"] and weekly["previous_week_high"] > current_price:
        levels["resistance"].append({
            "price": weekly["previous_week_high"],
            "strength": "Strong",
            "source": "Weekly High"
        })

    if weekly["previous_week_low"] and weekly["previous_week_low"] < current_price:
        levels["support"].append({
            "price": weekly["previous_week_low"],
            "strength": "Strong",
            "source": "Weekly Low"
        })

    # ---- 4H STRUCTURE (STRONG) ----
    df_4h = fetch_ohlc("4h", LOOKBACK_4H_DAYS)
    res_4h = detect_swings(df_4h, side=2, is_high=True)
    sup_4h = detect_swings(df_4h, side=2, is_high=False)

    for p in res_4h:
        if p > current_price:
            levels["resistance"].append({
                "price": float(p),
                "strength": "Strong",
                "source": "4H Structure"
            })

    for p in sup_4h:
        if p < current_price:
            levels["support"].append({
                "price": float(p),
                "strength": "Strong",
                "source": "4H Structure"
            })

    # ---- 1H STRUCTURE (MODERATE) ----
    df_1h = fetch_ohlc("1h", LOOKBACK_1H_DAYS)
    res_1h = detect_swings(df_1h, side=3, is_high=True)
    sup_1h = detect_swings(df_1h, side=3, is_high=False)

    for p in res_1h:
        if p > current_price:
            levels["resistance"].append({
                "price": float(p),
                "strength": "Moderate",
                "source": "1H Structure"
            })

    for p in sup_1h:
        if p < current_price:
            levels["support"].append({
                "price": float(p),
                "strength": "Moderate",
                "source": "1H Structure"
            })

    # ---- SESSION (MODERATE‑LOW) ----
    if session["high"] and session["high"] > current_price:
        levels["resistance"].append({
            "price": float(session["high"]),
            "strength": "Moderate",
            "source": "Session High"
        })

    if session["low"] and session["low"] < current_price:
        levels["support"].append({
            "price": float(session["low"]),
            "strength": "Moderate",
            "source": "Session Low"
        })

    # ---- SORT + SELECT (NEAREST FIRST) ----
    levels["resistance"] = sorted(
        levels["resistance"], key=lambda x: x["price"]
    )[:2]

    levels["support"] = sorted(
        levels["support"], key=lambda x: x["price"], reverse=True
    )[:2]

    return levels

# =========================================================
# MAIN PRODUCER
# =========================================================

def run_phase2_producer():
    print(">>> Phase‑2 producer started")

    df_5m = fetch_ohlc("5m", 7)
    current_price = float(df_5m["close"].iloc[-1])

    weekly = compute_weekly_levels(df_5m)
    session = compute_session_levels(df_5m)
    key_levels = compute_key_levels(current_price, weekly, session)

    snapshot = {
        "phase": 2,
        "symbol": "NIFTY",
        "session": {
            "start": "09:15",
            "end": "15:30",
            "timezone": "IST"
        },
        "weekly_levels": weekly,
        "key_levels": key_levels,
        "session_levels": session,
        "structure_events": [],
        "momentum_events": [],
        "global_indices": {
            "time_window_minutes": 30,
            "indices": []
        },
        "bias": {
            "day": None,
            "h4": None,
            "h1": None
        },
        "computed_at": datetime.now(IST).isoformat()
    }

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(">>> Phase‑2 snapshot written")

if __name__ == "__main__":
    run_phase2_producer()
