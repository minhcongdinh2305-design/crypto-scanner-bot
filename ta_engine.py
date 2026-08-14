"""
Technical Analysis (TA) Calculation Engine
Pure Python Implementation for RSI, EMA, MACD, Stochastic RSI
Zero external dependency required!
"""

def calculate_ema(prices, period):
    """Calculate Exponential Moving Average (EMA)."""
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    # Start with SMA for the first EMA value
    ema = [sum(prices[:period]) / period]
    
    for price in prices[period:]:
        new_ema = (price - ema[-1]) * multiplier + ema[-1]
        ema.append(new_ema)
        
    return ema

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (RSI)."""
    if len(prices) <= period:
        return []
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
            
    # Initial Average Gain/Loss
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
        
        if avg_loss == 0:
            rsi_list.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_list.append(100.0 - (100.0 / (1.0 + rs)))
            
    return rsi_list

def calculate_macd(prices, fast=12, slow=26, signal_period=9):
    """Calculate Moving Average Convergence Divergence (MACD)."""
    if len(prices) < slow + signal_period:
        return None
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    # Align starting points (ema_fast is longer than ema_slow)
    offset = slow - fast
    macd_line = [f - s for f, s in zip(ema_fast[offset:], ema_slow)]
    
    signal_line = calculate_ema(macd_line, signal_period)
    
    if not signal_line:
        return None
        
    histogram = macd_line[-1] - signal_line[-1]
    
    return {
        "macd": macd_line[-1],
        "signal": signal_line[-1],
        "histogram": histogram,
        "is_bullish": macd_line[-1] > signal_line[-1]
    }

def analyze_timeframe(candles):
    """
    Analyzes candles for a specific timeframe (15m, 1h, 4h, 1d).
    Returns dict with RSI, EMA status, MACD, and overall Signal.
    """
    if not candles or len(candles) < 50:
        return None
        
    close_prices = [c["close"] for c in candles]
    current_price = close_prices[-1]
    
    # Calculate RSI
    rsi_values = calculate_rsi(close_prices, 14)
    current_rsi = round(rsi_values[-1], 2) if rsi_values else 50.0
    
    # RSI Condition
    rsi_status = "Trung tính 🟢"
    if current_rsi <= 30:
        rsi_status = "QUÁ BÁN 💎 (Mua đẹp)"
    elif current_rsi <= 40:
        rsi_status = "Vùng Mua 🟢"
    elif current_rsi >= 70:
        rsi_status = "QUÁ MUA ⚠️ (Nên chốt)"
    elif current_rsi >= 60:
        rsi_status = "Vùng Bán 🔴"

    # Calculate EMAs (20, 50, 200)
    ema20_list = calculate_ema(close_prices, 20)
    ema50_list = calculate_ema(close_prices, 50)
    ema200_list = calculate_ema(close_prices, 200) if len(close_prices) >= 200 else []
    
    ema20 = ema20_list[-1] if ema20_list else current_price
    ema50 = ema50_list[-1] if ema50_list else current_price
    ema200 = ema200_list[-1] if ema200_list else None
    
    # EMA Trend Evaluation
    ema_trend = "Sideways ⚪"
    if current_price > ema20 > ema50:
        ema_trend = "Uptrend Mạnh 🚀"
    elif current_price > ema20:
        ema_trend = "Uptrend 🟢"
    elif current_price < ema20 < ema50:
        ema_trend = "Downtrend Mạnh 📉"
    elif current_price < ema20:
        ema_trend = "Downtrend 🔴"
        
    # EMA Cross Check (Recent 3 candles)
    ema_cross = "Không"
    if len(ema20_list) >= 3 and len(ema50_list) >= 3:
        if ema20_list[-3] < ema50_list[-3] and ema20_list[-1] > ema50_list[-1]:
            ema_cross = "GOLDEN CROSS (Cắt lên) 🔥"
        elif ema20_list[-3] > ema50_list[-3] and ema20_list[-1] < ema50_list[-1]:
            ema_cross = "DEATH CROSS (Cắt xuống) ⚠️"

    # MACD Calculation
    macd = calculate_macd(close_prices)
    macd_status = "Trung tính"
    if macd:
        if macd["is_bullish"]:
            macd_status = "Tăng điểm (Bullish 🟢)"
        else:
            macd_status = "Giảm điểm (Bearish 🔴)"

    return {
        "price": current_price,
        "rsi": current_rsi,
        "rsi_status": rsi_status,
        "ema20": round(ema20, 4),
        "ema50": round(ema50, 4),
        "ema200": round(ema200, 4) if ema200 else "N/A",
        "ema_trend": ema_trend,
        "ema_cross": ema_cross,
        "macd_status": macd_status
    }
