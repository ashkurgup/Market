def calculate_atr_15m(df, period=14):
    """
    Calculate 14‑period ATR on 15‑minute candles.
    Phase‑1 safe: simple TR, simple moving average.
    """
    high = df['High']
    low = df['Low']
    close = df['Close']

    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    # Return latest completed ATR
    return round(float(atr.dropna().iloc[-1]), 1)
