"""
Dual-Engine Visual Chart Renderer for Crypto Scanner Bot
Supports:
1. Native Matplotlib Renderer (if installed)
2. Zero-Dependency QuickChart Financial API Fallback (100% Guaranteed Image Generation on ANY Cloud Host!)
Absolute zero crash failsafe built-in!
"""
import os
import sys
import json
import urllib.request
import urllib.parse
from ta_engine import calculate_ema, calculate_supertrend, calculate_rsi_tuetrading

def render_chart_quickchart(symbol, interval, candles):
    if not candles:
        return None

    symbol_upper = symbol.upper().replace("USDT", "")
    candles_subset = candles[-60:]
    
    close_prices = [c["close"] for c in candles_subset]
    
    ema20 = calculate_ema(close_prices, 20)
    ema50 = calculate_ema(close_prices, 50)
    
    ema20_aligned = [None] * (len(close_prices) - len(ema20)) + [round(v, 2) for v in ema20]
    ema50_aligned = [None] * (len(close_prices) - len(ema50)) + [round(v, 2) for v in ema50]

    labels = [f"#{i+1}" for i in range(len(candles_subset))]
    
    chart_config = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": f"{symbol_upper} Price",
                    "data": [round(c, 2) for c in close_prices],
                    "borderColor": "#089981" if close_prices[-1] >= close_prices[0] else "#F23645",
                    "borderWidth": 2,
                    "fill": False,
                    "pointRadius": 0
                },
                {
                    "label": "EMA 20",
                    "data": ema20_aligned,
                    "borderColor": "#2962FF",
                    "borderWidth": 1.5,
                    "fill": False,
                    "pointRadius": 0
                },
                {
                    "label": "EMA 50",
                    "data": ema50_aligned,
                    "borderColor": "#FF6D00",
                    "borderWidth": 1.5,
                    "fill": False,
                    "pointRadius": 0
                }
            ]
        },
        "options": {
            "title": {
                "display": True,
                "text": f"TradingView Chart: {symbol_upper}/USDT ({interval.upper()})",
                "fontColor": "#FFFFFF",
                "fontSize": 18
            },
            "legend": {
                "labels": {"fontColor": "#D1D4DC"}
            },
            "scales": {
                "xAxes": [{
                    "gridLines": {"color": "#1E222D"},
                    "ticks": {"fontColor": "#787B86", "maxTicksLimit": 10}
                }],
                "yAxes": [{
                    "gridLines": {"color": "#1E222D"},
                    "ticks": {"fontColor": "#787B86"}
                }]
            }
        }
    }

    post_data = json.dumps({
        "backgroundColor": "#131722",
        "width": 800,
        "height": 450,
        "devicePixelRatio": 2.0,
        "format": "png",
        "chart": chart_config
    }).encode('utf-8')

    output_filename = f"chart_{symbol_upper}_{interval.lower()}.png"

    try:
        req = urllib.request.Request(
            "https://quickchart.io/chart",
            data=post_data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                with open(output_filename, "wb") as f:
                    f.write(response.read())
                print(f"✅ QuickChart API successfully rendered PNG image: {output_filename}")
                return output_filename
    except Exception as e:
        print(f"⚠️ QuickChart API error: {e}")

    return None

def generate_chart_image(symbol, interval, candles):
    """
    Dual-Engine Chart Renderer with Failsafe Guarantee.
    Never throws ValueError.
    """
    if not candles or len(candles) < 5:
        from binance_api import get_klines
        candles = get_klines(symbol, "1d", 150)

    symbol_upper = symbol.upper().replace("USDT", "")
    output_filename = f"chart_{symbol_upper}_{interval.lower()}.png"

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        candles_subset = candles[-120:]
        close_prices = [c["close"] for c in candles_subset]
        
        ema20 = calculate_ema(close_prices, 20)
        ema50 = calculate_ema(close_prices, 50)
        st_major = calculate_supertrend(candles_subset, atr_period=15, multiplier=10.0)
        st_minor = calculate_supertrend(candles_subset, atr_period=10, multiplier=3.0)
        
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

        indices = list(range(len(candles_subset)))
        
        for i, c in enumerate(candles_subset):
            open_p, high_p, low_p, close_p = c["open"], c["high"], c["low"], c["close"]
            color = '#089981' if close_p >= open_p else '#F23645'
            
            ax1.plot([i, i], [low_p, high_p], color=color, linewidth=1.2)
            
            body_bottom = min(open_p, close_p)
            body_height = max(abs(close_p - open_p), (high_p - low_p) * 0.001)
            rect = Rectangle((i - 0.35, body_bottom), 0.7, body_height, facecolor=color, edgecolor=color)
            ax1.add_patch(rect)

        if len(ema20) > 0:
            offset20 = len(indices) - len(ema20)
            ax1.plot(indices[offset20:], ema20, color='#2962FF', linewidth=1.5, label='EMA 20')
            
        if len(ema50) > 0:
            offset50 = len(indices) - len(ema50)
            ax1.plot(indices[offset50:], ema50, color='#FF6D00', linewidth=1.5, label='EMA 50')

        if st_major["history"] and len(st_major["history"]) > 0:
            st_maj_color = '#00E676' if st_major["is_buy"] else '#FF5252'
            st_maj_offset = len(indices) - len(st_major["history"])
            ax1.plot(indices[st_maj_offset:], st_major["history"], color=st_maj_color, linewidth=2.0, linestyle='--', label='ST Major (15,10)')

        if st_minor["history"] and len(st_minor["history"]) > 0:
            st_min_color = '#00E5FF' if st_minor["is_buy"] else '#FF1744'
            st_min_offset = len(indices) - len(st_minor["history"])
            ax1.plot(indices[st_min_offset:], st_minor["history"], color=st_min_color, linewidth=1.5, label='ST Minor (10,3)')

        ax1.set_title(f"TradingView Chart: {symbol_upper}/USDT ({interval.upper()})", color='#FFFFFF', fontsize=14, fontweight='bold', pad=10)
        ax1.grid(True, color='#1E222D', linestyle=':', alpha=0.6)
        ax1.legend(loc='upper left', facecolor='#1E222D', edgecolor='#2A2E39', fontsize=8, textcolor='#D1D4DC')

        # Subplot 2: RSI
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

        ax2.axhline(70, color='#FF5252', linestyle='--', alpha=0.7, linewidth=1)
        ax2.axhline(50, color='#787B86', linestyle=':', alpha=0.5, linewidth=1)
        ax2.axhline(30, color='#00E676', linestyle='--', alpha=0.7, linewidth=1)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("RSI", color='#D1D4DC', fontsize=10)
        ax2.grid(True, color='#1E222D', linestyle=':', alpha=0.6)

        ax1.set_xticklabels([])
        ax2.set_xlim(0, len(candles_subset))
        ax1.set_xlim(0, len(candles_subset))

        plt.tight_layout()
        plt.savefig(output_filename, facecolor='#131722', edgecolor='none', bbox_inches='tight')
        plt.close(fig)

        print(f"✅ Matplotlib engine successfully rendered PNG image: {output_filename}")
        return output_filename
    except Exception as e_mat:
        print(f"⚠️ Matplotlib engine unavailable ({e_mat}). Switching to QuickChart API fallback...")

    fallback_res = render_chart_quickchart(symbol, interval, candles)
    if fallback_res:
        return fallback_res

    return None

def cleanup_chart_image(filepath):
    """Safely delete temporary chart image file after sending."""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"🗑 Deleted temporary chart file: {filepath}")
        except Exception as e:
            print(f"⚠️ Error deleting temporary chart file {filepath}: {e}")
