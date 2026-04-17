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
# ATR (unchanged)
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
# Candle classifier (LOCKED logic)
# =====================================================
def classify_candle(o, h, l, c):
    rng = h - l
    body = abs(c - o)

    if rng == 0:
        return "DOJI", "NEUTRAL", 0

    body_pct = body / rng
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    if body == 0:
        return "DOJI", "NEUTRAL", 0

    color = "GREEN" if c > o else "RED"

    if body_pct >= 0.80:
        return "MARUBOZU", color, round(body_pct * 100)

    if lower_wick >= 2 * body and upper_wick <= 0.25 * body:
        return "HAMMER", color, round(body_pct * 100)

    if upper_wick >= 2 * body and lower_wick <= 0.25 * body:
        return "INVERTED HAMMER", color, round(body_pct * 100)

    if 0.15 <= body_pct < 0.40 and upper_wick > body and lower_wick > body:
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
    expansion = upper - lower
    return round(mid, 2), round(upper, 2), round(lower, 2), round(expansion, 2)

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

    if len(df15_today) < 2 or len(df5_today) < 2:
        return

    prev_day_df = df15[df15.index.date < today]
    prev_close = float(prev_day_df.iloc[-1]["Close"])
    last_close = float(df15_today.iloc[-1]["Close"])

    # ---------------- ATR ----------------
    atr = calculate_atr_15m(df15_today)
    atr_sample = "Enough Sample" if len(df15_today) >= ATR_PERIOD + 1 else "Less Sample"

    # ---------------- VWAP ----------------
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

    # ---------------- Market Open ----------------
    market_open = calculate_market_open(df15_today, prev_close)

    # ================= TREND ARCHITECT =================
    if now_time <= TREND_FREEZE_TIME:
        df5_window = df5_today.between_time("09:30", "11:05")

        # Gap behavior
        gap_closed = any(
            r["Low"] <= prev_close <= r["High"] for _, r in df5_window.iterrows()
        )

        gap_behavior = {
            "status": "Closed by 11:05" if gap_closed else "Not Closed by 11:05",
            "frozen_at": "11:05 IST"
        }

        # Major candle
        df_mc = df5_today.between_time("09:30", "11:00")
        df_mc = df_mc[df_mc.index.strftime("%H:%M") != "09:30"]
        df_mc["range"] = df_mc["High"] - df_mc["Low"]
        mc = df_mc.loc[df_mc["range"].idxmax()]
        mctype, mccolor, _ = classify_candle(mc["Open"], mc["High"], mc["Low"], mc["Close"])

        major_candle = {
            "range": round(mc["range"], 1),
            "type": mctype,
            "color": mccolor,
            "time": f"{mc.name.strftime('%H:%M')}–{(mc.name + timedelta(minutes=5)).strftime('%H:%M')}"
        }

        # Next candle
        idx = df5_today.index.get_loc(mc.name)
        if idx + 1 < len(df5_today):
            nc = df5_today.iloc[idx + 1]
            same = (nc["Close"] > nc["Open"]) == (mc["Close"] > mc["Open"])
            next_candle = {
                "relation": "SUPPORTING" if same else "OPPOSING",
                "color": "GREEN" if same else "RED"
            }
        else:
            next_candle = {"relation": "NA", "color": "GREY"}

        # Distance + overlap
        open_0930 = df5_today.at_time("09:30").iloc[0]["Open"]
        close_1105 = df5_today.at_time("11:05").iloc[-1]["Close"]
        dist = round(close_1105 - open_0930, 1)

        overlap = 0
        candles = df5_window
        for i in range(len(candles) - 1):
            c1, c2 = candles.iloc[i], candles.iloc[i + 1]
            b1l, b1h = sorted([c1["Open"], c1["Close"]])
            b2l, b2h = sorted([c2["Open"], c2["Close"]])
            intersection = max(0, min(b1h, b2h) - max(b1l, b2l))
            body2 = abs(c2["Close"] - c2["Open"])
            if body2 > 0 and intersection / body2 >= 0.8:
                overlap += 1

        if overlap >= 3:
            character = "Upward movement with frequent overlap — be cautious"
        elif abs(dist) > expansion:
            character = "Steady move with buyer acceptance"
        else:
            character = "Directional bias intact, but higher risk of deep pullback"

        trend_architect = {
            "gap_behavior": gap_behavior,
            "major_candle": major_candle,
            "next_candle": next_candle,
            "distance_travelled": {
                "points": abs(dist),
                "direction": "UP" if dist > 0 else "DOWN",
                "overlaps": overlap
            },
            "market_character": character
        }
    else:
        # after 11:05 → freeze
        try:
            with open("snapshots/market_phase1.json", "r") as f:
                trend_architect = json.load(f).get("trend_architect")
        except:
            trend_architect = None

    # ================= PREVIOUS DAY ANCHORS =================
    if now_time >= ANCHOR_UPDATE_TIME:
        pdh = round(df15_today["High"].max(), 2)
        pdl = round(df15_today["Low"].min(), 2)
        pdc = round(df15_today.iloc[-1]["Close"], 2)
    else:
        try:
            with open("snapshots/market_phase1.json", "r") as f:
                prev = json.load(f).get("previous_day", {})
                pdh, pdl, pdc = prev["pdh"], prev["pdl"], prev["pdc"]
        except:
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
        "trend_architect": trend_architect,
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
