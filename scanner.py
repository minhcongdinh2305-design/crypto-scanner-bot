from binance_api import get_ticker_24h, get_klines, fetch_multi_klines_parallel
from ta_engine import analyze_timeframe
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

TOP_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", 
    "AVAX", "LINK", "DOT", "NEAR", "SUI", "APT", "PEPE", "WIF"
]

ALL_TIMEFRAMES = ["1d", "12h", "8h", "4h", "2h", "1h", "30m", "15m"]

def format_grouped_details(detail_map):
    """
    Groups timeframes by action status.
    Example: {"Xanh": ["4H", "1D"], "Xanh Flat": ["12H"]} -> "Xanh Flat 12H, Xanh 4H, 1D"
    """
    if not detail_map:
        return "KHÔNG ĐẠT"
        
    parts = []
    for status, tfs in detail_map.items():
        if tfs:
            parts.append(f"{status} {', '.join(tfs)}")
            
    if not parts:
        return "KHÔNG ĐẠT"
        
    return f"OK ({', '.join(parts)})"

def get_coin_report(symbol="BTC"):
    """
    Detailed Action Status + Timeframe Grouping minimal report:
    🪙 {SYMBOL}

    1. Trend: {OK (chi tiết trạng thái + khung) / KHÔNG ĐẠT}
    2. EMA: {OK (chi tiết trạng thái + khung) / KHÔNG ĐẠT}
    3. RSI: {OK (chi tiết trạng thái + khung) / KHÔNG ĐẠT}

    👉 Kết luận: ĐẠT {X}/3 {Nếu 3/3 ghi "(A+ Setup)", nếu <3/3 ghi "(Theo dõi thêm)"}
    """
    symbol_upper = symbol.upper().replace("USDT", "")
    full_symbol = symbol_upper + "USDT"
    
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)

    if not ticker:
        return f"❌ Không tìm thấy dữ liệu cho **{symbol_upper}/USDT**!"

    trend_detail_map = defaultdict(list)
    ema_detail_map = defaultdict(list)
    rsi_detail_map = defaultdict(list)

    tf_analyses = {}
    for tf in ALL_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        analysis = analyze_timeframe(candles)
        if analysis:
            tf_analyses[tf] = analysis
            tf_str = tf.upper()
            
            # 1. Trend Analysis (Supertrend Line Colors & Flat Status)
            st_maj = analysis["st_major"]
            st_min = analysis["st_minor"]
            if st_maj["is_buy"]:
                if st_maj["is_flat"]:
                    trend_detail_map["Xanh Flat"].append(tf_str)
                else:
                    trend_detail_map["Xanh"].append(tf_str)
            else:
                if st_maj["is_flat"]:
                    trend_detail_map["Đỏ Flat"].append(tf_str)
                else:
                    trend_detail_map["Đỏ"].append(tf_str)

            # 2. EMA Analysis (Crossover & Expansion Force)
            ema = analysis["ema_info"]
            if "GOLDEN CROSS" in ema["cross"]:
                ema_detail_map["Chớm cắt lên"].append(tf_str)
            elif "DEATH CROSS" in ema["cross"]:
                ema_detail_map["Chớm cắt xuống"].append(tf_str)
            elif ema["is_expanding"]:
                if ema["ema20"] and analysis["price"] > ema["ema20"]:
                    ema_detail_map["Mở rộng lên"].append(tf_str)
                else:
                    ema_detail_map["Mở rộng xuống"].append(tf_str)

            # 3. RSI TueTrading Analysis (Divergence, Squeeze, Extreme)
            rsi = analysis["rsi_tue"]
            if "BULLISH DIVERGENCE" in rsi["divergence"]:
                rsi_detail_map["Phân kỳ tăng"].append(tf_str)
            elif "BEARISH DIVERGENCE" in rsi["divergence"]:
                rsi_detail_map["Phân kỳ giảm"].append(tf_str)
            elif rsi["squeeze_breakout"]:
                rsi_detail_map["Bung nén"].append(tf_str)
            elif rsi["rsi"] <= 35:
                rsi_detail_map["Quá bán"].append(tf_str)
            elif rsi["rsi"] >= 70:
                rsi_detail_map["Quá mua"].append(tf_str)

    primary_tf = tf_analyses.get("4h") or tf_analyses.get("1h") or (list(tf_analyses.values())[0] if tf_analyses else None)

    # 1. Trend Line Formatting
    trend_line = format_grouped_details(trend_detail_map)
    is_trend_pass = trend_line != "KHÔNG ĐẠT"

    # 2. EMA Line Formatting
    ema_line = format_grouped_details(ema_detail_map)
    is_ema_pass = ema_line != "KHÔNG ĐẠT"

    # 3. RSI Line Formatting
    rsi_line = format_grouped_details(rsi_detail_map)
    is_rsi_pass = rsi_line != "KHÔNG ĐẠT"

    # Passed Count Calculation
    passed_count = (1 if is_trend_pass else 0) + (1 if is_ema_pass else 0) + (1 if is_rsi_pass else 0)

    # Conclusion formatting
    if passed_count == 3:
        conclusion_str = "ĐẠT 3/3 (A+ Setup)"
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
    Absolute Minimal Market Scanner with Action Statuses.
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

    if not results:
        return "⚪ Hiện tại các Top Coin chưa có điểm kích hoạt A+."

    return "\n\n----------------------------\n\n".join(results[:5])
