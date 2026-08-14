# 🤖 TRỢ LÝ BOT KIỂM TRA CHỈ BÁO & SCANNER CRYPTO

Bot thông minh giúp trader kiểm tra nhanh giá và các chỉ báo kỹ thuật (**RSI 14, EMA 20/50/200, MACD**) trên 4 khung thời gian (**15m, 1h, 4h, 1D**) lấy dữ liệu trực tiếp từ Binance API (Miễn phí 100%).

---

## ⚡ HƯỚNG DẪN DÙNG THỬ TRỰC TIẾP TRÊN MÁY TÍNH (KHÔNG CẦN TELEGRAM TOKEN)

Bạn có thể chạy thử nghiệm ngay lập tức trên máy tính của bạn:

1. Mở Terminal/Command Prompt
2. Chạy lệnh:
```bash
python3 cli_test.py
```
3. Nhập mã coin cần soi (ví dụ `btc`, `eth`, `sol`, `near`) hoặc chọn `2` để Quét Top 15 Coin!

---

## 📱 HƯỚNG DẪN KẾT NỐI VỚI TELEGRAM (KHI BẠN SẴN SÀNG)

### Bước 1: Lấy Token từ Telegram (Mất 30 giây)
1. Mở Telegram, tìm kiếm **`@BotFather`**
2. Nhắn lệnh `/newbot`
3. Nhập tên hiển thị cho Bot (Ví dụ: `MyTraderBot`)
4. Nhập username cho Bot (Phải kết thúc bằng chữ `bot`, ví dụ: `my_trade_scanner_bot`)
5. `@BotFather` sẽ gửi mã Token (Ví dụ: `7890123456:AAFx...`)

### Bước 2: Khởi động Telegram Bot
Chạy lệnh:
```bash
python3 bot.py
```
Nhập mã Token khi được hỏi. Bot sẽ bắt đầu lắng nghe và trả lời bạn ngay trên Telegram!
