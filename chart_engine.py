"""
Visual Chart Rendering Engine (TradingView Dark Theme Style)
Renders high-resolution Candlestick charts with:
- Main Subplot: OHLCV Candlesticks + Double Supertrend + EMA 20 & EMA 50
- Lower Subplot: RSI(14) with 30, 50, 70 Reference Levels
Saves temporary PNG image: chart_{symbol}_{tf}.png
"""
import os
from ta_engine import calculate_ema, calculate_supertrend, calculate_rsi_tuetrading

def generate_chart_image(symbol, interval, candles):
    """
    Renders TradingView Dark Theme Candlestick chart and saves temporary PNG.
    Returns path to saved PNG image or None if failed.
    """
    if not candles or len(candles) < 30:
        return None

    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend for server environments
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import Rectangle
        import datetime

        # Take last 120 candles for broad trend view
        candles_subset = candles[-120:]
        close_prices = [c["close"] for c in candles_subset]
        
        # Calculate Indicators
        ema20 = calculate_ema(close_prices, 20)
        ema50 = calculate_ema(close_prices, 50)
        st_major = calculate_supertrend(candles_subset, atr_period=15, multiplier=10.0)
        st_minor = calculate_supertrend(candles_subset, atr_period=10, multiplier=3.0)
        rsi_data = calculate_rsi_tuetrading(candles_subset)
        
        # Setup Figure with 2 Subplots (Price 75%, RSI 25%)
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(
            2, 1, 
            figsize=(12, 7), 
            dpi=150, 
            gridspec_kw={'height_ratios': [3, 1]},
            facecolor='#131722'
        )
        ax1.set_facecolor('#131722')
        ax2.set_facecolor('#131722')

        # X-axis indices
        indices = list(range(len(candles_subset)))
        
        # Plot Candlesticks
        for i, c in enumerate(candles_subset):
            open_p, high_p, low_p, close_p = c["open"], c["high"], c["low"], c["close"]
            color = '#089981' if close_p >= open_p else '#F23645'
            
            # High-Low Wick line
            ax1.plot([i, i], [low_p, high_p], color=color, linewidth=1.2)
            
            # Open-Close Body rectangle
            body_bottom = min(open_p, close_p)
            body_height = max(abs(close_p - open_p), (high_p - low_p) * 0.001)
            rect = Rectangle((i - 0.35, body_bottom), 0.7, body_height, facecolor=color, edgecolor=color)
            ax1.add_patch(rect)

        # Align EMA arrays
        offset20 = len(indices) - len(ema20)
        if len(ema20) > 0:
            ax1.plot(indices[offset20:], ema20, color='#2962FF', linewidth=1.5, label='EMA 20')
            
        offset50 = len(indices) - len(ema50)
        if len(ema50) > 0:
            ax1.plot(indices[offset50:], ema50, color='#FF6D00', linewidth=1.5, label='EMA 50')

        # Supertrend Major & Minor Lines
        if st_major["history"] and len(st_major["history"]) > 0:
            st_maj_color = '#00E676' if st_major["is_buy"] else '#FF5252'
            st_maj_offset = len(indices) - len(st_major["history"])
            ax1.plot(indices[st_maj_offset:], st_major["history"], color=st_maj_color, linewidth=2.0, linestyle='--', label='ST Major (15,10)')

        if st_minor["history"] and len(st_minor["history"]) > 0:
            st_min_color = '#00E5FF' if st_minor["is_buy"] else '#FF1744'
            st_min_offset = len(indices) - len(st_minor["history"])
            ax1.plot(indices[st_min_offset:], st_minor["history"], color=st_min_color, linewidth=1.5, label='ST Minor (10,3)')

        # Main Subplot Title & Labels
        symbol_upper = symbol.upper().replace("USDT", "")
        ax1.set_title(f"TradingView Chart: {symbol_upper}/USDT ({interval.upper()})", color='#FFFFFF', fontsize=14, fontweight='bold', pad=10)
        ax1.grid(True, color='#1E222D', linestyle=':', alpha=0.6)
        ax1.legend(loc='upper left', facecolor='#1E222D', edgecolor='#2A2E39', fontsize=8, textcolor='#D1D4DC')

        # Subplot 2: RSI TueTrading
        # Generate RSI array matching subset
        gains, losses = [], []
        for i in range(1, len(close_prices)):
            chg = close_prices[i] - close_prices[i-1]
            gains.append(chg if chg > 0 else 0)
            losses.append(abs(chg) if chg < 0 else 0)
            
        period = 14
        if len(gains) >= period:
            avg_g = sum(gains[:period]) / period
            avg_l = sum(losses[:period]) / period
            rsi_vals = []
            rsi_vals.append(100.0 if avg_l == 0 else 100.0 - (100.0 / (1.0 + (avg_g / avg_l))))
            for i in range(period, len(gains)):
                avg_g = (avg_g * (period - 1) + gains[i]) / period
                avg_l = (avg_l * (period - 1) + losses[i]) / period
                rsi_vals.append(100.0 if avg_l == 0 else 100.0 - (100.0 / (1.0 + (avg_g / avg_l))))
                
            rsi_offset = len(indices) - len(rsi_vals)
            ax2.plot(indices[rsi_offset:], rsi_vals, color='#7E57C2', linewidth=1.5, label='RSI (14)')

        # RSI Overbought / Oversold Lines
        ax2.axhline(70, color='#FF5252', linestyle='--', alpha=0.7, linewidth=1)
        ax2.axhline(50, color='#787B86', linestyle=':', alpha=0.5, linewidth=1)
        ax2.axhline(30, color='#00E676', linestyle='--', alpha=0.7, linewidth=1)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("RSI", color='#D1D4DC', fontsize=10)
        ax2.grid(True, color='#1E222D', linestyle=':', alpha=0.6)

        # Hide X-ticks on top subplot, set format on bottom
        ax1.set_xticklabels([])
        ax2.set_xlim(0, len(candles_subset))
        ax1.set_xlim(0, len(candles_subset))

        plt.tight_layout()

        # Save Image to File
        output_filename = f"chart_{symbol_upper}_{interval.lower()}.png"
        plt.savefig(output_filename, facecolor='#131722', edgecolor='none', bbox_inches='tight')
        plt.close(fig)

        print(f"✅ Successfully rendered chart image: {output_filename}")
        return output_filename
    except Exception as e:
        print(f"❌ Error in generate_chart_image for {symbol} ({interval}): {e}")
        return None

def cleanup_chart_image(filepath):
    """Safely delete temporary chart image file after sending."""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🗑 Deleted temporary chart file: {filepath}")
        except Exception as e:
            print(f"⚠️ Error deleting temporary chart file {filepath}: {e}")
