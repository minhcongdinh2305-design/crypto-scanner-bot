#!/usr/bin/env python3
"""
Telegram Bot Engine + TradingView Webhook Listener
Pure Python Implementation. Zero PIP dependencies required!
Compatible with 24/7 Cloud Deployment (Render / Railway / Replit / Heroku).

Features:
1. Listens for Telegram commands (/btc, /eth, /scan, /help) in Groups & PMs.
2. Runs an HTTP Webhook Server (Dynamic PORT binding for Cloud Hosts) to receive direct alerts from TradingView!
3. Automatically forwards custom TradingView alerts into your Telegram Group Chat.
"""
import urllib.request
import urllib.parse
import json
import time
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from scanner import get_coin_report, scan_market

CONFIG_FILE = "config.json"
# Cloud Host Port Binding (Render / Railway default PORT env, fallback to 8080)
WEBHOOK_PORT = int(os.environ.get("PORT", 8080))

def load_config():
    """Load configuration from config.json or Environment Variables."""
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass
            
    # Env vars override config file for Cloud Deployments!
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        config_data["telegram_token"] = token
        
    chat_id = os.environ.get("GROUP_CHAT_ID")
    if chat_id:
        config_data["group_chat_id"] = chat_id
        
    return config_data

def save_config(config_data):
    """Save config to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

def telegram_api(token, method, params=None):
    """Call Telegram Bot API endpoint."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        data = None
        if params:
            data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Telegram API Error ({method}): {e}")
        return None

def send_message(token, chat_id, text):
    """Send text message back to user or group in Telegram."""
    return telegram_api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

# GLOBAL STATE
config = load_config()
bot_token = config.get("telegram_token", "")
default_chat_id = config.get("group_chat_id", "")

class WebhookRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler to receive TradingView Webhook Alerts."""
    
    def do_POST(self):
        global bot_token, default_chat_id
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        print(f"\n🚨 RECEIVED TRADINGVIEW WEBHOOK ALERT: {post_data}")

        # Send HTTP 200 OK back to TradingView immediately
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

        # Format notification card
        signal_text = ""
        try:
            payload = json.loads(post_data)
            symbol = payload.get("ticker", payload.get("symbol", "CRYPTO")).upper()
            signal = payload.get("signal", payload.get("action", "TÍN HIỆU")).upper()
            price = payload.get("price", payload.get("close", "N/A"))
            interval = payload.get("timeframe", payload.get("interval", ""))
            note = payload.get("note", payload.get("message", ""))

            signal_text = (
                f"🚨 **TÍN HIỆU TỪ TRADINGVIEW (HỆ THỐNG RIÊNG)**\n\n"
                f"🪙 **Cặp giao dịch**: `{symbol}`\n"
                f"🎯 **Tín hiệu**: **{signal}**\n"
                f"💵 **Giá hiện tại**: `{price}`\n"
                f"⏱ **Khung time**: `{interval}`\n"
                f"📝 **Ghi chú**: {note if note else 'Chỉ báo riêng vừa kích hoạt!'}"
            )
        except Exception:
            # Fallback if TradingView sent plain text
            signal_text = f"🚨 **TÍN HIỆU TỰ ĐỘNG TỪ TRADINGVIEW**\n\n{post_data}"

        # Broadcast to Group Chat
        if bot_token and default_chat_id:
            send_message(bot_token, default_chat_id, signal_text)
            print(f"✅ Alert forwarded to Telegram Chat ID: {default_chat_id}")
        else:
            print("⚠️ Chat ID chưa được lưu. Vui lòng nhắn 1 câu trong Telegram Group để Bot ghi nhớ Chat ID!")

    def do_GET(self):
        """Health check endpoint for Cloud Host (Render / Railway / UptimeRobot)."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Bot TradingView Webhook 24/7 is Active!</h1></body></html>")

def start_webhook_server():
    """Start Webhook Server in a background thread."""
    server_address = ('', WEBHOOK_PORT)
    httpd = HTTPServer(server_address, WebhookRequestHandler)
    print(f"🌐 TRADINGVIEW WEBHOOK SERVER ĐANG CHẠY TẠI PORT: {WEBHOOK_PORT}")
    httpd.serve_forever()

