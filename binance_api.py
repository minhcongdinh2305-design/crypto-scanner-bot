import urllib.request
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Endpoints for Spot & Futures
BINANCE_ENDPOINTS = [
    "https://fapi.binance.com/fapi/v1",      # Binance Futures
    "https://api.binance.com/api/v3",        # Binance Spot
    "https://data-api.binance.vision/api/v3" # Binance Public Data API
]

def fetch_json_with_fallback(path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    for base_url in BINANCE_ENDPOINTS:
        url = f"{base_url}/{path}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data and isinstance(data, list):
                        return data
        except Exception:
            continue

    return None

def resample_candles(candles_1d, days=3):
    """
    Resamples daily (1d) candles into multi-day candles (e.g. 2D or 3D).
    Groups `days` consecutive 1D candles together:
    - Open = first candle open
    - High = max(highs)
    - Low = min(lows)
    - Close = last candle close
    - Volume = sum(volumes)
    """
    if not candles_1d or len(candles_1d) < days:
        return []

    resampled = []
    for i in range(0, len(candles_1d), days):
        group = candles_1d[i:i+days]
        if not group:
            continue
            
        resampled.append({
            "timestamp": group[0]["timestamp"],
            "open": group[0]["open"],
            "high": max(c["high"] for c in group),
            "low": min(c["low"] for c in group),
            "close": group[-1]["close"],
            "volume": sum(c["volume"] for c in group)
        })
        
    return resampled

def get_ticker_24h(symbol="BTCUSDT"):
    symbol = symbol.upper().replace("/", "").replace("-", "")
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    for base_url in BINANCE_ENDPOINTS:
        url = f"{base_url}/ticker/24hr?symbol={symbol}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    ticker_data = data[0] if isinstance(data, list) else data
                    if ticker_data and "lastPrice" in ticker_data:
                        return {
                            "symbol": ticker_data["symbol"],
                            "lastPrice": float(ticker_data["lastPrice"]),
                            "priceChangePercent": float(ticker_data.get("priceChangePercent", 0.0)),
                            "highPrice": float(ticker_data.get("highPrice", ticker_data["lastPrice"])),
                            "lowPrice": float(ticker_data.get("lowPrice", ticker_data["lastPrice"])),
                            "volume": float(ticker_data.get("volume", 0.0))
                        }
        except Exception:
            continue
    return None

def get_klines(symbol="BTCUSDT", interval="1h", limit=200):
    """
    Fetches OHLCV candlestick data.
    Auto-resamples 2d and 3d timeframes from 1D candles!
    """
    symbol = symbol.upper().replace("/", "").replace("-", "")
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"

    clean_tf = interval.lower().strip()

    # Special Resampling handling for 2D and 3D timeframes
    if clean_tf in ["2d", "3d"]:
        days = 2 if clean_tf == "2d" else 3
        print(f"🔄 Resampling {days}D candles for {symbol} from 300 1D candles...")
        candles_1d = get_klines(symbol, "1d", 300)
        resampled = resample_candles(candles_1d, days=days)
        if len(resampled) >= 10:
            print(f"✅ Successfully resampled {len(resampled)} {days.upper()}D candles for {symbol}")
            return resampled
        safe_interval = "1d"
    else:
        interval_map = {
            "15m": "15m", "30m": "30m", "1h": "1h", "2h": "2h",
            "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h", 
            "1d": "1d", "1w": "1w"
        }
        safe_interval = interval_map.get(clean_tf, "1d")

    path = f"klines?symbol={symbol}&interval={safe_interval}&limit={limit}"
    data = fetch_json_with_fallback(path)
    
    if not data or not isinstance(data, list):
        print(f"⚠️ Primary interval {safe_interval} returned empty for {symbol}. Absolute fallback to 1d...")
        path_fallback = f"klines?symbol={symbol}&interval=1d&limit={limit}"
        data = fetch_json_with_fallback(path_fallback)
        
    if not data or not isinstance(data, list):
        print(f"❌ Failed to fetch klines for {symbol} ({safe_interval})")
        return []
        
    candles = []
    try:
        for item in data:
            candles.append({
                "timestamp": item[0],
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5])
            })
        print(f"✅ Successfully fetched {len(candles)} candles for {symbol} ({safe_interval})")
        return candles
    except Exception as e:
        print(f"❌ Error parsing klines for {symbol}: {e}")
        return []

def fetch_multi_klines_parallel(symbol="BTCUSDT", intervals=["15m", "1h", "4h", "1d"]):
    results = {}
    with ThreadPoolExecutor(max_workers=len(intervals) + 1) as executor:
        future_ticker = executor.submit(get_ticker_24h, symbol)
        future_klines = {
            tf: executor.submit(get_klines, symbol, tf, 200)
            for tf in intervals
        }
        
        ticker = future_ticker.result()
        for tf, future in future_klines.items():
            try:
                results[tf] = future.result()
            except Exception as e:
                print(f"❌ Error in parallel fetch for {symbol} ({tf}): {e}")
                results[tf] = []
            
    return ticker, results
