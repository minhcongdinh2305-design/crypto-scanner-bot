from binance_api import get_ticker_24h, get_klines, fetch_multi_klines_parallel
from ta_engine import analyze_timeframe
from concurrent.futures import ThreadPoolExecutor

TOP_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", 
    "AVAX", "LINK", "DOT", "NEAR", "SUI", "APT", "PEPE", "WIF"
]

ALL_TIMEFRAMES = ["1d", "12h", "8h", "4h", "2h", "1h", "30m", "15m"]

def get_coin_report(symbol="BTC"):
    """
    Absolute Minimal Format:
    🪙 {SYMBOL}

    1. Trend: {OK (danh sách khung) / KHÔNG ĐẠT}
    2. EMA: {OK (danh sách khung) / KHÔNG ĐẠT}
    3. RSI: {OK (danh sách khung) / KHÔNG ĐẠT}

    👉 Kết luận: ĐẠT {X}/3 {Nếu 3/3 ghi "(A+ Setup)", nếu <3/3 ghi "(Theo dõi thêm)"}
    """
    symbol_upper = symbol.upper().replace("USDT", "")
    full_symbol = symbol_upper + "USDT"
    
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)

    if not ticker:
        return f"❌ Không tìm thấy dữ liệu cho **{symbol_upper}/USDT**!"

    trend_tfs = []
    ema_tfs = []
    rsi_tfs = []

    tf_analyses = {}
    for tf in ALL_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        analysis = analyze_timeframe(candles)
        if analysis:
            tf_analyses[tf] = analysis
            tf_str = tf.upper()
            
            # 1. Trend Evaluation (Double Supertrend)
            st_maj = analysis["st_major"]
            st_min = analysis["st_minor"]
            if (st_maj["is_buy"] and st_min["is_buy"]) or (not st_maj["is_buy"] and not st_min["is_buy"]) or st_maj["is_flat"]:
                trend_tfs.append(tf_str)

            # 2. EMA Evaluation
            ema = analysis["ema_info"]
            if ema["is_expanding"] or ema["cross"] != "NONE":
                ema_tfs.append(tf_str)

            # 3. RSI Evaluation
            rsi = analysis["rsi_tue"]
            if rsi["divergence"] != "NONE" or rsi["squeeze_breakout"] or rsi["rsi"] <= 35 or rsi["rsi"] >= 70:
                rsi_tfs.append(tf_str)

    primary_tf = tf_analyses.get("4h") or tf_analyses.get("1h") or list(tf_analyses.values())[0]

    # 1. Trend Line
    is_trend_pass = len(trend_tfs) >= 2
    trend_line = f"OK ({', '.join(trend_tfs[:4])})" if (is_trend_pass and trend_tfs) else "KHÔNG ĐẠT"

    # 2. EMA Line
    is_ema_pass = len(ema_tfs) >= 1 or primary_tf["ema_info"]["is_expanding"]
    ema_line = f"OK ({', '.join(ema_tfs[:4])})" if (is_ema_pass and ema_tfs) else "KHÔNG ĐẠT"

    # 3. RSI Line
    is_rsi_pass = len(rsi_tfs) >= 1 or primary_tf["rsi_tue"]["divergence"] != "NONE" or primary_tf["rsi_tue"]["squeeze_breakout"]
    rsi_line = f"OK ({', '.join(rsi_tfs[:4])})" if (is_rsi_pass and rsi_tfs) else "KHÔNG ĐẠT"

    # Passed Count Calculation
    passed_count = (1 if is_trend_pass else 0) + (1 if is_ema_pass else 0) + (1 if is_rsi_pass else 0)

    # Conclusion formatting
    if passed_count == 3:
        conclusion_str = f"ĐẠT 3/3 (A+ Setup)"
    else:
        conclusion_str = f"ĐẠT {passed_count}/3 (Theo dõi thêm)"

    report = []
    report.append(f"🪙 **{symbol_upper}/USDT**\n")
    report.append(f"1. Trend: **{trend_line}**")
    report.append(f"2. EMA: **{ema_line}**")
    report.append(f"3. RSI: **{rsi_line}**\n")
    report.append(f"👉 Kết luận: **{conclusion_str}**")

    return "\n".join(report)

def analyze_single_coin_for_scan(coin):
    full_symbol = coin.upper() + "USDT"
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)
    if not ticker:
        return None
        
    report_text = get_coin_report(coin)
    if "ĐẠT 3/3" in report_text or "OK" in report_text:
        return report_text
    return None

def scan_market(coins_list=None):
    """
    Absolute Minimal Market Scanner.
    Formats results using the mandatory minimal structure!
    """
    if not coins_list:
        coins_list = TOP_COINS

    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        scan_futures = [executor.submit(get_coin_report, coin) for coin in coins_list]
        for future in scan_futures:
            res = future.result()
            if res and ("ĐẠT 3/3" in res or "OK" in res):
                results.append(res)

    report = []
    report.append("🔍 **KẾT QUẢ QUÉT A+ SETUP (TOP COINS)**\n")
    
    if not results:
        report.append("⚪ Hiện tại các Top Coin chưa có điểm kích hoạt A+.")
        return "\n".join(report)

    report.append("\n\n----------------------------\n\n".join(results[:5]))
    return "\n".join(report)
