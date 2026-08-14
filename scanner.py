from binance_api import validate_binance_symbol, fetch_multi_klines_parallel
from ta_engine import analyze_4_trends, format_price_level
from concurrent.futures import ThreadPoolExecutor

TOP_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", 
    "AVAX", "LINK", "DOT", "NEAR", "SUI", "APT", "PEPE", "WIF"
]

SCAN_TIMEFRAMES = ["30m", "1h", "2h", "4h", "8h", "12h", "1d", "1w", "1m"]

def get_coin_report(symbol="NEAR"):
    """
    Detailed Action-Based 4-Trend Scan Report with explicit Current Price header.
    🪙 {SYMBOL}/USDT (CHI TIẾT 4 TREND)
    Giá: {current_price}
    """
    symbol_upper = symbol.upper().replace("USDT", "").replace("SCAN", "").replace("/", "").strip()
    
    # 1. VALIDATE SYMBOL WITH BINANCE
    is_valid, full_symbol = validate_binance_symbol(symbol_upper)
    if not is_valid:
        return f"❌ Không tìm thấy cặp giao dịch **{symbol_upper}/USDT** trên Binance."

    # 2. FETCH REAL DATA PARALLEL
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, SCAN_TIMEFRAMES, limit=100)

    if not klines_map:
        return f"❌ Không thể lấy dữ liệu từ Binance cho **{symbol_upper}/USDT**."

    curr_price_str = "Chưa xác định"
    if ticker and "lastPrice" in ticker:
        curr_price_str = format_price_level(ticker["lastPrice"])

    report = []
    report.append(f"🪙 **{symbol_upper}/USDT** (CHI TIẾT 4 TREND)")
    report.append(f"Giá: **{curr_price_str}**\n")

    for tf in SCAN_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        trend_st = analyze_4_trends(candles)
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
    if not coins_list or len(coins_list) == 0:
        coins_list = TOP_COINS

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        scan_futures = [executor.submit(get_coin_report, coin) for coin in coins_list]
        for future in scan_futures:
            res = future.result()
            if res and "CHI TIẾT 4 TREND" in res:
                results.append(res)

    if not results:
        return "⚪ Không thể lấy báo cáo chi tiết 4 đường Trend."

    return "\n\n----------------------------\n\n".join(results[:5])
