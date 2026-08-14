"""
100% Real Binance Data SuperTrend Engine with Explicit Price Levels
Format per timeframe:
▫️ 4H : 🔵 1.580 (+1.2%), 🟢 1.450 (+9.5%) | 🔴 1.630 (-1.5%), 🟡 1.800 (-12.0%)
"""

def format_price_level(val):
    if val >= 1000:
        return f"{val:.1f}"
    elif val >= 1:
        return f"{val:.3f}"
    elif val >= 0.01:
        return f"{val:.4f}"
    else:
        return f"{val:.6f}"

def calculate_supertrend(candles, period=10, multiplier=3.0):
    if not candles or len(candles) < period + 5:
        return None, None, None

    n = len(candles)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    hl2 = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    
    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr_val = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr.append(tr_val)

    atr = [0.0] * n
    for i in range(period - 1, n):
        atr[i] = sum(tr[i - period + 1 : i + 1]) / period

    up = [hl2[i] - (multiplier * atr[i]) for i in range(n)]
    dn = [hl2[i] + (multiplier * atr[i]) for i in range(n)]

    upperband = list(dn)
    lowerband = list(up)
    trend = [1] * n

    for i in range(1, n):
        if closes[i-1] > upperband[i-1]:
            upperband[i] = max(dn[i], upperband[i-1]) if closes[i] > upperband[i-1] else dn[i]
        else:
            upperband[i] = min(dn[i], upperband[i-1]) if closes[i] < upperband[i-1] else dn[i]

        if closes[i-1] < lowerband[i-1]:
            lowerband[i] = min(up[i], lowerband[i-1]) if closes[i] < lowerband[i-1] else up[i]
        else:
            lowerband[i] = max(up[i], lowerband[i-1]) if closes[i] > lowerband[i-1] else up[i]

        if closes[i] > upperband[i-1]:
            trend[i] = 1
        elif closes[i] < upperband[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
            if trend[i] == 1 and lowerband[i] < lowerband[i-1]:
                lowerband[i] = lowerband[i-1]
            if trend[i] == -1 and upperband[i] > upperband[i-1]:
                upperband[i] = upperband[i-1]

    return lowerband, upperband, trend

def analyze_4_trends(candles):
    if not candles or len(candles) < 15:
        return "Chưa đủ dữ liệu nến"

    current_close = candles[-1]["close"]
    
    # 1. Supertrend Nhanh (Blue / Red): ATR 10, Multiplier 3
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0)
    # 2. Supertrend Chậm (Green / Yellow): ATR 15, Multiplier 10
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0)
    
    if not low_fast or not low_slow or not up_fast or not up_slow:
        return "Chưa đủ dữ liệu nến"

    # Last price level values
    val_blue = low_fast[-1]
    val_red = up_fast[-1]
    val_green = low_slow[-1]
    val_yellow = up_slow[-1]
    
    # Percentage distance calculations
    diff_blue = ((current_close - val_blue) / current_close) * 100.0
    diff_green = ((current_close - val_green) / current_close) * 100.0
    diff_red = ((val_red - current_close) / current_close) * 100.0
    diff_yellow = ((val_yellow - current_close) / current_close) * 100.0
    
    # Formatted price levels
    p_blue = format_price_level(val_blue)
    p_green = format_price_level(val_green)
    p_red = format_price_level(val_red)
    p_yellow = format_price_level(val_yellow)

    res = f"🔵 {p_blue} (+{diff_blue:.1f}%), 🟢 {p_green} (+{diff_green:.1f}%) | 🔴 {p_red} (-{diff_red:.1f}%), 🟡 {p_yellow} (-{diff_yellow:.1f}%)"
    return res

def analyze_timeframe(candles):
    return analyze_4_trends(candles)
