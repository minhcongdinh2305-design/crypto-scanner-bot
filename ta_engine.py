"""
Multi-Timeframe Status Engine (30M, 1H, 2H, 4H, 8H, 12H, 1D, 1W, 1M)
Generates direct status strings per timeframe separated by '|':
{Trend Status} | {EMA Status} | {RSI Status}
"""

def calculate_ema(prices, period):
    if not prices or len(prices) < period:
        return []
    try:
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]
        for price in prices[period:]:
            new_ema = (price - ema[-1]) * multiplier + ema[-1]
            ema.append(new_ema)
        return ema
    except Exception:
        return []

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
        return {"is_buy": True, "value": 0, "is_flat": False, "dist_pct": 0.0, "history": []}
        
    try:
        atr = calculate_atr(candles, atr_period)
        if not atr:
            return {"is_buy": True, "value": 0, "is_flat": False, "dist_pct": 0.0, "history": []}
            
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

        return {
            "is_buy": trend[-1],
            "value": st_val,
            "is_flat": is_flat,
            "dist_pct": dist_pct,
            "history": supertrend
        }
    except Exception:
        return {"is_buy": True, "value": 0, "is_flat": False, "dist_pct": 0.0, "history": []}

def calculate_rsi_list(close_prices, period=14):
    if not close_prices or len(close_prices) <= period:
        return []
    try:
        gains, losses = [], []
        for i in range(1, len(close_prices)):
            chg = close_prices[i] - close_prices[i-1]
            gains.append(chg if chg > 0 else 0)
            losses.append(abs(chg) if chg < 0 else 0)
            
        avg_g = sum(gains[:period]) / period
        avg_l = sum(losses[:period]) / period
        rsi_list = []
        rsi_list.append(100.0 if avg_l == 0 else 100.0 - (100.0 / (1.0 + (avg_g / avg_l))))
        for i in range(period, len(gains)):
            avg_g = (avg_g * (period - 1) + gains[i]) / period
            avg_l = (avg_l * (period - 1) + losses[i]) / period
            rsi_list.append(100.0 if avg_l == 0 else 100.0 - (100.0 / (1.0 + (avg_g / avg_l))))
        return rsi_list
    except Exception:
        return []

def get_timeframe_status_row(candles):
    """
    Evaluates 1 timeframe and produces:
    (trend_status, ema_status, rsi_status)
    """
    if not candles or len(candles) < 20:
        return "Nằm trên Trend Xanh", "EMA dính chùm", "RSI trung tính (50.0)"

    close_prices = [c["close"] for c in candles]
    curr_price = close_prices[-1]

    # 1. TREND STATUS
    st = calculate_supertrend(candles, atr_period=15, multiplier=10.0)
    color = "Xanh" if st["is_buy"] else "Đỏ"
    
    if st["dist_pct"] <= 0.005:
        if st["is_flat"]:
            trend_status = f"Chạm Trend {color} flat"
        else:
            trend_status = f"Chạm Trend {color}"
    elif st["dist_pct"] > 0.02:
        trend_status = f"Cách xa Trend {color}"
    else:
        if st["is_buy"]:
            trend_status = "Nằm trên Trend Xanh"
        else:
            trend_status = "Nằm dưới Trend Đỏ"

    # 2. EMA STATUS
    ema20 = calculate_ema(close_prices, 20)
    ema50 = calculate_ema(close_prices, 50)
    
    ema_status = "EMA dính chùm"
    if ema20 and ema50 and len(ema20) >= 4 and len(ema50) >= 4:
        e20_curr, e50_curr = ema20[-1], ema50[-1]
        diff_curr = abs(e20_curr - e50_curr)
        diff_prev1 = abs(ema20[-2] - ema50[-2])
        diff_prev2 = abs(ema20[-3] - ema50[-3])
        dist_ratio = diff_curr / (curr_price + 1e-9)

        # Crossover check
        if (ema20[-4] < ema50[-4] or ema20[-3] < ema50[-3]) and e20_curr >= e50_curr:
            ema_status = "EMA chớm cắt lên"
        elif (ema20[-4] > ema50[-4] or ema20[-3] > ema50[-3]) and e20_curr <= e50_curr:
            ema_status = "EMA chớm cắt xuống"
        elif dist_ratio > 0.015 and (diff_curr > diff_prev1 > diff_prev2):
            ema_status = "EMA mở rộng lên" if e20_curr > e50_curr else "EMA mở rộng xuống"
        elif dist_ratio <= 0.005:
            ema_status = "EMA dính chùm"
        else:
            ema_status = "EMA dốc lên" if e20_curr > e50_curr else "EMA dốc xuống"

    # 3. RSI STATUS
    rsi_list = calculate_rsi_list(close_prices, 14)
    curr_rsi = round(rsi_list[-1], 1) if rsi_list else 50.0

    rsi_status = f"RSI trung tính ({curr_rsi})"
    
    # Check RSI 50 crossover
    if len(rsi_list) >= 3:
        if rsi_list[-3] < 50 and rsi_list[-1] >= 50:
            rsi_status = f"RSI cắt lên 50 ({curr_rsi})"
        elif rsi_list[-3] > 50 and rsi_list[-1] <= 50:
            rsi_status = f"RSI cắt xuống 50 ({curr_rsi})"

    # Divergence check
    if len(close_prices) >= 30 and len(rsi_list) >= 30:
        rsi_offset = len(close_prices) - len(rsi_list)
        aligned_rsi = [50.0] * rsi_offset + rsi_list
        
        price_lows = []
        for i in range(len(close_prices) - 25, len(close_prices) - 2):
            if close_prices[i] <= close_prices[i-1] and close_prices[i] <= close_prices[i+1]:
                price_lows.append((i, close_prices[i], aligned_rsi[i]))

        price_highs = []
        for i in range(len(close_prices) - 25, len(close_prices) - 2):
            if close_prices[i] >= close_prices[i-1] and close_prices[i] >= close_prices[i+1]:
                price_highs.append((i, close_prices[i], aligned_rsi[i]))

        if len(price_lows) >= 2 and price_lows[-1][1] < price_lows[-2][1] and price_lows[-1][2] > price_lows[-2][2] + 1.5:
            rsi_status = f"RSI phân kỳ tăng ({curr_rsi})"
        elif len(price_highs) >= 2 and price_highs[-1][1] > price_highs[-2][1] and price_highs[-1][2] < price_highs[-2][2] - 1.5:
            rsi_status = f"RSI phân kỳ giảm ({curr_rsi})"

    if curr_rsi <= 30.0:
        rsi_status = f"RSI quá bán ({curr_rsi})"
    elif curr_rsi >= 70.0:
        rsi_status = f"RSI quá mua ({curr_rsi})"

    return trend_status, ema_status, rsi_status

def analyze_timeframe(candles):
    """Fallback compatibility method for single TF analysis."""
    return get_timeframe_status_row(candles)
