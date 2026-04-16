import json
from datetime import datetime, time
import pytz
import yfinance as yf
import pandas as pd

IST = pytz.timezone("Asia/Kolkata")
NOW = datetime.now(IST)
TODAY = NOW.date()

OUTPUT_PATH = "snapshots/market_phase1.json"

# =======================
# FETCH DATA
# =======================

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

# =======================
# PREVIOUS DAY ANCHORS
# =======================

def previous_day_anchors(df):
    prev_day = df[df.index.date < TODAY].iloc[-1]
    return {
        "pdh": round(prev_day["High"], 2),
        "pdl": round(prev_day["Low"], 2),
        "pdc": round(prev_day["Close"], 2)
    }

# =======================
# VWAP (15 MIN)
# =======================

def vwap_15m(df_15):
    pv = (df_15["Close"] * df_15["Volume"]).cumsum()
    vol = df_15["Volume"].cumsum()
    return float((pv / vol).iloc[-1])

# =======================
# MARKET OPEN
# =======================

def market_open_logic(df_15, anchors):
    today_df = df_15[df_15.index.date == TODAY]
    open_candle = today_df.between_time("09:15", "09:30").iloc[0]

    gap_pts = round(open_candle["Open"] - anchors["pdc"], 2)
    gap_type = "NO GAP"
    if gap_pts > 0:
        gap_type = "GAP UP"
    elif gap_pts < 0:
        gap_type = "GAP DOWN"

    return {
        "gap_status": {
            "type": gap_type,
            "points": gap_pts,
            "frozen_at": "09:20"
        },
        "opening_candle": {
            "type": "DOJI" if abs(open_candle["Close"] - open_candle["Open"]) < (open_candle["High"] - open_candle["Low"]) * 0.2 else "BODY",
            "ohlc": {
                "open": round(open_candle["Open"], 2),
                "high": round(open_candle["High"], 2),
                "low": round(open_candle["Low"], 2),
                "close": round(open_candle["Close"], 2)
            },
            "range": round(open_candle["High"] - open_candle["Low"], 2),
            "frozen_at": "09:35"
        }
    }

# =======================
# TREND ARCHITECT
# =======================

def trend_architect(df_5, anchors):
    window = df_5.between_time("09:30", "11:00")
    window["body"] = abs(window["Close"] - window["Open"])

    impulse = window.loc[window["body"].idxmax()]
    idx = window.index.get_loc(impulse.name)

    if idx + 1 < len(window):
        next_candle = window.iloc[idx + 1]
        relation = (
            "SUPPORTING" if (next_candle["Close"] - next_candle["Open"]) * (impulse["Close"] - impulse["Open"]) > 0
            else "OPPOSING"
        )
    else:
        relation = "NA"

    gap_closed = any(df_5.between_time("09:30", "11:05")["Low"] <= anchors["pdc"])

    return {
        "gap_behavior": "CLOSED_BY_1105" if gap_closed else "NOT_CLOSED_BY_1105",
        "major_candle": {
            "size": round(impulse["body"], 2),
            "type": "MARUBOZU" if impulse["High"] == max(impulse["Open"], impulse["Close"]) and impulse["Low"] == min(impulse["Open"], impulse["Close"]) else "BODY",
            "time": impulse.name.strftime("%H:%M")
        },
        "next_candle_relation": relation,
        "market_character": "Measured discovery with acceptance",
        "effective_time": "11:00 AM"
    }

# =======================
# MAIN
# =======================

def main():
    df_15 = fetch_intraday("15m")
    df_5 = fetch_intraday("5m")

    spot, chg, pct = fetch_nifty_spot()
    anchors = previous_day_anchors(df_15)

    vwap = vwap_15m(df_15)
    last_price = float(df_15["Close"].iloc[-1])

    if last_price > vwap * 1.005:
        vwap_pos = "STRONG ABOVE"
    elif last_price > vwap:
        vwap_pos = "ABOVE"
    elif last_price < vwap * 0.995:
        vwap_pos = "STRONG BELOW"
    else:
        vwap_pos = "NEAR"

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
            "expansion_range": round(df_15["High"].iloc[-1] - df_15["Low"].iloc[-1], 1),
            "midline": "RISING"
        },
        "market_open": market_open_logic(df_15, anchors),
        "trend_architect": trend_architect(df_5, anchors),
        "previous_day": anchors,
        "institutional_flows": {
            "status": "AWAITING_INSTITUTIONAL_DATA"
        }
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)

if __name__ == "__main__":
    main()
