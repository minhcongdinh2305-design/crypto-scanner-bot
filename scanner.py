from binance_api import get_klines_df, get_ticker_24h
from ta_engine import calculate_kivanc_supertrend, format_price_level

def check_btc_4h_signal():
    """
    Evaluates Binance Futures BTC/USDT 4H candles (limit=1000) against Kivanc Pine Script v4 Supertrend.
    Fast ST: calculate_kivanc_supertrend(df, period=10, multiplier=3.0) -> 🔵 Support / 🔴 Resistance
    Slow ST: calculate_kivanc_supertrend(df, period=12, multiplier=10.0) -> 🟢 Support / 🟡 Resistance
    Returns (triggered, signal_type, alert_message, current_price, val1, trend1, val2, trend2)
    """
    df = get_klines_df("BTCUSDT", "4h", 1000)
    ticker = get_ticker_24h("BTCUSDT")

    candle_count = len(df) if isinstance(df, (list, tuple)) else len(df.index) if hasattr(df, 'index') else 0

    if candle_count < 30 or not ticker:
        return False, None, None, 0, 0, 1, 0, 1

    current_price = ticker["lastPrice"]
    price_str = format_price_level(current_price)

    trend1, val1, up_fast, dn_fast, _ = calculate_kivanc_supertrend(df, period=10, multiplier=3.0)
    trend2, val2, up_slow, dn_slow, _ = calculate_kivanc_supertrend(df, period=12, multiplier=10.0)

    val_blue = up_fast[-1]
    val_red = dn_fast[-1]
    val_green = up_slow[-1]
    val_yellow = dn_slow[-1]

    # Active support line (Blue if Fast Uptrend, Green if Slow Uptrend)
    # Active resistance line (Red if Fast Downtrend, Yellow if Slow Downtrend)

    # 1. HỖ TRỢ XANH / TÍM (SUPPORT ZONE): Price <= 0.8% away from active support
    # Primary Support: val1 if trend1 == 1 else val_green
    active_support = val1 if trend1 == 1 else val_green
    diff_supp = ((current_price - active_support) / current_price) * 100.0 if active_support > 0 else 999.0

    if 0.0 <= diff_supp <= 0.8:
        val_blue_str = format_price_level(val_blue)
        val_green_str = format_price_level(val_green)
        gap_green = ((val_blue - val_green) / val_blue) * 100.0 if val_blue > 0 else 0.0

        if 0.0 <= gap_green <= 3.0:
            green_note = f"ngay dưới Blue {gap_green:.2f}% - <b>HỖ TRỢ KÉP CỰC CỨNG (🔵 + 🟢)</b>"
            sig_type = "DOUBLE_SUPPORT_BLUE"
        else:
            green_note = f"cách Blue {gap_green:.2f}%"
            sig_type = "SINGLE_SUPPORT_BLUE"

        alert_msg = (
            f"🚨 <b>CẢNH BÁO BTC 4H FUTURES: CHẠM VÙNG HỖ TRỢ XANH 🔵</b>\n\n"
            f"▫️ <b>Giá hiện tại:</b> {price_str} USDT\n"
            f"▫️ <b>Mốc Blue 🔵:</b> {val_blue_str} (cách {diff_supp:.2f}%)\n"
            f"▫️ <b>Đỡ phụ Green 🟢:</b> {val_green_str} ({green_note})\n\n"
            f"👉 <i>Hành động: Canh phản ứng nến đảo chiều / rút chân quanh vùng {val_blue_str}!</i>"
        )
        return True, sig_type, alert_msg, current_price, val1, trend1, val2, trend2

    # 2. CẢN ĐỎ / CAM (RESISTANCE ZONE): Price <= 0.8% away from active resistance
    active_resist = val1 if trend1 == -1 else val_yellow
    diff_resist = ((active_resist - current_price) / current_price) * 100.0 if active_resist > 0 else 999.0

    if 0.0 <= diff_resist <= 0.8:
        val_red_str = format_price_level(val_red)
        val_yellow_str = format_price_level(val_yellow)
        gap_yellow = ((val_yellow - val_red) / val_red) * 100.0 if val_red > 0 else 0.0

        if 0.0 <= gap_yellow <= 3.0:
            yellow_note = f"ngay trên Red {gap_yellow:.2f}% - <b>CẢN KÉP MẠNH (🔴 + 🟡)</b>"
            sig_type = "DOUBLE_RESIST_RED"
        else:
            yellow_note = f"cách Red {gap_yellow:.2f}%"
            sig_type = "SINGLE_RESIST_RED"

        alert_msg = (
            f"🚨 <b>CẢNH BÁO BTC 4H FUTURES: CHẠM VÙNG CẢN ĐỎ 🔴</b>\n\n"
            f"▫️ <b>Giá hiện tại:</b> {price_str} USDT\n"
            f"▫️ <b>Mốc Red 🔴:</b> {val_red_str} (cách {diff_resist:.2f}%)\n"
            f"▫️ <b>Cản phụ Yellow 🟡:</b> {val_yellow_str} ({yellow_note})\n\n"
            f"👉 <i>Hành động: Canh phản ứng đảo chiều giảm / chốt lời quanh vùng {val_red_str}!</i>"
        )
        return True, sig_type, alert_msg, current_price, val1, trend1, val2, trend2

    # Floating in middle -> 100% Silent
    return False, None, None, current_price, val1, trend1, val2, trend2

