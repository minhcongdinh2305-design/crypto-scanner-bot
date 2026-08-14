from binance_api import get_ticker_24h, fetch_multi_klines_parallel
from ta_engine import analyze_timeframe
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

TOP_COINS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", 
    "AVAX", "LINK", "DOT", "NEAR", "SUI", "APT", "PEPE", "WIF"
]

ALL_TIMEFRAMES = ["1d", "12h", "8h", "4h", "2h", "1h", "30m", "15m"]

def format_indicator_line(detail_map):
    """
    Formats indicator line.
    Returns 'OK (Status TFs)' if events exist, otherwise 'KHÔNG CÓ TÍN HIỆU'.
    """
    if not detail_map:
        return "KHÔNG CÓ TÍN HIỆU"
        
    parts = []
    for status, tfs in detail_map.items():
        if tfs:
            parts.append(f"{status} {', '.join(tfs)}")
            
    if not parts:
        return "KHÔNG CÓ TÍN HIỆU"
        
    return f"OK ({', '.join(parts)})"

def get_coin_report(symbol="BTC"):
    """
    Strict Action-Based Report Generator with Directional Confluence & Conflict Check.
    """
    symbol_upper = symbol.upper().replace("USDT", "")
    full_symbol = symbol_upper + "USDT"
    
    ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)

    if not ticker:
        return f"❌ Không tìm thấy dữ liệu cho **{symbol_upper}/USDT**!"

    trend_detail_map = defaultdict(list)
    ema_detail_map = defaultdict(list)
    rsi_detail_map = defaultdict(list)

    has_buy_trend = False
    has_sell_trend = False
    has_buy_ema = False
    has_sell_ema = False
    has_buy_rsi = False
    has_sell_rsi = False

    for tf in ALL_TIMEFRAMES:
        candles = klines_map.get(tf, [])
        analysis = analyze_timeframe(candles)
        if not analysis:
            continue

        tf_str = tf.upper()
        st_maj = analysis["st_major"]
        ema = analysis["ema_info"]
        rsi = analysis["rsi_tue"]

        # 1. STRICT TREND FILTER: Only record if Flat S/R or Flipped color in last 1-3 candles
        if st_maj["is_flat"]:
            if st_maj["is_buy"]:
                trend_detail_map["Xanh Flat"].append(tf_str)
                has_buy_trend = True
            else:
                trend_detail_map["Đỏ Flat"].append(tf_str)
                has_sell_trend = True
        elif st_maj["just_flipped"]:
            if st_maj["is_buy"]:
                trend_detail_map["Đổi màu Xanh"].append(tf_str)
                has_buy_trend = True
            else:
                trend_detail_map["Đổi màu Đỏ"].append(tf_str)
                has_sell_trend = True

        # 2. STRICT EMA FILTER: Only record if Recent Crossover or Steep Expansion
        if ema["cross"] == "GOLDEN":
            ema_detail_map["Chớm cắt lên"].append(tf_str)
            has_buy_ema = True
        elif ema["cross"] == "DEATH":
            ema_detail_map["Chớm cắt xuống"].append(tf_str)
            has_sell_ema = True
        elif ema["is_expanding"]:
            if ema["direction"] == "BUY":
                ema_detail_map["Mở rộng lên"].append(tf_str)
                has_buy_ema = True
            else:
                ema_detail_map["Mở rộng xuống"].append(tf_str)
                has_sell_ema = True

        # 3. STRICT RSI FILTER: Only record if Divergence OR Extreme Zones (<30 / >70)
        if rsi["divergence"] == "BULLISH":
            rsi_detail_map["Phân kỳ tăng"].append(tf_str)
            has_buy_rsi = True
        elif rsi["divergence"] == "BEARISH":
            rsi_detail_map["Phân kỳ giảm"].append(tf_str)
            has_sell_rsi = True
        elif rsi["extreme"] == "OVERSOLD":
            rsi_detail_map["Quá bán"].append(tf_str)
            has_buy_rsi = True
        elif rsi["extreme"] == "OVERBOUGHT":
            rsi_detail_map["Quá mua"].append(tf_str)
            has_sell_rsi = True

    # Line Outputs
    trend_line = format_indicator_line(trend_detail_map)
    ema_line = format_indicator_line(ema_detail_map)
    rsi_line = format_indicator_line(rsi_detail_map)

    # Indicator Presence Checks
    is_trend_ok = trend_line != "KHÔNG CÓ TÍN HIỆU"
    is_ema_ok = ema_line != "KHÔNG CÓ TÍN HIỆU"
    is_rsi_ok = rsi_line != "KHÔNG CÓ TÍN HIỆU"

    indicator_count = (1 if is_trend_ok else 0) + (1 if is_ema_ok else 0) + (1 if is_rsi_ok else 0)

    # Directional Conflict Check
    any_buy = has_buy_trend or has_buy_ema or has_buy_rsi
    any_sell = has_sell_trend or has_sell_ema or has_sell_rsi

    is_conflict = (has_sell_trend and has_buy_rsi) or (has_buy_trend and has_sell_rsi) or (any_buy and any_sell and (has_buy_trend != has_sell_trend))

    # Conclusion Rating Logic
    if is_conflict and indicator_count >= 2:
        conclusion_str = "TÍN HIỆU XUNG ĐỘT (Đứng ngoài / Chờ phản ứng)"
    elif indicator_count == 3:
        if any_buy and not any_sell:
            conclusion_str = "ĐẠT 3/3 (Setup A+ BUY)"
        elif any_sell and not any_buy:
            conclusion_str = "ĐẠT 3/3 (Setup A+ SELL)"
        else:
            conclusion_str = "TÍN HIỆU XUNG ĐỘT (Đứng ngoài / Chờ phản ứng)"
    elif indicator_count == 2:
        conclusion_str = "ĐẠT 2/3 (Theo dõi thêm)"
    else:
        conclusion_str = f"ĐẠT {indicator_count}/3 (Theo dõi thêm)"

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
    if "ĐẠT 3/3" in report_text or "ĐẠT 2/3" in report_text:
        return report_text
    return None

def scan_market(coins_list=None):
    """
    Market Watchlist Scanner using strict action-based logic.
    """
    if not coins_list or len(coins_list) == 0:
        coins_list = TOP_COINS

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        scan_futures = [executor.submit(get_coin_report, coin) for coin in coins_list]
        for future in scan_futures:
            res = future.result()
            if res and ("ĐẠT 3/3" in res or "ĐẠT 2/3" in res):
                results.append(res)

    if not results:
        return "⚪ Hiện tại các Top Coin chưa có setup đồng thuận rõ ràng."

    return "\n\n----------------------------\n\n".join(results[:5])
