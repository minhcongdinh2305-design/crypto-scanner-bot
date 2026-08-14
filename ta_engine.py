"""
Advanced Technical Analysis (TA) Engine
Modules Included:
1. Double Supertrend (Major: 15/10, Minor: 10/3) + Flat Line & Key S/R Level Detection
2. EMA Expansion (EMA 20 & EMA 50 Crossover & Expansion Force)
3. RSI TueTrading + Multi-Pivot Bullish/Bearish Divergence Detection
4. Squeeze & Breakout Energy Momentum Detection
Robust exception handling & sanitization included!
"""

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average (EMA)."""
    if not prices or len(prices) < period:
        return []
    
    try:
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]
        
        for price in prices[period:]:
            new_ema = (price - ema[-1]) * multiplier + ema[-1]
            ema.append(new_ema)
            
        return ema
    except Exception as e:
        print(f"❌ Error in calculate_ema ({period}): {e}")
        return []

def calculate_atr(candles, period=15):
    """Calculate Average True Range (ATR)."""
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
    except Exception as e:
        print(f"❌ Error in calculate_atr ({period}): {e}")
        return []

def calculate_supertrend(candles, atr_period=15, multiplier=10.0):
    """
    Calculate Supertrend & Flat Line Key Level Detection.
    Returns: {trend, is_buy, value, is_flat, flat_duration, history}
    """
    default_res = {"trend": "NEUTRAL ⚪", "is_buy": False, "value": None, "is_flat": False, "flat_duration": 0, "history": []}
    
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
            
            if basic_upper < prev_upper or prev_close > prev_upper:
                final_upper = basic_upper
            else:
                final_upper = prev_upper
            upper_band.append(final_upper)
            
            if basic_lower > prev_lower or prev_close < prev_lower:
                final_lower = basic_lower
            else:
                final_lower = prev_lower
            lower_band.append(final_lower)
            
            curr_trend = trend[i-1]
            if curr_trend and c["close"] < final_lower:
                curr_trend = False
            elif not curr_trend and c["close"] > final_upper:
                curr_trend = True
            trend.append(curr_trend)
            
            supertrend.append(final_lower if curr_trend else final_upper)

        # Flat Line Detection (Detect key S/R level when ST value is constant over 3-5 candles)
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

        return {
            "trend": "BUY 🟢" if trend[-1] else "SELL 🔴",
            "is_buy": trend[-1],
            "value": round(supertrend[-1], 4) if supertrend else None,
            "is_flat": is_flat,
            "flat_duration": flat_duration,
            "history": supertrend
        }
    except Exception as e:
        print(f"❌ Error in calculate_supertrend (ATR {atr_period}, Mult {multiplier}): {e}")
        return default_res

def analyze_ema_expansion(close_prices):
    """
    Module 2: EMA Expansion (EMA 20 & EMA 50)
    Determines Crossover state and Expansion Force.
    """
    default_res = {"ema20": None, "ema50": None, "ema200": None, "cross": "NONE", "is_expanding": False, "diff": 0}
    
    if not close_prices or len(close_prices) < 50:
        return default_res
        
    try:
        ema20_list = calculate_ema(close_prices, 20)
        ema50_list = calculate_ema(close_prices, 50)
        ema200_list = calculate_ema(close_prices, 200) if len(close_prices) >= 200 else []
        
        if not ema20_list or not ema50_list:
            return default_res

        ema20 = ema20_list[-1]
        ema50 = ema50_list[-1]
        ema200 = ema200_list[-1] if ema200_list else None
        
        # Crossover State
        cross = "NONE"
        if len(ema20_list) >= 3 and len(ema50_list) >= 3:
            if ema20_list[-3] < ema50_list[-3] and ema20_list[-1] >= ema50_list[-1]:
                cross = "GOLDEN CROSS 🔥 (EMA20 Cắt Lên EMA50)"
            elif ema20_list[-3] > ema50_list[-3] and ema20_list[-1] <= ema50_list[-1]:
                cross = "DEATH CROSS ⚠️ (EMA20 Cắt Xuống EMA50)"

        # Expansion Force Calculation abs(EMA20 - EMA50)
        diff_curr = abs(ema20_list[-1] - ema50_list[-1])
        diff_prev1 = abs(ema20_list[-2] - ema50_list[-2])
        diff_prev2 = abs(ema20_list[-3] - ema50_list[-3])
        
        is_expanding = (diff_curr > diff_prev1 > diff_prev2)
        
        return {
            "ema20": round(ema20, 4),
            "ema50": round(ema50, 4),
            "ema200": round(ema200, 4) if ema200 else None,
            "cross": cross,
            "is_expanding": is_expanding,
            "diff": round(diff_curr, 4)
        }
    except Exception as e:
        print(f"❌ Error in analyze_ema_expansion: {e}")
        return default_res

def detect_rsi_divergence(candles, rsi_values):
    """
    Module 3: RSI TueTrading Multi-Pivot Bullish/Bearish Divergence Detection.
    """
    if not candles or not rsi_values or len(candles) < 30 or len(rsi_values) < 30:
        return {"divergence": "NONE", "detail": ""}

    try:
        close_prices = [c["close"] for c in candles]
        rsi_offset = len(close_prices) - len(rsi_values)
        aligned_rsi = [50.0] * rsi_offset + rsi_values
        
        # Find Local Swing Lows (Bottoms)
        price_lows = []
        for i in range(len(close_prices) - 25, len(close_prices) - 2):
            if close_prices[i] <= close_prices[i-1] and close_prices[i] <= close_prices[i+1]:
                if close_prices[i] <= close_prices[i-2] and close_prices[i] <= close_prices[i+2]:
                    price_lows.append((i, close_prices[i], aligned_rsi[i]))

        # Find Local Swing Highs (Tops)
        price_highs = []
        for i in range(len(close_prices) - 25, len(close_prices) - 2):
            if close_prices[i] >= close_prices[i-1] and close_prices[i] >= close_prices[i+1]:
                if close_prices[i] >= close_prices[i-2] and close_prices[i] >= close_prices[i+2]:
                    price_highs.append((i, close_prices[i], aligned_rsi[i]))

        # Bullish Divergence Check
        if len(price_lows) >= 2:
            p1 = price_lows[-2]
            p2 = price_lows[-1]
            if p2[1] < p1[1] and p2[2] > p1[2] + 1.5:
                return {
                    "divergence": "BULLISH DIVERGENCE 💎 (Phân Kỳ Dương Đáy)",
                    "detail": f"Giá tạo Đáy Thấp Hơn ({p2[1]:.2f} < {p1[1]:.2f}) nhưng RSI tạo Đáy Cao Hơn ({p2[2]:.1f} > {p1[2]:.1f})"
                }

        # Bearish Divergence Check
        if len(price_highs) >= 2:
            p1 = price_highs[-2]
            p2 = price_highs[-1]
            if p2[1] > p1[1] and p2[2] < p1[2] - 1.5:
                return {
                    "divergence": "BEARISH DIVERGENCE ⚠️ (Phân Kỳ Âm Đỉnh)",
                    "detail": f"Giá tạo Đỉnh Cao Hơn ({p2[1]:.2f} > {p1[1]:.2f}) nhưng RSI tạo Đỉnh Thấp Hơn ({p2[2]:.1f} < {p1[2]:.1f})"
                }

        return {"divergence": "NONE", "detail": ""}
    except Exception as e:
        print(f"❌ Error in detect_rsi_divergence: {e}")
        return {"divergence": "NONE", "detail": ""}

def calculate_rsi_tuetrading(candles):
    """
    Calculate RSI TueTrading with Signal Line & Energy Breakout Squeeze Detection.
    """
    default_res = {"rsi": 50.0, "signal": 50.0, "status": "Trung tính 🟢", "divergence": "NONE", "squeeze_breakout": False}
    
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
            
        signal_list = calculate_ema(rsi_list, 9)
        curr_rsi = round(rsi_list[-1], 2)
        curr_signal = round(signal_list[-1], 2) if signal_list else curr_rsi
        
        div_info = detect_rsi_divergence(candles, rsi_list)
        
        squeeze_breakout = False
        if len(rsi_list) >= 4:
            if rsi_list[-4] < 52 and rsi_list[-3] < 52 and rsi_list[-1] > 55:
                squeeze_breakout = True

        rsi_status = "Trung tính 🟢"
        if curr_rsi <= 35:
            rsi_status = "QUÁ BÁN 💎 (Vùng Gom Mua Rất Đẹp)"
        elif curr_rsi >= 70:
            rsi_status = "QUÁ MUA ⚠️ (Vùng Chốt Lời / Cảnh Báo)"
        elif curr_rsi > curr_signal:
            rsi_status = "Tăng điểm (Bullish 🟢)"

        return {
            "rsi": curr_rsi,
            "signal": curr_signal,
            "status": rsi_status,
            "divergence": div_info["divergence"],
            "divergence_detail": div_info["detail"],
            "squeeze_breakout": squeeze_breakout
        }
    except Exception as e:
        print(f"❌ Error in calculate_rsi_tuetrading: {e}")
        return default_res

def analyze_timeframe(candles):
    """
    Comprehensive Timeframe Analysis Engine:
    Integrates Double Supertrend Kıvanç EXACT, EMA Expansion, and RSI TueTrading Divergence.
    """
    if not candles or len(candles) < 30:
        return None
        
    try:
        close_prices = [c["close"] for c in candles]
        current_price = close_prices[-1]
        
        # 1. Double Supertrend Kıvanç EXACT
        st_major = calculate_supertrend(candles, atr_period=15, multiplier=10.0) # ST Lớn
        st_minor = calculate_supertrend(candles, atr_period=10, multiplier=3.0)  # ST Nhỏ
        
        # Proximity Check (ST Nhỏ áp sát ST Lớn)
        st_proximity = False
        if st_major["value"] and st_minor["value"]:
            dist_pct = abs(st_minor["value"] - st_major["value"]) / current_price
            if dist_pct <= 0.025:
                st_proximity = True
                
        # 2. EMA Expansion
        ema_info = analyze_ema_expansion(close_prices)
        
        # 3. RSI TueTrading & Divergence
        rsi_tue = calculate_rsi_tuetrading(candles)

        # 4. Master Setup Evaluation Logic
        st_buy_confluence = st_major["is_buy"] and st_minor["is_buy"]
        st_sell_confluence = not st_major["is_buy"] and not st_minor["is_buy"]
        
        score = 50
        reasons = []

        if st_buy_confluence:
            score += 20
            reasons.append("Cả 2 Supertrend (Lớn & Nhỏ) đều XANH")
        elif st_sell_confluence:
            score -= 20
            reasons.append("Cả 2 Supertrend (Lớn & Nhỏ) đều ĐỎ")

        if st_major["is_flat"]:
            if st_major["is_buy"]:
                score += 15
                reasons.append(f"Supertrend Lớn XANH đi ngang Flat ({st_major['flat_duration']} nến) làm Hỗ trợ Đáy Rất Mạnh")
            else:
                score -= 15
                reasons.append(f"Supertrend Lớn ĐỎ đi ngang Flat ({st_major['flat_duration']} nến) làm Cản Kháng Cự Rất Mạnh")

        if ema_info["is_expanding"]:
            score += 10 if (ema_info["ema20"] and current_price > ema_info["ema20"]) else -10
            reasons.append("EMA 20 & EMA 50 đang DÃN RỘNG MẠNH (Lực xu hướng gia tăng)")

        if "BULLISH DIVERGENCE" in rsi_tue["divergence"]:
            score += 20
            reasons.append("Xuất hiện PHÂN KỲ DƯƠNG ĐÁY (Bullish Divergence) cực chuẩn!")
        elif "BEARISH DIVERGENCE" in rsi_tue["divergence"]:
            score -= 20
            reasons.append("Xuất hiện PHÂN KỲ ÂM ĐỈNH (Bearish Divergence) cảnh báo gãy!")

        if rsi_tue["squeeze_breakout"]:
            score += 10
            reasons.append("RSI vừa BỨT PHÁ BUNG NÉN nén lực thành công!")

        # Signal Rating Classification
        rating = "B (BÌNH THƯỜNG)"
        direction = "TRUNG TÍNH ⚪"

        if score >= 80:
            rating = "⭐ TÍN HIỆU A+ (CỰC MẠNH 100%)"
            direction = "LONG CỰC MẠNH 🔥"
        elif score >= 65:
            rating = "🟢 TÍN HIỆU A (MẠNH)"
            direction = "MUA (LONG) 🟢"
        elif score <= 20:
            rating = "⚠️ TÍN HIỆU A+ (CỰC MẠNH 100%)"
            direction = "SHORT CỰC MẠNH 🔻"
        elif score <= 35:
            rating = "🔴 TÍN HIỆU A (MẠNH)"
            direction = "BÁN (SHORT) 🔴"

        return {
            "price": current_price,
            "st_major": st_major,
            "st_minor": st_minor,
            "st_proximity": st_proximity,
            "ema_info": ema_info,
            "rsi_tue": rsi_tue,
            "score": score,
            "rating": rating,
            "direction": direction,
            "reasons": reasons
        }
    except Exception as e:
        print(f"❌ Error in analyze_timeframe: {e}")
        return None
