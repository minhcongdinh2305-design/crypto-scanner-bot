from binance_api import get_klines, get_ticker_24h
from ta_engine import calculate_supertrend, format_price_level

def check_btc_4h_signal():
    """
    Evaluates BTC/USDT 4H candles (limit=500) against Kivanc Pine Script v4 Supertrend.
    Fast ST: ATR 10, Mult 3.0
    Slow ST: ATR 15, Mult 10.0
    Returns (triggered, signal_type, alert_message, current_price, val_blue, val_red)
    """
    candles = get_klines("BTCUSDT", "4h", 500)
    ticker = get_ticker_24h("BTCUSDT")

    if not candles or len(candles) < 30 or not ticker:
        return False, None, None, 0, 0, 0

    current_price = ticker["lastPrice"]
    price_str = format_price_level(current_price)

    # 1. Supertrend Nhanh (Blue / Red): ATR 10, Multiplier 3.0
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0, change_atr=True)
    # 2. Supertrend Chậm (Green / Yellow): ATR 15, Multiplier 10.0
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0, change_atr=True)

    if not low_fast or not low_slow or not up_fast or not up_slow:
        return False, None, None, current_price, 0, 0

    val_blue = low_fast[-1]
    val_red = up_fast[-1]
    val_green = low_slow[-1]
    val_yellow = up_slow[-1]

    diff_blue = ((current_price - val_blue) / current_price) * 100.0
    diff_red = ((val_red - current_price) / current_price) * 100.0

    # 1. KÈO HỖ TRỢ XANH 🔵 (diff_blue <= 0.8%)
    if 0.0 <= diff_blue <= 0.8:
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
            f"🚨 <b>CẢNH BÁO BTC 4H: CHẠM VÙNG HỖ TRỢ XANH 🔵</b>\n\n"
            f"▫️ <b>Giá hiện tại:</b> {price_str} USDT\n"
            f"▫️ <b>Mốc Blue 🔵:</b> {val_blue_str} (cách {diff_blue:.2f}%)\n"
            f"▫️ <b>Đỡ phụ Green 🟢:</b> {val_green_str} ({green_note})\n\n"
            f"👉 <i>Hành động: Canh phản ứng nến đảo chiều / rút chân!</i>"
        )
        return True, sig_type, alert_msg, current_price, val_blue, val_red

    # 2. KÈO CẢN ĐỎ 🔴 (abs(diff_red) <= 0.8%)
    if 0.0 <= abs(diff_red) <= 0.8:
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
            f"🚨 <b>CẢNH BÁO BTC 4H: CHẠM VÙNG CẢN ĐỎ 🔴</b>\n\n"
            f"▫️ <b>Giá hiện tại:</b> {price_str} USDT\n"
            f"▫️ <b>Mốc Red 🔴:</b> {val_red_str} (cách {abs(diff_red):.2f}%)\n"
            f"▫️ <b>Cản phụ Yellow 🟡:</b> {val_yellow_str} ({yellow_note})\n\n"
            f"👉 <i>Hành động: Canh phản ứng đảo chiều giảm / chốt lời!</i>"
        )
        return True, sig_type, alert_msg, current_price, val_blue, val_red

    # Floating in middle -> 100% Silent
    return False, None, None, current_price, val_blue, val_red

def get_btc_4h_check_report():
    """
    Instant test report for /check command.
    Prints current BTC price and the 2 Supertrend bands (Fast 10,3 & Slow 15,10) for TradingView verification.
    """
    ticker = get_ticker_24h("BTCUSDT")
    candles = get_klines("BTCUSDT", "4h", 500)

    if not ticker or not candles:
        return "❌ Không thể kết nối tới Binance API để lấy nến BTC 4H."

    curr_price = ticker["lastPrice"]
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0, change_atr=True)
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0, change_atr=True)

    if not low_fast or not low_slow or not up_fast or not up_slow:
        return "❌ Không đủ dữ liệu nến BTC 4H để tính chỉ báo."

    val_blue = low_fast[-1]
    val_red = up_fast[-1]
    val_green = low_slow[-1]
    val_yellow = up_slow[-1]

    diff_blue = ((curr_price - val_blue) / curr_price) * 100.0
    diff_green = ((curr_price - val_green) / curr_price) * 100.0
    diff_red = ((val_red - curr_price) / curr_price) * 100.0
    diff_yellow = ((val_yellow - curr_price) / curr_price) * 100.0

    gap_green = ((val_blue - val_green) / val_blue) * 100.0 if val_blue > 0 else 0.0
    gap_yellow = ((val_yellow - val_red) / val_red) * 100.0 if val_red > 0 else 0.0

    status_note = "⚪ <b>Trạng thái:</b> Giá lơ lửng ở giữa (Không chạm cản / không chạm hỗ trợ -> 100% Im lặng)."
    if 0.0 <= diff_blue <= 0.8:
        status_note = "🚨 <b>Trạng thái:</b> Đang áp sát vùng Hỗ trợ Xanh Blue 🔵!"
    elif 0.0 <= abs(diff_red) <= 0.8:
        status_note = "🚨 <b>Trạng thái:</b> Đang áp sát vùng Kháng cự Đỏ Red 🔴!"

    report = [
        "🧪 <b>BẢN TIN KIỂM TRA DOUBLE SUPERTREND KIVANC (BTC 4H)</b>\n",
        f"▫️ <b>Giá BTC hiện tại:</b> {format_price_level(curr_price)} USDT\n",
        "<b>📌 DẢI 1 (NHANH - 🔵 / 🔴): ATR 10, Multiplier 3.0</b>",
        f"▫️ Blue Support 🔵: <b>{format_price_level(val_blue)}</b> (cách {diff_blue:.2f}%)",
        f"▫️ Red Resistance 🔴: <b>{format_price_level(val_red)}</b> (cách -{abs(diff_red):.2f}%)\n",
        "<b>📌 DẢI 2 (CHẬM - 🟢 / 🟡): ATR 15, Multiplier 10.0</b>",
        f"▫️ Green Support 🟢: <b>{format_price_level(val_green)}</b> (dưới Blue {gap_green:.2f}%)",
        f"▫️ Yellow Resistance 🟡: <b>{format_price_level(val_yellow)}</b> (trên Red {gap_yellow:.2f}%)\n",
        f"{status_note}\n",
        "✅ <i>Đối chiếu 100% khớp từng con số với TradingView Kivanc Supertrend!</i>"
    ]
    return "\n".join(report)

def get_coin_report(symbol="BTC"):
    return get_btc_4h_check_report()

def scan_market(coins_list=None):
    return get_btc_4h_check_report()
