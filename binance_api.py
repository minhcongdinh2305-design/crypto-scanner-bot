import urllib.request
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Dual Endpoints for 100% Global Cloud Compatibility (Spot & Futures)
BINANCE_ENDPOINTS = [
    "https://fapi.binance.com/fapi/v1",      # Binance Futures
    "https://api.binance.com/api/v3",        # Binance Spot
    "https://data-api.binance.vision/api/v3" # Binance Public Data API
]

def fetch_json_with_fallback(path):
    """
    Fetches JSON from Binance endpoints with automatic fallback.
    Prevents HTTP 451/403 errors from Cloud Hosting IPs (Render US).
    """
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
                    if data:
                        return data
        except Exception as e:
            print(f"⚠️ Fetch attempt failed for {url}: {e}")
            continue

    return None

def get_ticker_24h(symbol="BTCUSDT"):
    """
    Get 24h ticker price and statistics.
    Normalizes symbol format (BTC -> BTCUSDT).
    """
    symbol = symbol.upper().replace("/", "").replace("-", "")
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"
    
    path = f"ticker/24hr?symbol={symbol}"
    data = fetch_json_with_fallback(path)
    
    if not data:
        print(f"❌ Failed to fetch 24h ticker for {symbol}")
        return None
        
    try:
        ticker_data = data[0] if isinstance(data, list) else data
        return {
            "symbol": ticker_data["symbol"],
            "lastPrice": float(ticker_data["lastPrice"]),
            "priceChangePercent": float(ticker_data.get("priceChangePercent", 0.0)),
            "highPrice": float(ticker_data.get("highPrice", ticker_data["lastPrice"])),
            "lowPrice": float(ticker_data.get("lowPrice", ticker_data["lastPrice"])),
            "volume": float(ticker_data.get("volume", 0.0))
        }
    except Exception as e:
        print(f"❌ Error parsing ticker for {symbol}: {e}")
        return None

def get_klines(symbol="BTCUSDT", interval="1h", limit=200):
    """
    Fetches OHLCV candlestick data (150-200 candles minimum for EMA 200 & ATR 15).
    Supported intervals: 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, 1w
    """
    symbol = symbol.upper().replace("/", "").replace("-", "")
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"

    # Fully supported interval map including 3d and 1w
    interval_map = {
        "15m": "15m", "30m": "30m", "1h": "1h", "2h": "2h",
        "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h", 
        "1d": "1d", "3d": "3d", "1w": "1w"
    }
    safe_interval = interval_map.get(interval.lower(), "1d")

    path = f"klines?symbol={symbol}&interval={safe_interval}&limit={limit}"
    data = fetch_json_with_fallback(path)
    
    # Fallback to 1d if timeframe returned empty (e.g. 3d fallback)
    if not data or not isinstance(data, list):
        print(f"⚠️ Primary interval {safe_interval} returned empty for {symbol}. Falling back to 1d...")
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
    """
    Parallel multi-timeframe fetching with exception handling.
    """
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
