"""
Dynamic Column Padding 4-Trend Line Engine (🔴 🟡 🔵 🟢)
Formats 4 perfectly aligned monospace columns:
Position words (max 4 chars):
- TRÊN
- DƯỚI
- CHẠM
- K.XĐ
Format per block: f"{color_icon} {pos:<4} {price:<7} ({diff:.1f}%)"
"""

def format_price_level(val):
    if val <= 0:
        return "-------"
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

def format_color_block(close, line_val, color_icon, is_support):
    """
    Formats a single color block with exact padding width:
    col = f"{color_icon} {pos:<4} {price:<7} ({sign}{diff:.1f}%)"
    """
    if line_val is None or line_val <= 0:
        return f"{color_icon} K.XĐ  ------- (---)"

    price_str = format_price_level(line_val)

    if is_support:
        diff_pct = ((close - line_val) / close) * 100.0
        abs_diff = abs(diff_pct)
        if 0.0 <= abs_diff <= 0.5:
            pos_str = "CHẠM"
        elif diff_pct > 0.5:
            pos_str = "TRÊN"
        else:
            pos_str = "DƯỚI"
            
        sign_str = "+" if diff_pct >= 0 else "-"
        diff_val_str = f"{sign_str}{abs_diff:.1f}%"
    else: # Resistance
        diff_pct = ((line_val - close) / close) * 100.0
        abs_diff = abs(diff_pct)
        if 0.0 <= abs_diff <= 0.5:
            pos_str = "CHẠM"
        elif diff_pct > 0.5:
            pos_str = "DƯỚI"
        else:
            pos_str = "TRÊN"
            
        sign_str = "-" if diff_pct >= 0 else "+"
        diff_val_str = f"{sign_str}{abs_diff:.1f}%"

    return f"{color_icon} {pos_str:<4} {price_str:<7} ({diff_val_str})"

def analyze_4_trends(candles):
    """
    Returns 4 aligned color block strings:
    col_blue, col_green, col_red, col_yellow
    """
    if not candles or len(candles) < 15:
        null_block_blue = format_color_block(0, 0, "🔵", True)
        null_block_green = format_color_block(0, 0, "🟢", True)
        null_block_red = format_color_block(0, 0, "🔴", False)
        null_block_yellow = format_color_block(0, 0, "🟡", False)
        return null_block_blue, null_block_green, null_block_red, null_block_yellow

    current_close = candles[-1]["close"]
    
    # 1. Supertrend Nhanh (Blue / Red): ATR 10, Multiplier 3
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0)
    # 2. Supertrend Chậm (Green / Yellow): ATR 15, Multiplier 10
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0)
    
    val_blue = low_fast[-1] if low_fast else 0
    val_red = up_fast[-1] if up_fast else 0
    val_green = low_slow[-1] if low_slow else 0
    val_yellow = up_slow[-1] if up_slow else 0

    col_blue = format_color_block(current_close, val_blue, "🔵", is_support=True)
    col_green = format_color_block(current_close, val_green, "🟢", is_support=True)
    col_red = format_color_block(current_close, val_red, "🔴", is_support=False)
    col_yellow = format_color_block(current_close, val_yellow, "🟡", is_support=False)

    return col_blue, col_green, col_red, col_yellow

def analyze_timeframe(candles):
    return analyze_4_trends(candles)
