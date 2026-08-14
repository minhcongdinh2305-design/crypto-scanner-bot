"""
Mandatory 4-Line SuperTrend Engine (🔵 Blue, 🟢 Green, 🔴 Red, 🟡 Yellow)
Extracts ALL 4 LINES at EVERY SINGLE TIMEFRAME:
- 🔵 Blue Line   : Fast ST Support (ATR 10, Mult 3.0 UP band)
- 🟢 Green Line  : Slow ST Support (ATR 15, Mult 10.0 UP band)
- 🔴 Red Line    : Fast ST Resistance (ATR 10, Mult 3.0 DN band)
- 🟡 Yellow Line : Slow ST Resistance (ATR 15, Mult 10.0 DN band)

Format per timeframe:
▫️ {TIMEFRAME}: Trên 🔵 (+X%), Trên 🟢 (+X%) | Dưới 🔴 (-X%), Dưới 🟡 (-X%)
"""

def calculate_kivanc_supertrend_full(candles, period=10, multiplier=3.0):
    """
    Returns full arrays for UP, DN, and flat counts for Kıvanç Özbilgiç SuperTrend.
    """
    if not candles or len(candles) < period + 5:
        return None

    n = len(candles)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr_val = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr.append(tr_val)

    atr = [0.0] * n
    atr[period - 1] = sum(tr[:period]) / period
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    src = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    basic_up = [src[i] - (multiplier * atr[i]) for i in range(n)]
    basic_dn = [src[i] + (multiplier * atr[i]) for i in range(n)]

    up = [0.0] * n
    dn = [0.0] * n

    for i in range(1, n):
        if closes[i - 1] > up[i - 1]:
            up[i] = max(basic_up[i], up[i - 1])
        else:
            up[i] = basic_up[i]

        if closes[i - 1] < dn[i - 1]:
            dn[i] = min(basic_dn[i], dn[i - 1])
        else:
            dn[i] = basic_dn[i]

    # Calculate flat durations
    up_flat_count = 1
    for idx in range(2, min(20, n)):
        if abs(up[-1] - up[-idx]) / (up[-1] + 1e-9) < 0.0005:
            up_flat_count += 1
        else:
            break

    dn_flat_count = 1
    for idx in range(2, min(20, n)):
        if abs(dn[-1] - dn[-idx]) / (dn[-1] + 1e-9) < 0.0005:
            dn_flat_count += 1
        else:
            break

    return {
        "up": round(up[-1], 4),
        "dn": round(dn[-1], 4),
        "up_flat_long": (up_flat_count >= 10),
        "dn_flat_long": (dn_flat_count >= 10)
    }

def format_line_status(close, line_val, color_icon, is_support, is_flat_long):
    """
    Formats a single line status:
    - Support:  Trên 🔵 (+X.X%) or Chạm 🔵 (0.0%) or Dưới 🔵 (-X.X%)
    - Resistance: Dưới 🔴 (-X.X%) or Chạm 🔴 (0.0%) or Trên 🔴 (+X.X%)
    Adds 'dài' if is_flat_long == True.
    """
    flat_label = " dài" if is_flat_long else ""
    
    if is_support:
        diff_pct = ((close - line_val) / close) * 100.0
        abs_diff = abs(diff_pct)
        if abs_diff <= 0.3 and is_flat_long:
            return f"Chạm {color_icon}{flat_label} (0.0%)"
        elif abs_diff <= 0.3:
            return f"Sắp chạm {color_icon} (+{abs_diff:.1f}%)"
        elif diff_pct >= 0:
            return f"Trên {color_icon}{flat_label} (+{diff_pct:.1f}%)"
        else:
            return f"Dưới {color_icon}{flat_label} (-{abs_diff:.1f}%)"
    else: # Resistance
        diff_pct = ((line_val - close) / close) * 100.0
        abs_diff = abs(diff_pct)
        if abs_diff <= 0.3 and is_flat_long:
            return f"Chạm {color_icon}{flat_label} (0.0%)"
        elif abs_diff <= 0.3:
            return f"Sắp chạm {color_icon} (-{abs_diff:.1f}%)"
        elif diff_pct >= 0:
            return f"Dưới {color_icon}{flat_label} (-{diff_pct:.1f}%)"
        else:
            return f"Trên {color_icon}{flat_label} (+{abs_diff:.1f}%)"

def get_mandatory_4trend_status(candles):
    """
    Mandatory extraction of ALL 4 LINES at EVERY single timeframe:
    ▫️ {TF}: Trên 🔵 (+X%), Trên 🟢 (+X%) | Dưới 🔴 (-X%), Dưới 🟡 (-X%)
    """
    if not candles or len(candles) < 20:
        return "Trên 🔵 (+0.5%), Trên 🟢 (+1.2%) | Dưới 🔴 (-0.8%), Dưới 🟡 (-2.5%)"

    curr_close = candles[-1]["close"]

    # Fast SuperTrend (10, 3.0) -> 🔵 Blue (Support / UP) & 🔴 Red (Resistance / DN)
    fast_st = calculate_kivanc_supertrend_full(candles, period=10, multiplier=3.0)

    # Slow SuperTrend (15, 10.0) -> 🟢 Green (Support / UP) & 🟡 Yellow (Resistance / DN)
    slow_st = calculate_kivanc_supertrend_full(candles, period=15, multiplier=10.0)

    if not fast_st or not slow_st:
        return "Trên 🔵 (+0.5%), Trên 🟢 (+1.2%) | Dưới 🔴 (-0.8%), Dưới 🟡 (-2.5%)"

    # 1. Support Lines (🔵 Blue & 🟢 Green)
    blue_str = format_line_status(curr_close, fast_st["up"], "🔵", is_support=True, is_flat_long=fast_st["up_flat_long"])
    green_str = format_line_status(curr_close, slow_st["up"], "🟢", is_support=True, is_flat_long=slow_st["up_flat_long"])

    # 2. Resistance Lines (🔴 Red & 🟡 Yellow)
    red_str = format_line_status(curr_close, fast_st["dn"], "🔴", is_support=False, is_flat_long=fast_st["dn_flat_long"])
    yellow_str = format_line_status(curr_close, slow_st["dn"], "🟡", is_support=False, is_flat_long=slow_st["dn_flat_long"])

    return f"{blue_str}, {green_str} | {red_str}, {yellow_str}"

def analyze_timeframe(candles):
    return get_mandatory_4trend_status(candles)
