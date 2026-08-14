from binance_api import get_ticker_24h, get_klines, fetch_multi_klines_parallel
from ta_engine import analyze_timeframe
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

DEFAULT_WATCHLIST = [
    "BTC", "ETH", "SOL", "LINK", "BNB", "NEAR", "SUI", "PEPE", "DOGE", "AVAX"
]

ALL_TIMEFRAMES = ["1d", "12h", "8h", "4h", "2h", "1h", "30m", "15m"]

def format_grouped_details(detail_map):
    if not detail_map:
        return "KHÔNG ĐẠT"
        
    parts = []
    for status, tfs in detail_map.items():
        if tfs:
            parts.append(f"{status} {', '.join(tfs)}")
            
    if not parts:
        return "KHÔNG ĐẠT"
        
    return f"OK ({', '.join(parts)})"

def get_coin_analysis_struct(symbol="BTC"):
    """
    Returns structured analysis object for a coin for scanner ranking & formatting.
    """
    symbol_upper = symbol.upper().replace("USDT", "")
    full_symbol = symbol_upper + "USDT"
    
    try:
        ticker, klines_map = fetch_multi_klines_parallel(full_symbol, ALL_TIMEFRAMES)
        if not ticker:
            return None

        trend_detail_map = defaultdict(list)
        ema_detail_map = defaultdict(list)
        rsi_detail_map = defaultdict(list)

        tf_analyses = {}
        htf_confluence_count = 0

        for tf in ALL_TIMEFRAMES:
            candles = klines_map.get(tf, [])
            analysis = analyze_timeframe(candles)
            if analysis:
                tf_analyses[tf] = analysis
                tf_str = tf.upper()
                
                # Count High Timeframe Confluence (1D, 12H, 8H, 4H)
                if tf in ["1d", "12h", "8h", "4h"] and analysis["st_major"]["is_buy"]:
                    htf_confluence_count += 1
                
                # 1. Trend Analysis
                st_maj = analysis["st_major"]
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

                # 2. EMA Analysis
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

                # 3. RSI Analysis
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
        if not primary_tf:
            return None

        # Line Formats
        trend_line = format_grouped_details(trend_detail_map)
        is_trend_pass = trend_line != "KHÔNG ĐẠT"

        ema_line = format_grouped_details(ema_detail_map)
        is_ema_pass = ema_line != "KHÔNG ĐẠT"

        rsi_line = format_grouped_details(rsi_detail_map)
        is_rsi_pass = rsi_line != "KHÔNG ĐẠT"

        passed_count = (1 if is_trend_pass else 0) + (1 if is_ema_pass else 0) + (1 if is_rsi_pass else 0)

        return {
            "symbol": symbol_upper,
            "full_symbol": full_symbol,
            "price": ticker["lastPrice"],
            "passed_count": passed_count,
            "score": primary_tf["score"],
            "htf_confluence_count": htf_confluence_count,
            "trend_line": trend_line,
            "ema_line": ema_line,
            "rsi_line": rsi_line
        }
    except Exception as e:
        print(f"❌ Error in get_coin_analysis_struct for {symbol}: {e}")
        return None

def get_coin_report(symbol="BTC"):
    """
    Returns single coin report matching required concise format.
    """
    data = get_coin_analysis_struct(symbol)
    if not data:
        return f"❌ Không tìm thấy dữ liệu cho **{symbol.upper()}/USDT**!"

    conclusion = "ĐẠT 3/3 (A+ Setup)" if data["passed_count"] == 3 else f"ĐẠT {data['passed_count']}/3 (Theo dõi thêm)"

    report = []
    report.append(f"🪙 **{data['symbol']}/USDT**\n")
    report.append(f"1. Trend: **{data['trend_line']}**")
    report.append(f"2. EMA: **{data['ema_line']}**")
    report.append(f"3. RSI: **{data['rsi_line']}**\n")
    report.append(f"👉 Kết luận: **{conclusion}**")

    return "\n".join(report)

def scan_market(coins_list=None):
    """
    Advanced Multi-Coin Watchlist Scanner with Ranking & Mandatory Output Format:
    🔥 KÈO NGON NHẤT: {TOP_SYMBOL} (ĐẠT {X}/3 - A+ Setup)
    1. Trend: ...
    2. EMA: ...
    3. RSI: ...

    -----------------------------------
    📊 XẾP HẠNG WATCHLIST:
    🥇 {COIN_1}: ĐẠT {X}/3 {Nếu 3/3 gắn sao ⭐}
    🥈 {COIN_2}: ĐẠT {X}/3
    🥉 {COIN_3}: ĐẠT {X}/3
    ...
    """
    if not coins_list or len(coins_list) == 0:
        coins_list = DEFAULT_WATCHLIST

    # Sanitize symbol list
    clean_coins = []
    for c in coins_list:
        sym = c.upper().replace("USDT", "").replace("/", "").strip()
        if sym and sym not in clean_coins:
            clean_coins.append(sym)

    # Parallel scan all coins
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_coin_analysis_struct, coin) for coin in clean_coins]
        for f in futures:
            try:
                res = f.result()
                if res:
                    results.append(res)
            except Exception as e:
                print(f"❌ Error in coin scan: {e}")

    if not results:
        return "⚪ Không thể lấy dữ liệu cho danh sách Watchlist."

    # Sorting & Ranking Algorithm:
    # 1. Passed Count (3 -> 2 -> 1 -> 0)
    # 2. HTF Confluence Count (1D, 12H, 8H, 4H)
    # 3. Overall Score
    results.sort(key=lambda x: (x["passed_count"], x["htf_confluence_count"], x["score"]), reverse=True)

    top_pick = results[0]
    top_setup_label = "A+ Setup" if top_pick["passed_count"] == 3 else "Theo dõi thêm"

    report = []
    # SECTION 1: TOP PICK (KÈO NGON NHẤT)
    report.append(f"🔥 **KÈO NGON NHẤT**: **{top_pick['symbol']}/USDT** (ĐẠT **{top_pick['passed_count']}/3** - {top_setup_label})")
    report.append(f"1. Trend: **{top_pick['trend_line']}**")
    report.append(f"2. EMA: **{top_pick['ema_line']}**")
    report.append(f"3. RSI: **{top_pick['rsi_line']}**")

    report.append("\n-----------------------------------")
    report.append("📊 **XẾP HẠNG WATCHLIST**:\n")

    # SECTION 2: WATCHLIST RANKINGS (🥇, 🥈, 🥉, 4., 5....)
    medals = ["🥇", "🥈", "🥉"]
    for idx, item in enumerate(results):
        rank_icon = medals[idx] if idx < 3 else f"{idx + 1}."
        star_tag = " ⭐" if item["passed_count"] == 3 else ""
        report.append(f"{rank_icon} **{item['symbol']}/USDT**: ĐẠT **{item['passed_count']}/3**{star_tag}")

    return "\n".join(report)
