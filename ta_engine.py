"""
100% Exact Kıvanç Özbilgiç SuperTrend Engine (Pure Python - Zero PIP Dependencies Required)
PINE SCRIPT LOGIC:
- src = (high + low) / 2
- up = src - (Multiplier * atr)
- up := close[1] > up[1] ? max(up, up[1]) : up
- dn = src + (Multiplier * atr)
- dn := close[1] < dn[1] ? min(dn, dn[1]) : dn
- trend := trend == -1 and close > dn[1] ? 1 : trend == 1 and close < up[1] ? -1 : trend

2 SuperTrends:
1. Fast ST (ATR=10, Mult=3.0):
   - trend == 1  => XANH (Green Support)
   - trend == -1 => ĐỎ (Red Resistance)
2. Slow ST (ATR=15, Mult=10.0):
   - trend == 1  => TÍM (Purple Support)
   - trend == -1 => CAM (Orange Resistance)
"""

def calculate_kivanc_supertrend(candles, period=10, multiplier=3.0):
    """
    Translates KivancOzbilgic Pine Script SuperTrend 100% accurately in Pure Python.
    """
    if not candles or len(candles) < period + 5:
        return None

    n = len(candles)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]

    # Calculate True Range (TR)
    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr_val = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        tr.append(tr_val)

    # Wilder's Smoothing ATR
    atr = [0.0] * n
    atr[period - 1] = sum(tr[:period]) / period
    for i in range(period, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    src = [(highs[i] + lows[i]) / 2.0 for i in range(n)]
    basic_up = [src[i] - (multiplier * atr[i]) for i in range(n)]
    basic_dn = [src[i] + (multiplier * atr[i]) for i in range(n)]

    up = [0.0] * n
    dn = [0.0] * n
    trend = [1] * n

    for i in range(1, n):
        # Calculate UP (Support line when bullish)
        if closes[i - 1] > up[i - 1]:
            up[i] = max(basic_up[i], up[i - 1])
        else:
            up[i] = basic_up[i]

        # Calculate DN (Resistance line when bearish)
        if closes[i - 1] < dn[i - 1]:
            dn[i] = min(basic_dn[i], dn[i - 1])
        else:
            dn[i] = basic_dn[i]

        # Calculate Trend Switch
        prev_trend = trend[i - 1]
        if prev_trend == -1 and closes[i] > dn[i - 1]:
            trend[i] = 1
        elif prev_trend == 1 and closes[i] < up[i - 1]:
            trend[i] = -1
        else:
            trend[i] = prev_trend

    active_line = up[-1] if trend[-1] == 1 else dn[-1]
    prev_active = up[-4] if trend[-4] == 1 else dn[-4]
    
    is_flat = False
    if abs(active_line - prev_active) / (active_line + 1e-9) < 0.0005:
        is_flat = True

    return {
        "up": round(up[-1], 4),
        "dn": round(dn[-1], 4),
        "trend": trend[-1],  # 1 for Buy, -1 for Sell
        "active_line": round(active_line, 4),
        "is_flat": is_flat,
        "dist_pct": abs(closes[-1] - active_line) / (closes[-1] + 1e-9)
    }

def get_kivanc_4trend_status(candles):
    """
    Evaluates price position & distance relative to Kıvanç Özbilgiç 4-Trend Lines:
    - XANH (Fast ST Buy = Support)
    - ĐỎ   (Fast ST Sell = Resistance)
    - TÍM  (Slow ST Buy = Support)
    - CAM  (Slow ST Sell = Resistance)
    """
    if not candles or len(candles) < 20:
        return "Trên Xanh, Tím | Dưới Đỏ, Cam"

    curr_price = candles[-1]["close"]

    # Fast SuperTrend (10, 3.0) -> Xanh (Buy) / Đỏ (Sell)
    fast_st = calculate_kivanc_supertrend(candles, period=10, multiplier=3.0)
    
    # Slow SuperTrend (15, 10.0) -> Tím (Buy) / Cam (Sell)
    slow_st = calculate_kivanc_supertrend(candles, period=15, multiplier=10.0)

    if not fast_st or not slow_st:
        return "Trên Xanh, Tím | Dưới Đỏ, Cam"

    # Identify Active Lines & Colors
    fast_color = "Xanh" if fast_st["trend"] == 1 else "Đỏ"
    fast_line = fast_st["active_line"]
    
    slow_color = "Tím" if slow_st["trend"] == 1 else "Cam"
    slow_line = slow_st["active_line"]

    # Inactive bands (opposing side lines)
    fast_opp_color = "Đỏ" if fast_st["trend"] == 1 else "Xanh"
    fast_opp_line = fast_st["dn"] if fast_st["trend"] == 1 else fast_st["up"]

    slow_opp_color = "Cam" if slow_st["trend"] == 1 else "Tím"
    slow_opp_line = slow_st["dn"] if slow_st["trend"] == 1 else slow_st["up"]

    # Flat testing check (distance <= 0.4%)
    if fast_st["dist_pct"] <= 0.004 and fast_st["is_flat"]:
        return f"Chạm {fast_color} Flat ({'Hỗ trợ ⭐' if fast_st['trend']==1 else 'Cản ⚠️'})"
        
    if slow_st["dist_pct"] <= 0.004 and slow_st["is_flat"]:
        return f"Chạm {slow_color} Flat ({'Hỗ trợ ⭐' if slow_st['trend']==1 else 'Cản ⚠️'})"

    # Evaluate relative positions for all 4 lines (Xanh, Tím, Đỏ, Cam)
    lines_dict = {
        fast_color: fast_line,
        slow_color: slow_line,
        fast_opp_color: fast_opp_line,
        slow_opp_color: slow_opp_line
    }

    above = []
    below = []
    
    # Enforce standard order: Xanh, Tím, Đỏ, Cam
    for color in ["Xanh", "Tím", "Đỏ", "Cam"]:
        val = lines_dict.get(color, curr_price)
        if curr_price >= val:
            above.append(color)
        else:
            below.append(color)

    # Confluence Check
    if len(above) == 4:
        return "Trên cả 4 đường (Xanh, Tím, Đỏ, Cam) 🔥"
    if len(below) == 4:
        return "Dưới cả 4 đường (Xanh, Tím, Đỏ, Cam) 🔻"

    above_str = ", ".join(above) if above else "Không"
    below_str = ", ".join(below) if below else "Không"

    return f"Trên {above_str} | Dưới {below_str}"

def analyze_timeframe(candles):
    return get_kivanc_4trend_status(candles)