def handle_update(token, update, bot_username=""):
    """Process incoming Telegram message."""
    global default_chat_id, config
    
    message = update.get("message")
    if not message:
        return
        
    chat_id = message["chat"]["id"]
    
    # Save the latest group/chat ID automatically for Webhook alerts!
    if str(chat_id) != str(default_chat_id):
        default_chat_id = chat_id
        config["group_chat_id"] = chat_id
        save_config(config)
        print(f"📌 Đã lưu Chat ID nhóm của bạn: {chat_id}")

    text = message.get("text", "").strip()
    if not text:
        return

    # STRICT SILENT FILTER: Must start with '/' or tag bot
    is_command = text.startswith("/")
    is_tagged = bot_username and f"@{bot_username.lower()}" in text.lower()
    
    if not is_command and not is_tagged:
        return

    clean_text = text.split("@")[0].strip()
    if clean_text.startswith("/"):
        clean_text = clean_text[1:].strip()
        
    text_lower = clean_text.lower()
    
    if text_lower in ["start", "help"]:
        welcome = (
            "🤖 **TRỢ LÝ CHỈ BÁO CRYPTO & TRADINGVIEW WEBHOOK BOT (24/7 CLOUD)**\n\n"
            "Bot đang hoạt động 24/7 trên Cloud, nhận tín hiệu trực tiếp từ TradingView!\n\n"
            "📌 **CÂU LỆNH SỬ DỤNG:**\n"
            "• `/btc`, `/eth`, `/sol`... : Xem chỉ báo nhanh\n"
            "• `/scan` : Quét Top 15 Coin\n"
            "• `/webhook` : Hướng dẫn cài Webhook TradingView\n"
            "• `/help` : Xem trợ giúp\n"
        )
        send_message(token, chat_id, welcome)
        return

    if text_lower == "webhook":
        info = (
            "🌐 **HƯỚNG DẪN CÀI ĐẶT TRADINGVIEW WEBHOOK (24/7)**\n\n"
            "1. Trên TradingView ➔ Mở chỉ báo của bạn ➔ Bấm **Tạo Cảnh Báo (Create Alert)**\n"
            "2. Mục **Notifications** ➔ Tích chọn **Webhook URL**\n"
            "3. Nhập URL Server Webhook của Bot\n"
            "4. Mục **Message**, dán định dạng JSON:\n"
            "```json\n"
            "{\n"
            '  "ticker": "{{ticker}}",\n'
            '  "price": "{{close}}",\n'
            '  "signal": "MUA (LONG)",\n'
            '  "timeframe": "{{interval}}"\n'
            "}\n"
            "```\n"
            "Mỗi khi chỉ báo của bạn kích hoạt ➔ Bot tự động bắn báo động vào Group này!"
        )
        send_message(token, chat_id, info)
        return

    if text_lower == "scan":
        send_message(token, chat_id, "⏳ Đang quét dữ liệu Top 15 Coin... Vui lòng đợi 0.5s...")
        report = scan_market()
        send_message(token, chat_id, report)
        return

    # Check coin symbol (e.g. /btc, /sol)
    symbol = text_lower.replace("check", "").strip()
    if len(symbol) >= 2 and len(symbol) <= 10 and symbol.isalnum():
        send_message(token, chat_id, f"⏳ Đang đọc dữ liệu nến & tính chỉ báo cho **{symbol.upper()}**...")
        report = get_coin_report(symbol)
        send_message(token, chat_id, report)

def run_bot():
    global bot_token
    config_data = load_config()
    bot_token = config_data.get("telegram_token", "")
    
    if not bot_token:
        print("❌ Chưa có Telegram Bot Token trong config.json hoặc biến TELEGRAM_BOT_TOKEN!")
        sys.exit(1)

    # Verify Token
    me = telegram_api(bot_token, "getMe")
    if not me or not me.get("ok"):
        print("❌ Token không chính xác hoặc không thể kết nối tới Telegram!")
        sys.exit(1)

    bot_info = me["result"]
    bot_username = bot_info.get('username', '')

    # Start Webhook HTTP Server in background thread
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()

    print("\n" + "="*60)
    print(f"🚀 TELEGRAM BOT + TRADINGVIEW WEBHOOK 24/7 ĐÃ SẴN SÀNG!")
    print(f"• Bot Username: @{bot_username}")
    print(f"• Webhook Port: {WEBHOOK_PORT}")
    print(f"• Chế độ: 24/7 Cloud Host Compatible!")
    print("="*60 + "\n")

    offset = 0
    while True:
        try:
            updates = telegram_api(bot_token, "getUpdates", {"offset": offset, "timeout": 20})
            if updates and updates.get("ok"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    handle_update(bot_token, update, bot_username)
        except Exception as e:
            print(f"Error in polling loop: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
