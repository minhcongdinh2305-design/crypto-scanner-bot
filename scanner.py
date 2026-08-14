from binance_api import get_ticker_24h, get_klines, fetch_multi_klines_parallel
from ta_engine import analyze_timeframe
from concurrent.futures import ThreadPoolExecutor

TOP_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", 
    "AVAX", "LINK", "DOT", "NEAR", "SUI", "APT", "PEPE", "WIF"
]

ALL_TIMEFRAMES = ["1d", "12h", "8h", "4h", "2h", "1h", "30m", "15m"]

def format_price(val):
    if not val:
        return "N/A"
    if val >= 1000:
        return f"${val:,.2f}"
    elif val >= 1:
        return f"${val:.4f}"
    else:
        return f"${val:.6f}"

def get_coin_report(symbol="BTC"):
    """
    Ultra-concise minimal report format according to exact user specification:
    🪙 {SYMBOL} | Giá: {PRICE} ({CHANGE_24H}%)
    🎯 Setup: {LONG/SHORT/NEUTRAL} (Điểm: {SCORE}/100)

    1. Trend: {ĐẠT / KHÔNG ĐẠT} - {BUY mạnh / SELL mạnh / Đi ngang} (Khung: {danh_sách_khung})
    2. EMA: {ĐẠT / KHÔNG ĐẠT} - {Cắt mở rộng / Thu hẹp / Đang cản} (Khung: {danh_sách_khung})
    3. RSI: {ĐẠT / KHÔNG ĐẠT} - {Phân kỳ tăng / Phân kỳ giảm / Bung nén} (Khung: {danh_sách_khung})

    👉 Kết luận: {ĐỦ ĐIỀU KIỆN A+ / Theo dõi thêm} ({PASSED_COUNT}/3 Chỉ báo đồng thuận)
    """
    symbol_upper = symbol.upper().replace("USDT", "")
    full_symbol = symbol_upper + "USDT"
    
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)

    if not ticker:
        return f"❌ Không tìm thấy dữ liệu cho cặp **{symbol_upper}/USDT**!"

    # Multi-timeframe evaluation arrays
    trend_tfs = []
    trend_type = "Đi ngang"
    ema_tfs = []
    ema_type = "Thu hẹp"
    rsi_tfs = []
    rsi_types = []

    buy_trend_count = 0
    sell_trend_count = 0
    
    tf_analyses = {}
    for tf in ALL_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        analysis = analyze_timeframe(candles)
        if analysis:
            tf_analyses[tf] = analysis
            tf_str = tf.upper()
            
            # 1. Trend Evaluation
            st_maj = analysis["st_major"]
            st_min = analysis["st_minor"]
            if st_maj["is_buy"] and st_min["is_buy"]:
                buy_trend_count += 1
                trend_tfs.append(tf_str)
            elif not st_maj["is_buy"] and not st_min["is_buy"]:
                sell_trend_count += 1
                trend_tfs.append(tf_str)
            elif st_maj["is_flat"]:
                trend_tfs.append(tf_str)

            # 2. EMA Evaluation
            ema = analysis["ema_info"]
            if ema["is_expanding"] or ema["cross"] != "NONE":
                ema_tfs.append(tf_str)
                if ema["is_expanding"]:
                    ema_type = "Cắt mở rộng"

            # 3. RSI Evaluation
            rsi = analysis["rsi_tue"]
            if rsi["divergence"] != "NONE" or rsi["squeeze_breakout"] or rsi["rsi"] <= 35 or rsi["rsi"] >= 70:
                rsi_tfs.append(tf_str)
                if "BULLISH" in rsi["divergence"]:
                    if "Phân kỳ tăng" not in rsi_types: rsi_types.append("Phân kỳ tăng")
                elif "BEARISH" in rsi["divergence"]:
                    if "Phân kỳ giảm" not in rsi_types: rsi_types.append("Phân kỳ giảm")
                if rsi["squeeze_breakout"]:
                    if "Bung nén" not in rsi_types: rsi_types.append("Bung nén")

    # Select Primary Timeframe (4H or 1H)
    primary_tf = tf_analyses.get("4h") or tf_analyses.get("1h") or list(tf_analyses.values())[0]
    
    # 1. Trend Assessment
    is_trend_pass = len(trend_tfs) >= 2
    if buy_trend_count > sell_trend_count:
        trend_type = "BUY mạnh"
    elif sell_trend_count > buy_trend_count:
        trend_type = "SELL mạnh"
    else:
        trend_type = "Đi ngang"
    trend_status = "ĐẠT" if is_trend_pass else "KHÔNG ĐẠT"
    trend_tfs_str = ", ".join(trend_tfs[:4]) if trend_tfs else "Không"

    # 2. EMA Assessment
    is_ema_pass = len(ema_tfs) >= 1 or primary_tf["ema_info"]["is_expanding"]
    ema_status = "ĐẠT" if is_ema_pass else "KHÔNG ĐẠT"
    ema_tfs_str = ", ".join(ema_tfs[:4]) if ema_tfs else "Không"

    # 3. RSI Assessment
    is_rsi_pass = len(rsi_tfs) >= 1 or primary_tf["rsi_tue"]["divergence"] != "NONE" or primary_tf["rsi_tue"]["squeeze_breakout"]
    rsi_status = "ĐẠT" if is_rsi_pass else "KHÔNG ĐẠT"
    rsi_type_str = " & ".join(rsi_types) if rsi_types else "Bình thường"
    rsi_tfs_str = ", ".join(rsi_tfs[:4]) if rsi_tfs else "Không"

    # Passed Count Calculation
    passed_count = (1 if is_trend_pass else 0) + (1 if is_ema_pass else 0) + (1 if is_rsi_pass else 0)

    # Conclusion & Rating Formatting
    if passed_count == 3 and primary_tf["score"] >= 65:
        conclusion = f"ĐỦ ĐIỀU KIỆN A+ ({passed_count}/3 Chỉ báo đồng thuận)"
        setup_label = "LONG CỰC MẠNH"
    elif passed_count == 3 and primary_tf["score"] <= 35:
        conclusion = f"ĐỦ ĐIỀU KIỆN A+ ({passed_count}/3 Chỉ báo đồng thuận)"
        setup_label = "SHORT CỰC MẠNH"
    elif passed_count >= 2:
        conclusion = f"TÍN HIỆU TỐT ({passed_count}/3 Chỉ báo đồng thuận)"
        setup_label = "MUA (LONG)" if buy_trend_count >= sell_trend_count else "BÁN (SHORT)"
    else:
        conclusion = f"Theo dõi thêm ({passed_count}/3 Chỉ báo đồng thuận)"
        setup_label = "TRUNG TÍNH"

    change_pct = ticker['priceChangePercent']
    change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

    report = []
    report.append(f"🪙 **{symbol_upper}/USDT** | Giá: `{format_price(ticker['lastPrice'])}` ({change_str})")
    report.append(f"🎯 Setup: **{setup_label}** (Điểm: `{primary_tf['score']}/100`)\n")

    report.append(f"1. Trend: **{trend_status}** - {trend_type} ({trend_tfs_str})")
    report.append(f"2. EMA: **{ema_status}** - {ema_type} ({ema_tfs_str})")
    report.append(f"3. RSI: **{rsi_status}** - {rsi_type_str} ({rsi_tfs_str})\n")

    report.append(f"👉 Kết luận: **{conclusion}**")

    return "\n".join(report)

def analyze_single_coin_for_scan(coin):
    full_symbol = coin.upper() + "USDT"
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)
    if not ticker:
        return None
        
    report_text = get_coin_report(coin)
    if "ĐẠT" in report_text or "A+" in report_text:
        return report_text
    return None

def scan_market(coins_list=None):
    """
    Ultra-Concise Minimal Market Scanner.
    Formats results using the required concise template!
    """
    if not coins_list:
        coins_list = TOP_COINS

    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        scan_futures = [executor.submit(get_coin_report, coin) for coin in coins_list]
        for future in scan_futures:
            res = future.result()
            if res and ("ĐẠT" in res or "A+" in res):
                results.append(res)

    report = []
    report.append("🔍 **KẾT QUẢ QUÉT HỆ THỐNG GIAO DỊCH A+ (TOP COINS)**\n")
    
    if not results:
        report.append("⚪ Hiện tại các Top Coin đang ở vùng tích lũy, chưa kích hoạt tín hiệu A+.")
        return "\n".join(report)

    report.append("\n\n----------------------------\n\n".join(results[:5]))
    return "\n".join(report)
