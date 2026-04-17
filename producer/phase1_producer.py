import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

# =============================
# ATR (15m, 14)
# =============================
def calculate_atr_15m(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(period).mean()
    return round(float(atr.dropna().iloc[-1]), 1)


# =============================
# VWAP (SAFE — NEVER NaN)
# =============================
def calculate_vwap_15m(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    vol = df["Volume"]

    vol_sum = vol.sum()
    if vol_sum == 0 or pd.isna(vol_sum):
        return None

    vwap = (tp * vol).sum() / vol_sum
    return round(float(vwap), 2)


# =============================
# MARKET OPEN (FROZEN)
# =============================
def calculate_market_open(df_today, prev_close):
    first = df_today.iloc[0]

    o = round(float(first["Open"]), 2)
    h = round(float(first["High"]), 2)
    l = round(float(first["Low"]), 2)
    c = round(float(first["Close"]), 2)

    range_pts = round(h - l, 2)
    body_pts = round(abs(c - o), 2)

    # Candle classification
    if range_pts == 0:
        candle_type = "DOJI"
        candle_color = "NEUTRAL"
    elif body_pts <= range_pts * 0.25:
        candle_type = "DOJI"
        candle_color = "NEUTRAL"
    elif body_pts >= range_pts * 0.70:
        candle_type = "MARUBOZU"
        candle_color = "GREEN" if c > o else "RED"
    else:
        candle_type = "BODY"
        candle_color = "GREEN" if c > o else "RED"

    # Gap
    gap_pts = round(o - prev_close, 2)
    if abs(gap_pts) < 0.25:
        gap_dir = "FLAT"
    elif gap_pts > 0:
        gap_dir = "UP"
    else:
        gap_dir = "DOWN"

    return {
        "gap": {
            "direction": gap_dir,
            "points": gap_pts,
            "frozen_at": "09:20 IST"
        },
        "opening_candle": {
            "type": candle_type,
            "color": candle_color,
            "size": body_pts,
            "range": range_pts,
            "ohlc": {
                "open": o,
                "high": h,
                "low": l,
                "close": c
            },
            "frozen_at": "09:35 IST"
        }
    }


# =============================
# MAIN
# =============================
def main():
    now = datetime.now(IST)

    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)

    df_today = df15[df15.index.date == now.date()]
    if len(df_today) < 5:
        return

    prev_close = round(
        float(df15[df15.index.date < now.date()].iloc[-1]["Close"]), 2
    )

    last_close = round(float(df_today.iloc[-1]["Close"]), 2)

    # ATR
    atr_value = calculate_atr_15m(df_today)
    atr_sample_status = (
        "Enough Sample" if len(df_today) >= ATR_PERIOD + 1 else "Less Sample"
    )

    # VWAP
    vwap_value = calculate_vwap_15m(df_today)
    expansion = round(float(df_today.iloc[-1]["High"] - df_today.iloc[-1]["Low"]), 1)

    if vwap_value is None:
        vwap_position = "UNKNOWN"
    else:
        distance = last_close - vwap_value
        threshold = expansion * 0.15
        if abs(distance) <= threshold:
            vwap_position = "NEAR"
        elif distance > 0:
            vwap_position = "ABOVE"
        else:
            vwap_position = "BELOW"

    basis_time = df_today.index[-1].strftime("%H:%M")

    # Choppiness
    if atr_sample_status == "Less Sample":
        choppiness = {
            "state": "Not Classified",
            "message": "Insufficient Volatility Sample"
        }
    elif atr_value <= 18:
        choppiness = {
            "state": "High",
            "message": "Rotational / Mean‑Reversion Likely"
        }
    elif atr_value <= 25:
        choppiness = {
            "state": "Moderate",
            "message": "Expansion Needs Confirmation"
        }
    else:
        choppiness = {
            "state": "Low",
            "message": "Continuation‑Friendly Environment"
        }

    market_open = calculate_market_open(df_today, prev_close)

    output = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST"
        },
        "nifty": {
            "spot": last_close,
            "change_points": round(last_close - prev_close, 1),
            "change_percent": round(((last_close - prev_close) / prev_close) * 100, 2)
        },
        "volatility": {
            "atr": atr_value,
            "sample_status": atr_sample_status,
            "reliable_from": ATR_RELIABLE_FROM
        },
        "choppiness": choppiness,
        "vwap": {
            "value": vwap_value,
            "position": vwap_position,
            "expansion_range": expansion,
            "midline": "RISING",
            "basis_candle_close": basis_time
        },
        "market_open": market_open,
        "trend_architect": {
            "gap_behavior": "CLOSED_BY_1105",
            "major_candle": {
                "size": 32.45,
                "type": "MARUBOZU",
                "direction": "UP",
                "time": "09:35"
            },
            "next_candle_relation": "OPPOSING",
            "effective_time": "11:00 AM"
        },
        "previous_day": {
            "pdh": 24203.25,
            "pdl": 24177.80,
            "pdc": 24188.40
        },
        "institutional_flows": {
            "fii_today": None,
            "dii_today": None,
            "fii_last_4_days": [None, None, None, None],
            "dii_last_4_days": [None, None, None, None]
        }
    }

    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()
