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

# ============================================================
# SUPPORT / RESISTANCE ENGINE – FINAL
# ============================================================

MAX_GAP_POINTS = 300
FLIP_DISTANCE = 50
FLIP_15M_CANDLES = 3


def count_respects(df_5m, level, lookback=500):
    """
    Count meaningful respects:
    touch/breach followed by rejection >= 30 points
    """
    respects = 0
    recent = df_5m.tail(lookback)

    for i in range(1, len(recent) - 1):
        price = recent["close"].iloc[i]
        prev = recent["close"].iloc[i - 1]
        nxt = recent["close"].iloc[i + 1]

        if abs(price - level) <= 10:
            if (nxt - price) >= 30 or (price - nxt) >= 30:
                respects += 1

    return respects


def detect_structural_levels(df_tf, side, is_high=True):
    """
    Swing detection (safe, non-ambiguous)
    """
    swings = []
    series = df_tf["high"] if is_high else df_tf["low"]

    for i in range(side, len(df_tf) - side):
        center = float(series.iloc[i])
        left = series.iloc[i - side:i].to_numpy()
        right = series.iloc[i + 1:i + side + 1].to_numpy()

        if is_high and center > left.max() and center > right.max():
            swings.append(center)

        if not is_high and center < left.min() and center < right.min():
            swings.append(center)

    return list(set(swings))  # uniqueness


def evaluate_role_flip(df_15m, level, role):
    """
    Support ↔ Resistance flip logic
    """
    closes = df_15m["close"].to_numpy()

    if role == "support":
        if closes[-1] < level - FLIP_DISTANCE:
            return "resistance"

        if all(c < level for c in closes[-FLIP_15M_CANDLES:]):
            return "resistance"

    if role == "resistance":
        if closes[-1] > level + FLIP_DISTANCE:
            return "support"

        if all(c > level for c in closes[-FLIP_15M_CANDLES:]):
            return "support"

    return role


def compute_support_resistance(current_price, weekly, df_5m):
    """
    FINAL Support / Resistance Engine
    """

    eligible_resistance = []
    eligible_support = []

    # ---- WEEKLY (always eligible, Strong)
    if weekly["previous_week_high"]:
        eligible_resistance.append({
            "price": weekly["previous_week_high"],
            "strong": True
        })

    if weekly["previous_week_low"]:
        eligible_support.append({
            "price": weekly["previous_week_low"],
            "strong": True
        })

    # ---- 4H STRUCTURE (Strong)
    df_4h = fetch_ohlc("4h", LOOKBACK_4H_DAYS)

    for p in detect_structural_levels(df_4h, side=2, is_high=True):
        if count_respects(df_5m, p) >= 2:
            eligible_resistance.append({"price": p, "strong": True})

    for p in detect_structural_levels(df_4h, side=2, is_high=False):
        if count_respects(df_5m, p) >= 2:
            eligible_support.append({"price": p, "strong": True})

    # ---- 1H STRUCTURE (Eligible, may or may not be strong)
    df_1h = fetch_ohlc("1h", LOOKBACK_1H_DAYS)

    for p in detect_structural_levels(df_1h, side=3, is_high=True):
        respects = count_respects(df_5m, p)
        if respects >= 2:
            eligible_resistance.append({"price": p, "strong": respects >= 3})

    for p in detect_structural_levels(df_1h, side=3, is_high=False):
        respects = count_respects(df_5m, p)
        if respects >= 2:
            eligible_support.append({"price": p, "strong": respects >= 3})

    # ---- SORT BY DISTANCE
    eligible_resistance = sorted(
        eligible_resistance, key=lambda x: abs(x["price"] - current_price)
    )
    eligible_support = sorted(
        eligible_support, key=lambda x: abs(x["price"] - current_price)
    )

    # ---- APPLY 300 POINT GAP RULE
    def build_levels(levels, direction):
        result = []
        last_price = current_price

        for lvl in levels:
            gap = abs(lvl["price"] - last_price)
            if gap > MAX_GAP_POINTS and result:
                continue

            result.append(lvl)
            last_price = lvl["price"]

        return result

    resistance_levels = build_levels(
        [l for l in eligible_resistance if l["price"] > current_price], "resistance"
    )

    support_levels = build_levels(
        [l for l in eligible_support if l["price"] < current_price], "support"
    )

    # ---- ROLE STABILITY CHECK (15m)
    df_15m = df_5m.set_index("timestamp").resample("15T").last().dropna()

    if resistance_levels:
        for lvl in resistance_levels:
            lvl["role"] = evaluate_role_flip(df_15m, lvl["price"], "resistance")

    if support_levels:
        for lvl in support_levels:
            lvl["role"] = evaluate_role_flip(df_15m, lvl["price"], "support")

    # ---- FINAL FORMAT FOR UI
    def format_levels(levels):
        out = []
        for l in levels:
            if l["strong"]:
                out.append(f'{l["price"]:.2f} (Strong)')
            else:
                out.append(f'{l["price"]:.2f}')
        return out

    return {
        "resistance": format_levels(resistance_levels),
        "support": format_levels(support_levels)
    }

# ==============================
# MAIN
# ==============================

def run_phase2_producer():
    print(">>> Phase‑2 producer started")

    # ---- Fetch latest 5‑min data (base for everything intraday)
    df5 = fetch_ohlc("5m", 7)
    current_price = float(df5["close"].iloc[-1])

    # ---- Weekly & Session (already correct)
    weekly = compute_weekly_levels(df5)
    session = compute_session_levels(df5)

    # ---- ✅ FINAL Support / Resistance Engine (CORRECT CALL)
    key_levels = compute_support_resistance(
        current_price=current_price,
        weekly=weekly,
        df_5m=df5
    )

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

    print(">>> Phase‑2 snapshot written successfully")


if __name__ == "__main__":
    run_phase2_producer()
