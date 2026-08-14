from binance_api import get_klines, get_ticker_24h
from ta_engine import calculate_supertrend, format_price_level

def check_btc_4h_signal():
    """
    Dedicated 24/7 BTC 4H Auto-Monitor Signal Evaluator.
    Returns (triggered, signal_type, alert_message)
    100% SILENT when price is floating in the middle (neither Blue <= 0.8% nor Red <= 0.8%).
    """
    candles = get_klines("BTCUSDT", "4h", 100)
    ticker = get_ticker_24h("BTCUSDT")

    if not candles or len(candles) < 20 or not ticker:
        return False, None, None

    current_price = ticker["lastPrice"]
    price_str = format_price_level(current_price)

    # 1. Supertrend Nhanh (Blue / Red): ATR 10, Multiplier 3
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0)
    # 2. Supertrend Chậm (Green / Yellow): ATR 15, Multiplier 10
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0)

    if not low_fast or not low_slow or not up_fast or not up_slow:
        return False, None, None

    val_blue = low_fast[-1]
    val_red = up_fast[-1]
    val_green = low_slow[-1]
    val_yellow = up_slow[-1]

    diff_blue = ((current_price - val_blue) / current_price) * 100.0
    diff_red = ((val_red - current_price) / current_price) * 100.0

    # 1. KHI GIÁ RƠI VỀ GẦN BLUE (diff_blue <= 0.8%)
    if 0.0 <= diff_blue <= 0.8:
        val_blue_str = format_price_level(val_blue)
        val_green_str = format_price_level(val_green)
        gap_green = ((val_blue - val_green) / val_blue) * 100.0 if val_blue > 0 else 0.0

        if 0.0 <= gap_green <= 3.0:
            green_line_str = f"▫️ <b>Đỡ phụ Green 🟢:</b> {val_green_str} (ngay dưới Blue {gap_green:.2f}% - <b>HỖ TRỢ KÉP CỰC CỨNG</b>)"
            sig_type = "DOUBLE_SUPPORT_BLUE"
        else:
            green_line_str = f"▫️ <b>Đỡ phụ Green 🟢:</b> {val_green_str} (cách Blue {gap_green:.2f}%)"
            sig_type = "SINGLE_SUPPORT_BLUE"

        alert_msg = (
            f"🚨 <b>CẢNH BÁO BTC 4H: CHẠM VÙNG HỖ TRỢ XANH 🔵</b>\n\n"
            f"▫️ <b>Giá hiện tại:</b> {price_str} USDT\n"
            f"▫️ <b>Mốc Blue 🔵:</b> {val_blue_str} (cách {diff_blue:.1f}% - Đang test)\n"
            f"{green_line_str}\n\n"
            f"👉 <i>Hành động: Canh phản ứng nến rút râu / đảo chiều quanh {val_blue_str}!</i>"
        )
        return True, sig_type, alert_msg

    # 2. KHI GIÁ HỒI LÊN GẦN RED (abs(diff_red) <= 0.8%)
    if 0.0 <= abs(diff_red) <= 0.8:
        val_red_str = format_price_level(val_red)
        val_yellow_str = format_price_level(val_yellow)
        gap_yellow = ((val_yellow - val_red) / val_red) * 100.0 if val_red > 0 else 0.0

        if 0.0 <= gap_yellow <= 3.0:
            yellow_line_str = f"▫️ <b>Cản phụ Yellow 🟡:</b> {val_yellow_str} (ngay trên Red {gap_yellow:.2f}% - <b>CẢN KÉP MẠNH</b>)"
            sig_type = "DOUBLE_RESIST_RED"
        else:
            yellow_line_str = f"▫️ <b>Cản phụ Yellow 🟡:</b> {val_yellow_str} (cách Red {gap_yellow:.2f}%)"
            sig_type = "SINGLE_RESIST_RED"

        alert_msg = (
            f"🚨 <b>CẢNH BÁO BTC 4H: CHẠM VÙNG CẢN ĐỎ 🔴</b>\n\n"
            f"▫️ <b>Giá hiện tại:</b> {price_str} USDT\n"
            f"▫️ <b>Mốc Red 🔴:</b> {val_red_str} (cách {abs(diff_red):.1f}% - Đang test)\n"
            f"{yellow_line_str}\n\n"
            f"👉 <i>Hành động: Canh phản ứng đảo chiều giảm / chốt lời quanh {val_red_str}!</i>"
        )
        return True, sig_type, alert_msg

    # Floating in middle -> 100% SILENT
    return False, None, None

def get_coin_report(symbol="BTC"):
    """
    Returns single manual BTC 4H report.
    """
    ticker = get_ticker_24h("BTCUSDT")
    candles = get_klines("BTCUSDT", "4h", 100)

    if not ticker or not candles:
        return "❌ Không thể lấy dữ liệu BTC 4H từ Binance."

    curr_price = ticker["lastPrice"]
    low_fast, up_fast, trend_fast = calculate_supertrend(candles, period=10, multiplier=3.0)
    low_slow, up_slow, trend_slow = calculate_supertrend(candles, period=15, multiplier=10.0)

    if not low_fast or not low_slow or not up_fast or not up_slow:
        return "❌ Không đủ dữ liệu nến BTC 4H."

    val_blue = low_fast[-1]
    val_red = up_fast[-1]
    val_green = low_slow[-1]
    val_yellow = up_slow[-1]

    diff_blue = ((curr_price - val_blue) / curr_price) * 100.0
    diff_green = ((curr_price - val_green) / curr_price) * 100.0
    diff_red = ((val_red - curr_price) / curr_price) * 100.0
    diff_yellow = ((val_yellow - curr_price) / curr_price) * 100.0

    report = [
        "🤖 <b>BÁO CÁO TRẠNG THÁI BTC 4H</b>",
        f"Giá hiện tại: <b>{format_price_level(curr_price)} USDT</b>\n",
        f"🔵 Blue Support (Nhanh): <b>{format_price_level(val_blue)}</b> (+{diff_blue:.1f}%)",
        f"🟢 Green Support (Chậm) : <b>{format_price_level(val_green)}</b> (+{diff_green:.1f}%)",
        f"🔴 Red Resistance (Nhanh): <b>{format_price_level(val_red)}</b> (-{diff_red:.1f}%)",
        f"🟡 Yellow Resistance (Chậm): <b>{format_price_level(val_yellow)}</b> (-{diff_yellow:.1f}%)"
    ]
    return "\n".join(report)

def scan_market(coins_list=None):
    return get_coin_report("BTC")
