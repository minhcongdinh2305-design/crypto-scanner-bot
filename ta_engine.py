"""
100% Exact TradingView Pine Script v4 Supertrend Kivanc Engine
Fast ST: ATR 10, Multiplier 3.0
Slow ST: ATR 15, Multiplier 10.0
Source: hl2, RMA Wilder's ATR Calculation
"""

def format_price_level(val):
    if val is None or val <= 0:
        return "-------"
    if val >= 1000:
        return f"{val:.1f}"
    elif val >= 1:
        return f"{val:.3f}"
    elif val >= 0.01:
        return f"{val:.4f}"
    else:
        return f"{val:.6f}"

def calculate_supertrend(candles, period=10, multiplier=3.0, change_atr=True):
    if not candles or len(candles) < period + 5:
        return None, None, None

    n = len(candles)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    hl2 = [(highs[i] + lows[i]) / 2.0 for i in range(n)]

    # 1. True Range (TR)
    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr_val = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr.append(tr_val)

    # 2. ATR Calculation (TradingView RMA Wilder's Smoothing)
    atr = [0.0] * n
    if change_atr:
        if n >= period:
            atr[period - 1] = sum(tr[:period]) / float(period)
            for i in range(period, n):
                atr[i] = (atr[i-1] * (period - 1) + tr[i]) / float(period)
    else:
        for i in range(period - 1, n):
            atr[i] = sum(tr[i - period + 1 : i + 1]) / float(period)

    # 3. Basic Up & Dn bands
    up = [hl2[i] - (multiplier * atr[i]) for i in range(n)]
    dn = [hl2[i] + (multiplier * atr[i]) for i in range(n)]

    upperband = [0.0] * n
    lowerband = [0.0] * n
    trend = [1] * n

    upperband[0] = dn[0]
    lowerband[0] = up[0]

    for i in range(1, n):
        prev_lower = lowerband[i-1]
        prev_upper = upperband[i-1]

        if closes[i-1] > prev_lower:
            lowerband[i] = max(up[i], prev_lower)
        else:
            lowerband[i] = up[i]

        if closes[i-1] < prev_upper:
            upperband[i] = min(dn[i], prev_upper)
        else:
            upperband[i] = dn[i]

        prev_trend = trend[i-1]
        if prev_trend == -1 and closes[i] > prev_upper:
            trend[i] = 1
        elif prev_trend == 1 and closes[i] < prev_lower:
            trend[i] = -1
        else:
            trend[i] = prev_trend

    return lowerband, upperband, trend

def analyze_4_trends(candles):
    if not candles or len(candles) < 15:
        return None, None, None, None

    current_close = candles[-1]["close"]
    
    # 1. Supertrend Nhanh (Blue / Red): ATR 10, Multiplier 3.0
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0, change_atr=True)
    # 2. Supertrend Chậm (Green / Yellow): ATR 15, Multiplier 10.0
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0, change_atr=True)
    
    val_blue = low_fast[-1] if low_fast else 0
    val_red = up_fast[-1] if up_fast else 0
    val_green = low_slow[-1] if low_slow else 0
    val_yellow = up_slow[-1] if up_slow else 0

    return val_blue, val_green, val_red, val_yellow
