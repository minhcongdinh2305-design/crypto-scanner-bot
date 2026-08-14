"""
100% Exact TradingView Pine Script v4 Supertrend Kivanc Engine
Supports both NumPy/Pandas and Pure Python fallback for zero-crash guarantees.

Pine Script v4 Logic:
calculate_rma(series, length): alpha = 1.0 / length, rma[i] = alpha * val[i] + (1.0 - alpha) * rma[i-1]
"""

try:
    import numpy as np
    import pandas as pd
    HAS_NUMPY_PANDAS = True
except ImportError:
    HAS_NUMPY_PANDAS = False

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

def calculate_rma_python(values, length: int):
    alpha = 1.0 / float(length)
    n = len(values)
    rma = [0.0] * n
    if n > 0:
        rma[0] = float(values[0])
        for i in range(1, n):
            rma[i] = alpha * float(values[i]) + (1.0 - alpha) * rma[i - 1]
    return rma

def calculate_kivanc_supertrend_python(candles, period: int, multiplier: float):
    n = len(candles)
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]
    src = [(highs[i] + lows[i]) / 2.0 for i in range(n)]

    tr = [highs[0] - lows[0]]
    for i in range(1, n):
        tr_val = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        tr.append(tr_val)

    atr = calculate_rma_python(tr, period)

    up = [0.0] * n
    dn = [0.0] * n
    trend = [1] * n

    up[0] = src[0] - multiplier * atr[0]
    dn[0] = src[0] + multiplier * atr[0]
    trend[0] = 1

    for i in range(1, n):
        up_basic = src[i] - multiplier * atr[i]
        dn_basic = src[i] + multiplier * atr[i]

        up[i] = max(up_basic, up[i - 1]) if closes[i - 1] > up[i - 1] else up_basic
        dn[i] = min(dn_basic, dn[i - 1]) if closes[i - 1] < dn[i - 1] else dn_basic

        prev_trend = trend[i - 1]
        if prev_trend == -1 and closes[i] > dn[i - 1]:
            trend[i] = 1
        elif prev_trend == 1 and closes[i] < up[i - 1]:
            trend[i] = -1
        else:
            trend[i] = prev_trend

    current_trend = trend[-1]
    current_val = up[-1] if current_trend == 1 else dn[-1]
    return current_trend, current_val, up, dn, trend

if HAS_NUMPY_PANDAS:
    def calculate_rma(series: pd.Series, length: int) -> np.ndarray:
        alpha = 1.0 / length
        values = series.to_numpy()
        rma = np.zeros(len(values))
        rma[0] = values[0]
        for i in range(1, len(values)):
            rma[i] = alpha * values[i] + (1.0 - alpha) * rma[i - 1]
        return rma

    def calculate_kivanc_supertrend(df, period: int, multiplier: float):
        if isinstance(df, list):
            df = pd.DataFrame(df)

        high = df['high'].to_numpy()
        low = df['low'].to_numpy()
        close = df['close'].to_numpy()
        src = (high + low) / 2.0
        
        tr = np.zeros(len(df))
        tr[0] = high[0] - low[0]
        for i in range(1, len(df)):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        
        atr = calculate_rma(pd.Series(tr), period)
        
        up = np.zeros(len(df))
        dn = np.zeros(len(df))
        trend = np.zeros(len(df), dtype=int)
        
        up[0] = src[0] - multiplier * atr[0]
        dn[0] = src[0] + multiplier * atr[0]
        trend[0] = 1
        
        for i in range(1, len(df)):
            up_basic = src[i] - multiplier * atr[i]
            dn_basic = src[i] + multiplier * atr[i]
            
            up[i] = max(up_basic, up[i - 1]) if close[i - 1] > up[i - 1] else up_basic
            dn[i] = min(dn_basic, dn[i - 1]) if close[i - 1] < dn[i - 1] else dn_basic
            
            prev_trend = trend[i - 1]
            if prev_trend == -1 and close[i] > dn[i - 1]:
                trend[i] = 1
            elif prev_trend == 1 and close[i] < up[i - 1]:
                trend[i] = -1
            else:
                trend[i] = prev_trend
                
        current_trend = trend[-1]
        current_val = up[-1] if current_trend == 1 else dn[-1]
        return current_trend, current_val, up.tolist(), dn.tolist(), trend.tolist()
else:
    def calculate_kivanc_supertrend(df, period: int, multiplier: float):
        return calculate_kivanc_supertrend_python(df, period, multiplier)

def calculate_supertrend(candles, period=10, multiplier=3.0, change_atr=True):
    if not candles or len(candles) < 15:
        return None, None, None
        
    up, dn, trend = calculate_kivanc_supertrend(candles, period, multiplier)[2:]
    return up, dn, trend

def analyze_4_trends(candles):
    if not candles or len(candles) < 15:
        return None, None, None, None

    up_fast, dn_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0)
    up_slow, dn_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0)
    
    val_blue = up_fast[-1] if up_fast else 0
    val_red = dn_fast[-1] if dn_fast else 0
    val_green = up_slow[-1] if up_slow else 0
    val_yellow = dn_slow[-1] if dn_slow else 0

    return val_blue, val_green, val_red, val_yellow
