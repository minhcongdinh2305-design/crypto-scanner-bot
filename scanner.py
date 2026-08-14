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
    Dynamic Column Padded 4-Trend Scan Report wrapped in HTML <pre> monospace tags.
    """
    symbol_upper = symbol.upper().replace("USDT", "").replace("SCAN", "").replace("/", "").strip()
    
    # 1. VALIDATE SYMBOL WITH BINANCE
    is_valid, full_symbol = validate_binance_symbol(symbol_upper)
    if not is_valid:
        return f"❌ Không tìm thấy cặp giao dịch <b>{symbol_upper}/USDT</b> trên Binance."

    # 2. FETCH REAL DATA PARALLEL
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, SCAN_TIMEFRAMES, limit=100)

    if not klines_map:
        return f"❌ Không thể lấy dữ liệu từ Binance cho <b>{symbol_upper}/USDT</b>."

    curr_price_str = "Chưa xác định"
    if ticker and "lastPrice" in ticker:
        curr_price_str = format_price_level(ticker["lastPrice"])

    report = []
    report.append(f"<b>🪙 {symbol_upper}/USDT (CHI TIẾT 4 TREND)</b>")
    report.append(f"Giá: <b>{curr_price_str}</b>\n")
    report.append("<pre>")

    for tf in SCAN_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        col_blue, col_green, col_red, col_yellow = analyze_4_trends(candles)
        tf_label = tf.upper()

        row_str = f"{tf_label:<4}: {col_blue:<22} | {col_green:<22} | {col_red:<22} | {col_yellow:<22}"
        report.append(row_str)

    report.append("</pre>")
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
