"""
Ultra-Fast Pure Supertrend Engine (Double Supertrend: Major 15/10, Minor 10/3)
Zero EMA, Zero RSI. Focus 100% on Trend Key Levels & Flat Line S/R.
Execution speed: < 0.1s!
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

def calculate_supertrend(candles, atr_period=15, multiplier=10.0):
    if not candles or len(candles) <= atr_period + 5:
        return {"is_buy": True, "value": 0, "is_flat": False, "dist_pct": 0.0, "just_flipped": False}
        
    try:
        atr = calculate_atr(candles, atr_period)
        if not atr:
            return {"is_buy": True, "value": 0, "is_flat": False, "dist_pct": 0.0, "just_flipped": False}
            
        offset = len(candles) - len(atr)
        aligned_candles = candles[offset:]
        
        upper_band = []
        lower_band = []
        trend = []
        supertrend = []

        for i in range(len(atr)):
            c = aligned_candles[i]
            hl2 = (c["high"] + c["low"]) / 2.0
            basic_upper = hl2 + (multiplier * atr[i])
            basic_lower = hl2 - (multiplier * atr[i])
            
            if i == 0:
                upper_band.append(basic_upper)
                lower_band.append(basic_lower)
                trend.append(True)
                supertrend.append(basic_lower)
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
            
            supertrend.append(final_lower if curr_trend else final_upper)

        curr_price = aligned_candles[-1]["close"]
        st_val = supertrend[-1]
        dist_pct = abs(curr_price - st_val) / (curr_price + 1e-9)

        is_flat = False
        if len(supertrend) >= 4:
            if abs(supertrend[-1] - supertrend[-4]) / (st_val + 1e-9) < 0.0005:
                is_flat = True

        just_flipped = False
        if len(trend) >= 3:
            if trend[-1] != trend[-2] or trend[-2] != trend[-3]:
                just_flipped = True

        return {
            "is_buy": trend[-1],
            "value": st_val,
            "is_flat": is_flat,
            "dist_pct": dist_pct,
            "just_flipped": just_flipped
        }
    except Exception:
        return {"is_buy": True, "value": 0, "is_flat": False, "dist_pct": 0.0, "just_flipped": False}

def get_trend_status(candles):
    """
    Evaluates 1 timeframe and produces single crisp Trend Status string:
    - Chạm Xanh Flat ⭐ (distance <= 0.5% & Flat)
    - Chạm Đỏ Flat ⚠️ (distance <= 0.5% & Flat)
    - Vừa đổi màu Xanh 🚀 (flipped to Buy in last 1-2 candles)
    - Vừa đổi màu Đỏ 🔻 (flipped to Sell in last 1-2 candles)
    - Cách xa Trend Xanh / Đỏ (distance > 2.5%)
    - Nằm trên Trend Xanh / Nằm dưới Trend Đỏ
    """
    if not candles or len(candles) < 20:
        return "Nằm trên Trend Xanh"

    st_major = calculate_supertrend(candles, atr_period=15, multiplier=10.0)
    st_minor = calculate_supertrend(candles, atr_period=10, multiplier=3.0)

    is_buy = st_major["is_buy"]
    dist_pct = st_major["dist_pct"]
    is_flat = st_major["is_flat"]
    just_flipped = st_major["just_flipped"] or st_minor["just_flipped"]

    if just_flipped:
        return "Vừa đổi màu Xanh 🚀" if is_buy else "Vừa đổi màu Đỏ 🔻"

    if dist_pct <= 0.005:
        if is_buy:
            return "Chạm Xanh Flat ⭐" if is_flat else "Chạm Trend Xanh"
        else:
            return "Chạm Đỏ Flat ⚠️" if is_flat else "Chạm Trend Đỏ"

    if dist_pct > 0.025:
        return "Cách xa Trend Xanh" if is_buy else "Cách xa Trend Đỏ"

    return "Nằm trên Trend Xanh" if is_buy else "Nằm dưới Trend Đỏ"

def analyze_timeframe(candles):
    return get_trend_status(candles)
