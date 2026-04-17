import json
from datetime import datetime
import pytz
import yfinance as yf
import pandas as pd
import numpy as np

# =========================
# TIME
# =========================
IST = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(IST)
TODAY = NOW.date()

OUTPUT_PATH = "snapshots/market_phase1.json"

# =========================
# DATA FETCH
# =========================
def fetch_intraday(interval):
    df = yf.download("^NSEI", interval=interval, period="2d", progress=False)
    df = df.dropna()
    df.index = df.index.tz_localize(None)
    return df

def fetch_nifty_spot():
    t = yf.Ticker("^NSEI")
    info = t.fast_info
    spot = float(info["lastPrice"])
    prev = float(info["previousClose"])
    return spot, round(spot - prev, 2), round((spot - prev) / prev * 100, 2)

# =========================
# PREVIOUS DAY ANCHORS
# =========================
def previous_day_anchors(df):
    prev_rows = df[df.index.date < TODAY]
    if prev_rows.empty:
        return None

    last = prev_rows.iloc[-1]
    return {
        "pdh": float(last["High"]),
        "pdl": float(last["Low"]),
        "pdc": float(last["Close"])
    }

# =========================
# VWAP (15‑MIN)
# =========================
def calculate_vwap_15m(df):
    pv = (df["Close"] * df["Volume"]).cumsum()
    vol = df["Volume"].cumsum()
    return float((pv / vol).iloc[-1])

# =========================
# MARKET OPEN
# =========================
def market_open_logic(df_15, anchors):
    today_df = df_15[df_15.index.date == TODAY]
    opening = today_df.between_time("09:15", "09:30")

    if opening.empty:
        return None

    row = opening.iloc[0]

    open_p  = float(row["Open"])
    high_p  = float(row["High"])
    low_p   = float(row["Low"])
    close_p = float(row["Close"])

    gap_pts = round(open_p - float(anchors["pdc"]), 2)

    if gap_pts > 0:
        gap_type = "GAP UP"
    elif gap_pts < 0:
        gap_type = "GAP DOWN"
    else:
        gap_type = "NO GAP"

    body = abs(close_p - open_p)
    range_ = high_p - low_p
    candle_type = "DOJI" if body <= range_ * 0.20 else "BODY"

    return {
        "gap_status": {
            "type": gap_type,
            "points": gap_pts,
            "frozen_at": "09:20"
        },
        "opening_candle": {
            "type": candle_type,
            "ohlc": {
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p
            },
            "range": round(range_, 2),
            "frozen_at": "09:35"
        }
    }

# =========================
# TREND ARCHITECT (FINAL)
# =========================
def trend_architect(df_5, anchors):
    window = df_5.between_time("09:30", "11:00").copy()
    if window.empty:
        return None

    window["body"] = (window["Close"] - window["Open"]).abs()

    impulse_pos = window["body"].values.argmax()
    impulse = window.iloc[impulse_pos]

    impulse_open = float(impulse["Open"])
    impulse_close = float(impulse["Close"])
    impulse_body = abs(impulse_close - impulse_open)
    impulse_time = impulse.name.strftime("%H:%M")

    relation = "NA"
    if impulse_pos + 1 < len(window):
        nxt = window.iloc[impulse_pos + 1]
        nxt_dir = float(nxt["Close"]) - float(nxt["Open"])
        imp_dir = impulse_close - impulse_open
        relation = "SUPPORTING" if np.sign(nxt_dir) == np.sign(imp_dir) else "OPPOSING"

    lows = df_5.between_time("09:30", "11:05")["Low"].astype(float).values
    gap_closed = bool(np.any(lows <= float(anchors["pdc"])))

    return {
        "gap_behavior": "CLOSED_BY_1105" if gap_closed else "NOT_CLOSED_BY_1105",
        "major_candle": {
            "size": round(impulse_body, 2),
            "type": "MARUBOZU",
            "time": impulse_time
        },
        "next_candle_relation": relation,
        "market_character": "Measured discovery with acceptance",
        "effective_time": "11:00 AM"
    }

# =========================
# MAIN
# =========================
def main():
    df_15 = fetch_intraday("15m")
    df_5 = fetch_intraday("5m")

    spot, chg, pct = fetch_nifty_spot()
    anchors = previous_day_anchors(df_15)
    if not anchors:
        return

    vwap = calculate_vwap_15m(df_15)
    last_close = float(df_15["Close"].tail(1).values[0])

    if last_close > vwap * 1.005:
        vwap_pos = "STRONG ABOVE"
    elif last_close > vwap:
        vwap_pos = "ABOVE"
    elif last_close < vwap * 0.995:
        vwap_pos = "STRONG BELOW"
    else:
        vwap_pos = "NEAR"

    expansion_range = float(
        df_15["High"].tail(1).values[0] -
        df_15["Low"].tail(1).values[0]
    )

    snapshot = {
        "meta": {
            "date": str(TODAY),
            "last_updated": NOW.strftime("%H:%M:%S"),
            "timezone": "IST"
        },
        "nifty": {
            "spot": spot,
            "change_points": chg,
            "change_percent": pct
        },
        "vwap": {
            "position": vwap_pos,
            "expansion_range": round(expansion_range, 1),
            "midline": "RISING"
        },
        "market_open": market_open_logic(df_15, anchors),
        "trend_architect": trend_architect(df_5, anchors),
        "previous_day": anchors,
        "institutional_flows": {
            "status": "AWAITING_INSTITUTIONAL_DATA"
        }
    }

    # FINAL SAFETY CHECK (will raise if anything is unserializable)
    json.dumps(snapshot)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    main()
