from binance_api import get_ticker_24h, fetch_multi_klines_parallel
from ta_engine import get_4trend_status
from concurrent.futures import ThreadPoolExecutor

TOP_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", 
    "AVAX", "LINK", "DOT", "NEAR", "SUI", "APT", "PEPE", "WIF"
]

SCAN_TIMEFRAMES = ["30m", "1h", "2h", "4h", "8h", "12h", "1d", "1w", "1m"]

def get_coin_report(symbol="BTC"):
    """
    4-Trend Line Scan Report (XANH, TÍM, ĐỎ, CAM) across 9 timeframes.
    ▫️ {TF}: {Trạng thái 4 đường}
    """
    symbol_upper = symbol.upper().replace("USDT", "").replace("SCAN", "").replace("/", "").strip()
    full_symbol = symbol_upper + "USDT"
    
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, SCAN_TIMEFRAMES)

    if not ticker:
        return f"❌ Không tìm thấy dữ liệu cho **{symbol_upper}/USDT**!"

    report = []
    report.append(f"🪙 **{symbol_upper}/USDT** (4-TREND SCAN)\n")

    for tf in SCAN_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        trend_st = get_4trend_status(candles)
        tf_label = tf.upper()
        
        # Alignment space for 1H, 2H, 4H, 8H, 1D, 1W, 1M
        if len(tf_label) == 2:
            tf_display = f"{tf_label} "
        else:
            tf_display = tf_label

        report.append(f"▫️ **{tf_display}**: {trend_st}")

    return "\n".join(report)

def analyze_single_coin_for_scan(coin):
    return get_coin_report(coin)

def scan_market(coins_list=None):
    """
    Market Watchlist Scanner using 4-Trend Scan.
    """
    if not coins_list or len(coins_list) == 0:
        coins_list = TOP_COINS

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        scan_futures = [executor.submit(get_coin_report, coin) for coin in coins_list]
        for future in scan_futures:
            res = future.result()
            if res and "4-TREND SCAN" in res:
                results.append(res)

    if not results:
        return "⚪ Không thể lấy báo cáo quét 4 đường Trend."

    return "\n\n----------------------------\n\n".join(results[:5])
