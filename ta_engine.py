"""
Action-Based 4-Trend SuperTrend Engine with Explicit Prices & Negative Value Shield
Formats:
- 🔵 Support Near : Trên 🔵 1.580 (+1.2%) / Sắp chạm 🔵 1.580 (+0.3%)
- 🟢 Support Far  : Trên 🟢 1.450 (+9.5%)
- 🔴 Resistance Near : Dưới 🔴 1.630 (-1.5%) / Sắp chạm 🔴 1.630 (-0.2%)
- 🟡 Resistance Far  : Dưới 🟡 1.800 (-12.0%)
Shields against negative price values on 1W/1M by returning 'Chưa xác định'.
"""

def format_price_level(val):
    if val <= 0:
        return None
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

def format_single_line_status(close, line_val, color_icon, is_support):
    if line_val <= 0:
        return f"{color_icon} Chưa xác định"

    price_str = format_price_level(line_val)
    if not price_str:
        return f"{color_icon} Chưa xác định"

    if is_support:
        diff_pct = ((close - line_val) / close) * 100.0
        abs_diff = abs(diff_pct)
        if 0.0 <= abs_diff <= 0.5:
            return f"Sắp chạm {color_icon} {price_str} (+{abs_diff:.1f}%)"
        elif diff_pct > 0.5:
            return f"Trên {color_icon} {price_str} (+{diff_pct:.1f}%)"
        else:
            return f"Dưới {color_icon} {price_str} (-{abs_diff:.1f}%)"
    else: # Resistance
        diff_pct = ((line_val - close) / close) * 100.0
        abs_diff = abs(diff_pct)
        if 0.0 <= abs_diff <= 0.5:
            return f"Sắp chạm {color_icon} {price_str} (-{abs_diff:.1f}%)"
        elif diff_pct > 0.5:
            return f"Dưới {color_icon} {price_str} (-{diff_pct:.1f}%)"
        else:
            return f"Trên {color_icon} {price_str} (+{abs_diff:.1f}%)"

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

    val_blue = low_fast[-1]
    val_red = up_fast[-1]
    val_green = low_slow[-1]
    val_yellow = up_slow[-1]

    blue_str = format_single_line_status(current_close, val_blue, "🔵", is_support=True)
    green_str = format_single_line_status(current_close, val_green, "🟢", is_support=True)
    red_str = format_single_line_status(current_close, val_red, "🔴", is_support=False)
    yellow_str = format_single_line_status(current_close, val_yellow, "🟡", is_support=False)

    res = f"{blue_str}, {green_str} | {red_str}, {yellow_str}"
    return res

def analyze_timeframe(candles):
    return analyze_4_trends(candles)