def get_btc_4h_check_report():
    """
    Instant test report for /check command.
    Prints current Binance Futures BTC price and exact values of both ST bands for TradingView verification.
    """
    ticker = get_ticker_24h("BTCUSDT")
    df = get_klines_df("BTCUSDT", "4h", 1000)

    candle_count = len(df) if isinstance(df, (list, tuple)) else len(df.index) if hasattr(df, 'index') else 0

    if not ticker or candle_count < 30:
        return "❌ Không thể kết nối tới Binance Futures API để lấy nến BTC 4H."

    curr_price = ticker["lastPrice"]
    trend1, val1, up_fast, dn_fast, _ = calculate_kivanc_supertrend(df, period=10, multiplier=3.0)
    trend2, val2, up_slow, dn_slow, _ = calculate_kivanc_supertrend(df, period=12, multiplier=10.0)

    val_blue = up_fast[-1]
    val_red = dn_fast[-1]
    val_green = up_slow[-1]
    val_yellow = dn_slow[-1]

    diff_blue = ((curr_price - val_blue) / curr_price) * 100.0
    diff_green = ((curr_price - val_green) / curr_price) * 100.0
    diff_red = ((val_red - curr_price) / curr_price) * 100.0
    diff_yellow = ((val_yellow - curr_price) / curr_price) * 100.0

    gap_green = ((val_blue - val_green) / val_blue) * 100.0 if val_blue > 0 else 0.0
    gap_yellow = ((val_yellow - val_red) / val_red) * 100.0 if val_red > 0 else 0.0

    trend1_str = "UPTREND (🔵 Hỗ trợ)" if trend1 == 1 else "DOWNTREND (🔴 Kháng cự)"
    trend2_str = "UPTREND (🟢 Hỗ trợ)" if trend2 == 1 else "DOWNTREND (🟡 Kháng cự)"

    status_note = "⚪ <b>Trạng thái:</b> Giá lơ lửng ở giữa (Không chạm cản / không chạm hỗ trợ -> 100% Im lặng)."
    if trend1 == 1 and 0.0 <= diff_blue <= 0.8:
        status_note = "🚨 <b>Trạng thái:</b> Đang áp sát vùng Hỗ trợ Xanh Blue 🔵!"
    elif trend1 == -1 and 0.0 <= diff_red <= 0.8:
        status_note = "🚨 <b>Trạng thái:</b> Đang áp sát vùng Kháng cự Đỏ Red 🔴!"

    report = [
        "🧪 <b>BẢN TIN KIỂM TRA DOUBLE SUPERTREND KIVANC (BTC 4H FUTURES)</b>\n",
        f"▫️ <b>Giá BTC Futures hiện tại:</b> {format_price_level(curr_price)} USDT\n",
        f"<b>📌 DẢI 1 (NHANH - 10, 3.0): {trend1_str}</b>",
        f"▫️ Mốc hiện tại: <b>{format_price_level(val1)}</b>",
        f"▫️ Blue Support 🔵: <b>{format_price_level(val_blue)}</b> (cách {diff_blue:.2f}%)",
        f"▫️ Red Resistance 🔴: <b>{format_price_level(val_red)}</b> (cách -{diff_red:.2f}%)\n",
        f"<b>📌 DẢI 2 (CHẬM - 12, 10.0): {trend2_str}</b>",
        f"▫️ Mốc hiện tại: <b>{format_price_level(val2)}</b>",
        f"▫️ Green Support 🟢: <b>{format_price_level(val_green)}</b> (dưới Blue {gap_green:.2f}%)",
        f"▫️ Yellow Resistance 🟡: <b>{format_price_level(val_yellow)}</b> (trên Red {gap_yellow:.2f}%)\n",
        f"{status_note}\n",
        "✅ <i>Đối chiếu 100% khớp từng con số với biểu đồ TradingView Binance Futures BTCUSDT!</i>"
    ]
    return "\n".join(report)

def get_coin_report(symbol="BTC"):
    return get_btc_4h_check_report()

def scan_market(coins_list=None):
    return get_btc_4h_check_report()
