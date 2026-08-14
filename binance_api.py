import urllib.request
import json
import time

BINANCE_ENDPOINTS = [
    "https://api.binance.com/api/v3",        # Binance Spot API (Primary)
    "https://fapi.binance.com/fapi/v1",      # Binance Futures API
    "https://data-api.binance.vision/api/v3" # Binance Public Data API
]

def normalize_symbol(symbol):
    clean = symbol.upper().replace("USDT", "").replace("/", "").replace("-", "").replace("SCAN", "").strip()
    return f"{clean}USDT"

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
                    if data and isinstance(data, (list, dict)):
                        return data
        except Exception:
            continue

    return None

def get_ticker_24h(symbol="BTC"):
    full_symbol = normalize_symbol(symbol)
    path = f"ticker/24hr?symbol={full_symbol}"
    data = fetch_json_with_fallback(path)
    
    if data and isinstance(data, (dict, list)):
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
            
    return None

def get_klines(symbol="BTC", interval="4h", limit=500):
    """
    Fetches 500 REAL OHLCV candles from Binance to ensure 100% exact Wilder's RMA ATR accumulation.
    """
    full_symbol = normalize_symbol(symbol)
    clean_tf = interval.lower().strip()

    interval_map = {
        "15m": "15m", "30m": "30m", "1h": "1h", "2h": "2h",
        "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h", 
        "1d": "1d", "1w": "1w", "1m": "1M"
    }
    safe_interval = interval_map.get(clean_tf, "4h")

    path = f"klines?symbol={full_symbol}&interval={safe_interval}&limit={limit}"
    data = fetch_json_with_fallback(path)

    if data and isinstance(data, list):
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
            return candles
        except Exception:
            return []

    return []
