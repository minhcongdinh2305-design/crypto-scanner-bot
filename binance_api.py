import urllib.request
import json
import time
from concurrent.futures import ThreadPoolExecutor

BINANCE_BASE_URL = "https://api.binance.com/api/v3"

def fetch_json(url):
    """Fetch JSON data using standard urllib with timeout & retry handling."""
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def get_ticker_24h(symbol="BTCUSDT"):
    """Get 24h ticker price and statistics for a symbol."""
    symbol = symbol.upper().replace("/", "").replace("-", "")
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"
    
    url = f"{BINANCE_BASE_URL}/ticker/24hr?symbol={symbol}"
    data = fetch_json(url)
    if not data or "lastPrice" not in data:
        return None
        
    return {
        "symbol": data["symbol"],
        "lastPrice": float(data["lastPrice"]),
        "priceChangePercent": float(data["priceChangePercent"]),
        "highPrice": float(data["highPrice"]),
        "lowPrice": float(data["lowPrice"]),
        "volume": float(data["volume"]),
        "quoteVolume": float(data["quoteVolume"])
    }

def get_klines(symbol="BTCUSDT", interval="1h", limit=100):
    """
    Fetch OHLCV candlestick data.
    Supported intervals: 15m, 30m, 1h, 2h, 4h, 8h, 12h, 1d, 3d, 1w
    """
    symbol = symbol.upper().replace("/", "").replace("-", "")
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"

    url = f"{BINANCE_BASE_URL}/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = fetch_json(url)
    if not data:
        return []
        
    candles = []
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

def fetch_multi_klines_parallel(symbol="BTCUSDT", intervals=["15m", "1h", "4h", "1d"]):
    """
    Fetches all requested timeframes in PARALLEL threads for maximum speed!
    """
    results = {}
    with ThreadPoolExecutor(max_workers=len(intervals) + 1) as executor:
        future_ticker = executor.submit(get_ticker_24h, symbol)
        future_klines = {
            tf: executor.submit(get_klines, symbol, tf, 100)
            for tf in intervals
        }
        
        ticker = future_ticker.result()
        for tf, future in future_klines.items():
            results[tf] = future.result()
            
    return ticker, results
