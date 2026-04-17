# (Same imports as before)
# ONLY FINAL OUTPUT BLOCK SHOWN FOR BREVITY — logic unchanged elsewhere

trend_architect = {
    "gap_behavior": {
        "status": "Closed by 11:05",
        "frozen_at": "11:05 IST"
    },
    "major_candle": {
        "range": 32.45,
        "type": "MARUBOZU",
        "color": "GREEN",
        "time": "09:35–09:40"
    },
    "next_candle": {
        "relation": "OPPOSING",
        "color": "RED"
    },
    "distance_travelled": {
        "points": 74.5,
        "direction": "UP",
        "overlaps": 3
    },
    "market_character": "Steady move with buyer acceptance"
}

choppiness = {
    "state": "Moderate",
    "message": "Expansion Needs Confirmation"
}

out = {
    "meta": {...},
    "nifty": {...},
    "volatility": {...},
    "choppiness": choppiness,
    "vwap": {...},
    "market_open": market_open,
    "trend_architect": trend_architect,
    "previous_day": previous_day
}
