import json
import pandas as pd
import yfinance as yf
from datetime import datetime, time, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

TREND_FREEZE_TIME = time(11, 5)
ANCHOR_UPDATE_TIME = time(15, 45)

# =====================================================
# ATR
# =====================================================
def calculate_atr_15m(df, period=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([
        h - l,
        (h - pc).abs(),
        (l - pc).abs()
    ], axis=1).max(axis=1)
    return round(float(tr.rolling(period).mean().dropna().iloc[-1]), 1)

# =====================================================
# Candle classifier (LOCKED)
# =====================================================
def classify_candle(o, h, l, c):
    rng = h - l
    body = abs(c - o)
    if rng == 0 or body == 0:
        return "DOJI", "NEUTRAL", 0

    body_pct = body / rng
    uw = h - max(o, c)
    lw = min(o, c) - l
    color = "GREEN" if c > o else "RED"

    if body_pct >= 0.80:
        return "MARUBOZU", color, round(body_pct * 100)
    if lw >= 2 * body and uw <= 0.25 * body:
        return "HAMMER", color, round(body_pct * 100)
    if uw >= 2 * body and lw <= 0.25 * body:
        return "INVERTED HAMMER", color, round(body_pct * 100)
    if 0.15 <= body_pct < 0.40 and uw > body and lw > body:
        return "SPINNING TOP", color, round(body_pct * 100)

    return "OTHER", color, round(body_pct * 100)

# =====================================================
# Price‑centric VWAP (LOCKED)
# =====================================================
def calculate_price_vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    mid = tp.mean()
    sd = tp.std() if len(tp) > 1 else 0.0
    upper = mid + sd
    lower = mid - sd
    return round(mid, 2), round(upper, 2), round(lower, 2), round(upper - lower, 2)

# =====================================================
# Market Open (LOCKED)
# =====================================================
def calculate_market_open(df_today, prev_close):
    c = df_today.iloc[0]
    o, h, l, cl = map(float, [c["Open"], c["High"], c["Low"], c["Close"]])
    typ, col, body_pct = classify_candle(o, h, l, cl)
    gap = round(o - prev_close, 2)
    gdir = "FLAT" if abs(gap) < 0.25 else ("UP" if gap > 0 else "DOWN")

    return {
        "gap": {
            "direction": gdir,
            "points": gap,
            "frozen_at": "09:20 IST"
        },
        "opening_candle": {
            "type": typ,
            "color": col,
            "size": round(abs(cl - o), 2),
            "body_pct": body_pct,
            "range": round(h - l, 2),
            "ohlc": {
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(cl, 2)
            },
            "frozen_at": "09:35 IST"
        }
    }

# =====================================================
# MAIN
# =====================================================
def main():
    now = datetime.now(IST)
    now_time = now.time()
    today = now.date()

    ticker = yf.Ticker("^NSEI")
    df15 = ticker.history(interval="15m", period="2d").tz_convert(IST)
    df5  = ticker.history(interval="5m", period="1d").tz_convert(IST)

    df15_today = df15[df15.index.date == today]
    df5_today  = df5[df5.index.date == today]

    if len(df15_today) < 2:
        return

    prev_day_df = df15[df15.index.date < today]
    prev_close = float(prev_day_df.iloc[-1]["Close"])
    last_close = float(df15_today.iloc[-1]["Close"])

    # ATR
    atr = calculate_atr_15m(df15_today)
    atr_sample = "Enough Sample" if len(df15_today) >= ATR_PERIOD + 1 else "Less Sample"

    # VWAP
    mid, upper, lower, expansion = calculate_price_vwap(df15_today)
    if last_close > upper:
        vpos = "STRONG ABOVE"
    elif last_close > mid:
        vpos = "ABOVE"
    elif last_close >= lower:
        vpos = "NEAR"
    elif last_close >= mid - (upper - mid):
        vpos = "BELOW"
    else:
        vpos = "STRONG BELOW"

    # ✅ CHOPPINESS (RESTORED — THIS WAS MISSING)
    if atr_sample == "Less Sample":
        choppiness = {
            "state": "Not Classified",
            "message": "Insufficient Volatility Sample"
        }
    else:
        if expansion < atr:
            choppiness = {
                "state": "High",
                "message": "Rotational / Mean‑Reversion Likely"
            }
        elif expansion < atr * 1.5:
            choppiness = {
                "state": "Moderate",
                "message": "Expansion Needs Confirmation"
            }
        else:
            choppiness = {
                "state": "Low",
                "message": "Continuation‑Friendly Environment"
            }

    market_open = calculate_market_open(df15_today, prev_close)

    # ===== PREVIOUS DAY ANCHORS =====
    if now_time >= ANCHOR_UPDATE_TIME:
        pdh = round(df15_today["High"].max(), 2)
        pdl = round(df15_today["Low"].min(), 2)
        pdc = round(df15_today.iloc[-1]["Close"], 2)
    else:
        pdh = round(prev_day_df["High"].max(), 2)
        pdl = round(prev_day_df["Low"].min(), 2)
        pdc = round(prev_close, 2)

    out = {
        "meta": {
            "date": now.strftime("%Y-%m-%d"),
            "last_updated": now.strftime("%H:%M:%S"),
            "timezone": "IST"
        },
        "nifty": {
            "spot": round(last_close, 2),
            "change_points": round(last_close - prev_close, 1),
            "change_percent": round(((last_close - prev_close) / prev_close) * 100, 2)
        },
        "volatility": {
            "atr": atr,
            "sample_status": atr_sample,
            "reliable_from": ATR_RELIABLE_FROM
        },
        "choppiness": choppiness,
        "vwap": {
            "mid": mid,
            "upper": upper,
            "lower": lower,
            "expansion": expansion,
            "position": vpos,
            "midline": "RISING",
            "basis_candle_close": df15_today.index[-1].strftime("%H:%M")
        },
        "market_open": market_open,
        "previous_day": {
            "pdh": pdh,
            "pdl": pdl,
            "pdc": pdc
        }
    }

    with open("snapshots/market_phase1.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    main()
