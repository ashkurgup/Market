import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import numpy as np

IST = pytz.timezone("Asia/Kolkata")
ATR_PERIOD = 14
ATR_RELIABLE_FROM = "13:00"

# =============================
# ATR
# =============================
def calculate_atr_15m(df, period=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    pc = c.shift(1)
    tr = pd.concat([
        h - l,
        (h - pc).abs(),
        (l - pc).abs()
    ], axis=1).max(axis=1)
    return round(float(tr.rolling(period).mean().dropna().iloc[-1]), 1)

# =============================
# Candle Classifier (LOCKED)
# =============================
def classify_candle(o, h, l, c):
    rng = h - l
    body = abs(c - o)
    if rng == 0:
        return "DOJI", "NEUTRAL", 0

    body_pct = body / rng
    uw = h - max(o, c)
    lw = min(o, c) - l

    if body == 0:
        return "DOJI", "NEUTRAL", 0

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

# =============================
# Price‑Centric VWAP (LOCKED)
# =============================
def calc_price_vwap(df):
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    mid = tp.mean()
    sd = tp.std() if len(tp) > 1 else 0
    upper = mid + sd
    lower = mid - sd
    return round(mid, 2), round(upper, 2), round(lower, 2), round(upper - lower, 2)

# =============================
# Market Open (LOCKED)
# =============================
def calculate_market_open(df, prev_close):
    c = df.iloc[0]
    o,h,l,cl = map(float,[c["Open"],c["High"],c["Low"],c["Close"]])
    typ,col,bpct = classify_candle(o,h,l,cl)
    gap = round(o - prev_close,2)
    gdir = "FLAT" if abs(gap)<0.25 else ("UP" if gap>0 else "DOWN")

    return {
        "gap": {
            "direction": gdir,
            "points": gap,
            "frozen_at": "09:20 IST"
        },
        "opening_candle": {
            "type": typ,
            "color": col,
            "size": round(abs(cl-o),2),
            "body_pct": bpct,
            "range": round(h-l,2),
            "ohlc": {
                "open": round(o,2),
                "high": round(h,2),
                "low": round(l,2),
                "close": round(cl,2)
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
    df5  = ticker.history(interval="5m", period="1d").tz_convert(IST)

    today = now.date()
    df15_today = df15[df15.index.date == today]
    df5_today  = df5[df5.index.date == today]

    if len(df15_today) < 2 or len(df5_today) < 2:
        return

    prev_close = float(df15[df15.index.date < today].iloc[-1]["Close"])
    last_close = float(df15_today.iloc[-1]["Close"])

    # ATR
    atr = calculate_atr_15m(df15_today)
    atr_sample = "Enough Sample" if len(df15_today) >= ATR_PERIOD+1 else "Less Sample"

    # VWAP
    mid, upper, lower, expansion = calc_price_vwap(df15_today)

    if last_close > upper:
        vpos = "STRONG ABOVE"
    elif last_close > mid:
        vpos = "ABOVE"
    elif last_close >= lower:
        vpos = "NEAR"
    elif last_close >= mid - (upper-mid):
        vpos = "BELOW"
    else:
        vpos = "STRONG BELOW"

    # Market Open
    market_open = calculate_market_open(df15_today, prev_close)

    # =============================
    # TREND ARCHITECT (AUTOMATED)
    # =============================

    df5_window = df5_today.between_time("09:30","11:05")

    # Gap behavior
    gap_closed = any(r["Low"]<=prev_close<=r["High"] for _,r in df5_window.iterrows())
    gap_behavior = {
        "status": "Closed by 11:05" if gap_closed else "Not Closed by 11:05",
        "frozen_at": "11:05 IST"
    }

    # Major candle
    df_mc = df5_today.between_time("09:30","11:00")
    df_mc["range"] = df_mc["High"] - df_mc["Low"]
    mc = df_mc.loc[df_mc["range"].idxmax()]
    mct,mcc,_ = classify_candle(mc["Open"],mc["High"],mc["Low"],mc["Close"])
    major_candle = {
        "range": round(mc["range"],1),
        "type": mct,
        "color": mcc,
        "time": f"{mc.name.strftime('%H:%M')}–{(mc.name+pd.Timedelta(minutes=5)).strftime('%H:%M')}"
    }

    # Next candle
    idx = df5_today.index.get_loc(mc.name)
    if idx+1 < len(df5_today):
        nc = df5_today.iloc[idx+1]
        same = (nc["Close"]>nc["Open"])==(mc["Close"]>mc["Open"])
        next_candle = {
            "relation": "SUPPORTING" if same else "OPPOSING",
            "color": "GREEN" if same else "RED"
        }
    else:
        next_candle = {"relation":"NA","color":"GREY"}

    # Distance + overlap
    o0930 = df5_today.at_time("09:30").iloc[0]["Open"]
    c1105 = df5_today.at_time("11:05").iloc[-1]["Close"]
    dist = round(c1105 - o0930,1)

    overlap = 0
    for i in range(len(df5_window)-1):
        c1,c2 = df5_window.iloc[i],df5_window.iloc[i+1]
        b1l,b1h = sorted([c1["Open"],c1["Close"]])
        b2l,b2h = sorted([c2["Open"],c2["Close"]])
        inter = max(0,min(b1h,b2h)-max(b1l,b2l))
        if abs(c2["Close"]-c2["Open"])>0 and inter/abs(c2["Close"]-c2["Open"])>=0.8:
            overlap+=1

    if overlap>=3:
        character = "Upward movement with frequent overlap — be cautious"
    elif abs(dist)>expansion:
        character = "Steady move with buyer acceptance"
    else:
        character = "Directional bias intact, but higher risk of deep pullback"

    trend_architect = {
        "gap_behavior": gap_behavior,
        "major_candle": major_candle,
        "next_candle": next_candle,
        "distance_travelled": {
            "points": abs(dist),
            "direction": "UP" if dist>0 else "DOWN",
            "overlaps": overlap
        },
        "market_character": character
    }

    out = {
        "meta":{"date":now.strftime("%Y-%m-%d"),"last_updated":now.strftime("%H:%M:%S"),"timezone":"IST"},
        "nifty":{"spot":round(last_close,2),"change_points":round(last_close-prev_close,1),
                 "change_percent":round(((last_close-prev_close)/prev_close)*100,2)},
        "volatility":{"atr":atr,"sample_status":atr_sample,"reliable_from":ATR_RELIABLE_FROM},
        "vwap":{"mid":mid,"upper":upper,"lower":lower,"expansion":expansion,
                "position":vpos,"midline":"RISING","basis_candle_close":df15_today.index[-1].strftime("%H:%M")},
        "market_open":market_open,
        "trend_architect":trend_architect,
        "previous_day":{"pdh":24203.25,"pdl":24177.8,"pdc":24188.4}
    }

    with open("snapshots/market_phase1.json","w") as f:
        json.dump(out,f,indent=2)

if __name__=="__main__":
    main()
