"""
4-Trend Line Engine (XANH, TÍM, ĐỎ, CAM)
Calculates exact price position & distance relative to all 4 Trend Lines:
- XANH (Green): Major Support Line (ST1 Lower, ATR 15 / Mult 10)
- TÍM (Purple): Minor Support Line (ST2 Lower, ATR 10 / Mult 3)
- ĐỎ (Red): Major Resistance Line (ST1 Upper, ATR 15 / Mult 10)
- CAM (Orange): Minor Resistance Line (ST2 Upper, ATR 10 / Mult 3)
"""

def calculate_atr(candles, period=15):
    if not candles or len(candles) <= period:
        return []
    try:
        tr_list = []
        for i in range(1, len(candles)):
            high = candles[i]["high"]
            low = candles[i]["low"]
            prev_close = candles[i-1]["close"]
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        if len(tr_list) < period:
            return []
        atr = [sum(tr_list[:period]) / period]
        for tr in tr_list[period:]:
            new_atr = (atr[-1] * (period - 1) + tr) / period
            atr.append(new_atr)
        return atr
    except Exception:
        return []

def calculate_supertrend_bands(candles, atr_period=15, multiplier=10.0):
    """
    Returns upper and lower bands and trend state.
    """
    if not candles or len(candles) <= atr_period + 5:
        return {"upper": 0, "lower": 0, "is_buy": True, "upper_flat": False, "lower_flat": False}
        
    try:
        atr = calculate_atr(candles, atr_period)
        if not atr:
            return {"upper": 0, "lower": 0, "is_buy": True, "upper_flat": False, "lower_flat": False}
            
        offset = len(candles) - len(atr)
        aligned_candles = candles[offset:]
        
        upper_band = []
        lower_band = []
        trend = []

        for i in range(len(atr)):
            c = aligned_candles[i]
            hl2 = (c["high"] + c["low"]) / 2.0
            basic_upper = hl2 + (multiplier * atr[i])
            basic_lower = hl2 - (multiplier * atr[i])
            
            if i == 0:
                upper_band.append(basic_upper)
                lower_band.append(basic_lower)
                trend.append(True)
                continue
                
            prev_close = aligned_candles[i-1]["close"]
            prev_upper = upper_band[i-1]
            prev_lower = lower_band[i-1]
            
            final_upper = basic_upper if (basic_upper < prev_upper or prev_close > prev_upper) else prev_upper
            upper_band.append(final_upper)
            
            final_lower = basic_lower if (basic_lower > prev_lower or prev_close < prev_lower) else prev_lower
            lower_band.append(final_lower)
            
            curr_trend = trend[i-1]
            if curr_trend and c["close"] < final_lower:
                curr_trend = False
            elif not curr_trend and c["close"] > final_upper:
                curr_trend = True
            trend.append(curr_trend)

        upper_flat = False
        lower_flat = False
        if len(upper_band) >= 4:
            if abs(upper_band[-1] - upper_band[-4]) / (upper_band[-1] + 1e-9) < 0.0005:
                upper_flat = True
            if abs(lower_band[-1] - lower_band[-4]) / (lower_band[-1] + 1e-9) < 0.0005:
                lower_flat = True

        return {
            "upper": round(upper_band[-1], 4),
            "lower": round(lower_band[-1], 4),
            "is_buy": trend[-1],
            "upper_flat": upper_flat,
            "lower_flat": lower_flat
        }
    except Exception:
        return {"upper": 0, "lower": 0, "is_buy": True, "upper_flat": False, "lower_flat": False}

def get_4trend_status(candles):
    """
    Evaluates price position against ALL 4 TREND LINES:
    - XANH (Green): ST1 Lower
    - TÍM (Purple): ST2 Lower
    - ĐỎ (Red): ST1 Upper
    - CAM (Orange): ST2 Upper
    """
    if not candles or len(candles) < 20:
        return "Trên cả 4 đường (Xanh, Tím, Đỏ, Cam) 🔥"

    curr_price = candles[-1]["close"]

    # Calculate Major ST (15, 10) -> Green (Lower) & Red (Upper)
    st_maj = calculate_supertrend_bands(candles, atr_period=15, multiplier=10.0)
    line_xanh = st_maj["lower"]
    line_do = st_maj["upper"]

    # Calculate Minor ST (10, 3) -> Purple (Lower) & Orange (Upper)
    st_min = calculate_supertrend_bands(candles, atr_period=10, multiplier=3.0)
    line_tim = st_min["lower"]
    line_cam = st_min["upper"]

    # Testing Flat Level Check (<= 0.4%)
    dist_xanh = abs(curr_price - line_xanh) / curr_price if line_xanh > 0 else 1.0
    dist_tim = abs(curr_price - line_tim) / curr_price if line_tim > 0 else 1.0
    dist_do = abs(curr_price - line_do) / curr_price if line_do > 0 else 1.0
    dist_cam = abs(curr_price - line_cam) / curr_price if line_cam > 0 else 1.0

    if dist_xanh <= 0.004 and st_maj["lower_flat"]:
        return "Chạm Xanh Flat (Hỗ trợ ⭐)"
    if dist_do <= 0.004 and st_maj["upper_flat"]:
        return "Chạm Đỏ Flat (Cản ⚠️)"
    if dist_tim <= 0.004 and st_min["lower_flat"]:
        return "Chạm Tím Flat (Hỗ trợ)"
    if dist_cam <= 0.004 and st_min["upper_flat"]:
        return "Chạm Cam Flat (Cản)"

    # Check Position against all 4 lines
    above_lines = []
    below_lines = []

    if curr_price > line_xanh: above_lines.append("Xanh")
    else: below_lines.append("Xanh")

    if curr_price > line_tim: above_lines.append("Tím")
    else: below_lines.append("Tím")

    if curr_price > line_do: above_lines.append("Đỏ")
    else: below_lines.append("Đỏ")

    if curr_price > line_cam: above_lines.append("Cam")
    else: below_lines.append("Cam")

    # Absolute Confluence
    if len(above_lines) == 4:
        return "Trên cả 4 đường (Xanh, Tím, Đỏ, Cam) 🔥"
    if len(below_lines) == 4:
        return "Dưới cả 4 đường (Xanh, Tím, Đỏ, Cam) 🔻"

    # Squeezed between lines
    above_str = ", ".join(above_lines) if above_lines else "Không"
    below_str = ", ".join(below_lines) if below_lines else "Không"

    return f"Trên {above_str} | Dưới {below_str}"

def analyze_timeframe(candles):
    return get_4trend_status(candles)
