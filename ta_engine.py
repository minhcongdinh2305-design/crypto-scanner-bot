"""
Advanced Technical Analysis (TA) Engine - Strict Action-Based Signal Filter
Only detects active, clear technical events:
1. Supertrend: Testing Flat S/R level OR Flipped color within last 1-3 candles.
2. EMA: Crossover (last 1-3 candles) OR Steep Expansion Force.
3. RSI: Bullish/Bearish Divergence OR Extreme Zones (<30 / >70).
Neutral / Floating states are strictly ignored!
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
    """
    Supertrend Calculation with Flip Event & Flat Level Detection.
    """
    default_res = {"trend": "NEUTRAL", "is_buy": False, "value": None, "is_flat": False, "flat_duration": 0, "just_flipped": False, "history": []}
    
    if not candles or len(candles) <= atr_period + 5:
        return default_res
        
    try:
        atr = calculate_atr(candles, atr_period)
        if not atr:
            return default_res
            
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

        # Detect Flat Level (constant for 3+ candles)
        is_flat = False
        flat_duration = 1
        if len(supertrend) >= 5:
            last_val = supertrend[-1]
            for idx in range(2, 6):
                if abs(supertrend[-idx] - last_val) / (last_val + 1e-9) < 0.0005:
                    flat_duration += 1
                else:
                    break
            if flat_duration >= 3:
                is_flat = True

        # Detect Flip Event in last 1-3 candles
        just_flipped = False
        if len(trend) >= 4:
            if trend[-1] != trend[-2] or trend[-2] != trend[-3]:
                just_flipped = True

        return {
            "trend": "BUY 🟢" if trend[-1] else "SELL 🔴",
            "is_buy": trend[-1],
            "value": round(supertrend[-1], 4) if supertrend else None,
            "is_flat": is_flat,
            "flat_duration": flat_duration,
            "just_flipped": just_flipped,
            "history": supertrend
        }
    except Exception:
        return default_res

def analyze_ema_expansion(close_prices):
    """
    Strict EMA Action Filter:
    Only flags 'Chớm cắt' (Cross in last 1-3 candles) OR steep expansion force.
    """
    default_res = {"ema20": None, "ema50": None, "cross": "NONE", "is_expanding": False, "direction": "NEUTRAL"}
    
    if not close_prices or len(close_prices) < 50:
        return default_res
        
    try:
        ema20_list = calculate_ema(close_prices, 20)
        ema50_list = calculate_ema(close_prices, 50)
        
        if not ema20_list or not ema50_list or len(ema20_list) < 5:
            return default_res

        ema20 = ema20_list[-1]
        ema50 = ema50_list[-1]
        
        # Detect Recent Crossover (last 1-3 candles)
        cross = "NONE"
        if len(ema20_list) >= 4 and len(ema50_list) >= 4:
            # Golden Cross check
            if (ema20_list[-4] < ema50_list[-4] or ema20_list[-3] < ema50_list[-3]) and ema20_list[-1] >= ema50_list[-1]:
                cross = "GOLDEN"
            # Death Cross check
            elif (ema20_list[-4] > ema50_list[-4] or ema20_list[-3] > ema50_list[-3]) and ema20_list[-1] <= ema50_list[-1]:
                cross = "DEATH"

        # Expansion Force Calculation abs(EMA20 - EMA50)
        diff_curr = abs(ema20_list[-1] - ema50_list[-1])
        diff_prev1 = abs(ema20_list[-2] - ema50_list[-2])
        diff_prev2 = abs(ema20_list[-3] - ema50_list[-3])
        
        # Steep expansion check
        is_expanding = (diff_curr > diff_prev1 > diff_prev2) and (diff_curr / (close_prices[-1] + 1e-9) > 0.005)
        
        direction = "BUY" if ema20 > ema50 else "SELL"
        
        return {
            "ema20": round(ema20, 4),
            "ema50": round(ema50, 4),
            "cross": cross,
            "is_expanding": is_expanding,
            "direction": direction
        }
    except Exception:
        return default_res

def detect_rsi_divergence(candles, rsi_values):
    """
    RSI Multi-Pivot Bullish & Bearish Divergence Detection.
    """
    if not candles or not rsi_values or len(candles) < 30 or len(rsi_values) < 30:
        return "NONE"

    try:
        close_prices = [c["close"] for c in candles]
        rsi_offset = len(close_prices) - len(rsi_values)
        aligned_rsi = [50.0] * rsi_offset + rsi_values
        
        # Find Local Swing Lows
        price_lows = []
        for i in range(len(close_prices) - 25, len(close_prices) - 2):
            if close_prices[i] <= close_prices[i-1] and close_prices[i] <= close_prices[i+1]:
                price_lows.append((i, close_prices[i], aligned_rsi[i]))

        # Find Local Swing Highs
        price_highs = []
        for i in range(len(close_prices) - 25, len(close_prices) - 2):
            if close_prices[i] >= close_prices[i-1] and close_prices[i] >= close_prices[i+1]:
                price_highs.append((i, close_prices[i], aligned_rsi[i]))

        # Bullish Divergence Check
        if len(price_lows) >= 2:
            p1 = price_lows[-2]
            p2 = price_lows[-1]
            if p2[1] < p1[1] and p2[2] > p1[2] + 1.5:
                return "BULLISH"

        # Bearish Divergence Check
        if len(price_highs) >= 2:
            p1 = price_highs[-2]
            p2 = price_highs[-1]
            if p2[1] > p1[1] and p2[2] < p1[2] - 1.5:
                return "BEARISH"

        return "NONE"
    except Exception:
        return "NONE"

def calculate_rsi_tuetrading(candles):
    """
    RSI TueTrading Engine: Divergence OR Extreme Zones (<30 / >70).
    Neutral states (35 - 65) are strictly ignored!
    """
    default_res = {"rsi": 50.0, "divergence": "NONE", "extreme": "NONE"}
    
    if not candles or len(candles) <= 25:
        return default_res
        
    try:
        close_prices = [c["close"] for c in candles]
        gains = []
        losses = []
        for i in range(1, len(close_prices)):
            change = close_prices[i] - close_prices[i-1]
            gains.append(change if change > 0 else 0)
            losses.append(abs(change) if change < 0 else 0)
            
        period = 14
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_list = []
        if avg_loss == 0:
            rsi_list.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_list.append(100.0 - (100.0 / (1.0 + rs)))
            
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            rsi = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
            rsi_list.append(rsi)
            
        curr_rsi = round(rsi_list[-1], 2)
        div = detect_rsi_divergence(candles, rsi_list)
        
        extreme = "NONE"
        if curr_rsi <= 30:
            extreme = "OVERSOLD" # Quá bán
        elif curr_rsi >= 70:
            extreme = "OVERBOUGHT" # Quá mua

        return {
            "rsi": curr_rsi,
            "divergence": div,
            "extreme": extreme
        }
    except Exception:
        return default_res

def analyze_timeframe(candles):
    """
    Strict Timeframe Action Filter Engine.
    Returns structured events for Trend, EMA, and RSI.
    """
    if not candles or len(candles) < 30:
        return None
        
    try:
        st_major = calculate_supertrend(candles, atr_period=15, multiplier=10.0)
        ema_info = analyze_ema_expansion([c["close"] for c in candles])
        rsi_tue = calculate_rsi_tuetrading(candles)

        return {
            "st_major": st_major,
            "ema_info": ema_info,
            "rsi_tue": rsi_tue
        }
    except Exception:
        return None
