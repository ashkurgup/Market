import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

def calculate_atr_15m(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    return round(float(atr.dropna().iloc[-1]), 1)

def main():
    now = datetime.now(IST)

    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)

    df_today = df15[df15.index.date == now.date()]
    if len(df_today) < 5:
        return

    prev_day_close = round(
        float(df15[df15.index.date < now.date()].iloc[-1]["Close"]), 2
    )

    # --- ATR ---
    atr_value = calculate_atr_15m(df_today)
    atr_sample_status = (
        "Enough Sample" if len(df_today) >= ATR_PERIOD + 1 else "Less Sample"
    )

    # --- VWAP basis time (last completed candle) ---
    last_candle_time = df_today.index[-1]
    if now < last_candle_time:
        last_candle_time -= timedelta(minutes=15)

    vwap_basis_time = last_candle_time.strftime("%H:%M")

    expansion = round(
        float(df_today.iloc[-1]["High"] - df_today.iloc[-1]["Low"]), 1
    )

    vwap_block = {
        "position": "NEAR",
        "expansion_range": expansion,
        "midline": "RISING",
        "basis_candle_close": vwap_basis_time
    }

    # --- Choppiness (Phase‑1 message only) ---
    if atr_sample_status == "Less Sample":
        choppiness = {
            "state": "Not Classified",
            "message": "Insufficient Volatility Sample"
        }
    else:
        if atr_value <= 18:
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

    output = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST"
        },
        "nifty": {
            "spot": round(float(df_today.iloc[-1]["Close"]), 2),
            "change_points": round(
                float(df_today.iloc[-1]["Close"] - prev_day_close), 1
            ),
            "change_percent": round(
                ((df_today.iloc[-1]["Close"] - prev_day_close) / prev_day_close) * 100,
                2
            )
        },
        "volatility": {
            "atr": atr_value,
            "sample_status": atr_sample_status,
            "reliable_from": ATR_RELIABLE_FROM
        },
        "choppiness": choppiness,
        "vwap": vwap_block,
        "market_open": None,
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
