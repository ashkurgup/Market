import json
import pandas as pd
import yfinance as yf
from datetime import datetime, time, timedelta
import pytz

# -----------------------------
# CONFIG
# -----------------------------
IST = pytz.timezone("Asia/Kolkata")
ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

# -----------------------------
# ATR (15‑min, 14 period)
# -----------------------------
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

# -----------------------------
# VWAP (TradingView‑consistent)
# -----------------------------
def calculate_vwap_15m(df):
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    volume = df["Volume"]

    vwap = (typical_price * volume).sum() / volume.sum()
    return round(float(vwap), 2)

# -----------------------------
# MAIN
# -----------------------------
def main():
    now = datetime.now(IST)

    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)

    # Keep only today's candles
    df_today = df15[df15.index.date == now.date()]
    if len(df_today) < 5:
        return

    # Previous day close
    prev_day_close = round(
        float(df15[df15.index.date < now.date()].iloc[-1]["Close"]), 2
    )

    last_completed_candle_time = df_today.index[-1]

    # -----------------------------
    # ATR
    # -----------------------------
    atr_value = calculate_atr_15m(df_today)
    atr_sample_status = (
        "Enough Sample" if len(df_today) >= ATR_PERIOD + 1 else "Less Sample"
    )

    # -----------------------------
    # VWAP
    # -----------------------------
    vwap_value = calculate_vwap_15m(df_today)

    last_close = float(df_today.iloc[-1]["Close"])
    expansion = round(
        float(df_today.iloc[-1]["High"] - df_today.iloc[-1]["Low"]), 1
    )

    # VWAP position logic (relative, NOT heuristic)
    distance = last_close - vwap_value
    threshold = expansion * 0.15

    if abs(distance) <= threshold:
        vwap_position = "NEAR"
    elif distance > 0:
        vwap_position = "ABOVE"
    else:
        vwap_position = "BELOW"

    basis_time = last_completed_candle_time.strftime("%H:%M")

    # -----------------------------
    # CHOPPINESS (Phase‑1 message)
    # -----------------------------
    if atr_sample_status == "Less Sample":
        choppiness = {
            "state": "Not Classified",
            "message": "Insufficient Volatility Sample",
        }
    else:
        if atr_value <= 18:
            choppiness = {
                "state": "High",
                "message": "Rotational / Mean‑Reversion Likely",
            }
        elif atr_value <= 25:
            choppiness = {
                "state": "Moderate",
                "message": "Expansion Needs Confirmation",
            }
        else:
            choppiness = {
                "state": "Low",
                "message": "Continuation‑Friendly Environment",
            }

    # -----------------------------
    # OUTPUT JSON
    # -----------------------------
    output = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST",
        },
        "nifty": {
            "spot": round(last_close, 2),
            "change_points": round(last_close - prev_day_close, 1),
            "change_percent": round(
                ((last_close - prev_day_close) / prev_day_close) * 100, 2
            ),
        },
        "volatility": {
            "atr": atr_value,
            "sample_status": atr_sample_status,
            "reliable_from": ATR_RELIABLE_FROM,
        },
        "choppiness": choppiness,
        "vwap": {
            "value": vwap_value,
            "position": vwap_position,
            "expansion_range": expansion,
            "midline": "RISING",
            "basis_candle_close": basis_time,
        },
        "market_open": None,
        "trend_architect": {
            "gap_behavior": "CLOSED_BY_1105",
            "major_candle": {
                "size": 32.45,
                "type": "MARUBOZU",
                "direction": "UP",
                "time": "09:35",
            },
            "next_candle_relation": "OPPOSING",
            "effective_time": "11:00 AM",
        },
        "previous_day": {
            "pdh": 24203.25,
            "pdl": 24177.80,
            "pdc": 24188.40,
        },
        "institutional_flows": {
            "fii_today": None,
            "dii_today": None,
            "fii_last_4_days": [None, None, None, None],
            "dii_last_4_days": [None, None, None, None],
        },
    }

    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(output, f, indent=2)

# -----------------------------
# ENTRY
# -----------------------------
if __name__ == "__main__":
    main()
