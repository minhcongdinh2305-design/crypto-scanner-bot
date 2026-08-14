"""
100% Exact TradingView Pine Script v4 Supertrend Implementation (KivancOzbilgic)

Pine Script v4 Logic:
Periods = 10 / 15
Multiplier = 3.0 / 10.0
changeATR = true -> TradingView RMA (Wilder's Smoothing)

atr = changeATR ? rma(tr, Periods) : sma(tr, Periods)
up = src - (Multiplier * atr)
up1 = nz(up[1], up)
up := close[1] > up1 ? max(up, up1) : up
dn = src + (Multiplier * atr)
dn1 = nz(dn[1], dn)
dn := close[1] < dn1 ? min(dn, dn1) : dn
trend = 1
trend := trend == -1 and close > dn1 ? 1 : trend == 1 and close < up1 ? -1 : trend
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

    # 2. ATR Calculation (Pine Script atr(period) = RMA(tr, period) if change_atr else SMA(tr, period))
    atr = [0.0] * n
    if change_atr:
        # TradingView RMA (Wilder's Smoothing)
        if n >= period:
            atr[period - 1] = sum(tr[:period]) / float(period)
            for i in range(period, n):
                atr[i] = (atr[i-1] * (period - 1) + tr[i]) / float(period)
    else:
        # Simple Moving Average
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

        # up := close[1] > up1 ? max(up, up1) : up
        if closes[i-1] > prev_lower:
            lowerband[i] = max(up[i], prev_lower)
        else:
            lowerband[i] = up[i]

        # dn := close[1] < dn1 ? min(dn, dn1) : dn
        if closes[i-1] < prev_upper:
            upperband[i] = min(dn[i], prev_upper)
        else:
            upperband[i] = dn[i]

        # trend := trend == -1 and close > dn1 ? 1 : trend == 1 and close < up1 ? -1 : trend
        prev_trend = trend[i-1]
        if prev_trend == -1 and closes[i] > prev_upper:
            trend[i] = 1
        elif prev_trend == 1 and closes[i] < prev_lower:
            trend[i] = -1
        else:
            trend[i] = prev_trend

    return lowerband, upperband, trend

def format_color_block(close, line_val, color_icon, is_support):
    """
    Formats a single color block with exact padding width:
    col = f"{color_icon} {pos:<4} {price:<7} ({diff_str})"
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
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0, change_atr=True)
    # 2. Supertrend Chậm (Green / Yellow): ATR 15, Multiplier 10
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0, change_atr=True)
    
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
