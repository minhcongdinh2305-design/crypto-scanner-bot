#!/usr/bin/env python3
"""
Ultra-Lightweight TradingView Webhook -> Telegram Alert Bot
Pure Python Implementation (Zero PIP dependencies required).
Compatible with 24/7 Render / Railway / Replit Web Services.

Features:
1. Instant POST /webhook listener for TradingView Alert signals (< 0.05s latency).
2. GET / endpoint returning 200 OK for Render Web Service Health Checks.
3. Automatically captures & displays User Chat ID on /start or /chatid commands.
4. Forwards rich TradingView alerts directly to Telegram.
"""
import urllib.request
import urllib.parse
import json
import time
import os
import sys
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

CONFIG_FILE = "config.json"
WEBHOOK_PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://crypto-scanner-bot-zs2j.onrender.com")

def load_config():
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass
            
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        config_data["telegram_token"] = token
        
    chat_id = os.environ.get("GROUP_CHAT_ID")
    if chat_id:
        config_data["group_chat_id"] = chat_id
        
    return config_data

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

def telegram_api(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        data = None
        if params:
            data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Telegram API Error ({method}): {e}")
        return None

def send_message(token, chat_id, text):
    res = telegram_api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    })
    
    if not res or not res.get("ok"):
        res = telegram_api(token, "sendMessage", {
            "chat_id": chat_id,
            "text": text
        })
    return res

# GLOBAL STATE
config = load_config()
bot_token = config.get("telegram_token", "")
default_chat_id = config.get("group_chat_id", "")

class WebhookRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP Server handling:
    - GET / & GET /webhook -> 200 OK (Render Health Check)
    - POST / & POST /webhook -> Receives TradingView Alert & forwards to Telegram (< 0.05s)
    """
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html_response = (
            "<html><head><title>TradingView Webhook Bot</title></head>"
            "<body>"
            "<h1>🚀 TradingView Webhook Bot is Live 24/7!</h1>"
            "<p>Send POST requests to <code>/webhook</code> to forward alerts to Telegram.</p>"
            "</body></html>"
        )
        self.wfile.write(html_response.encode('utf-8'))

    def do_POST(self):
        global bot_token, default_chat_id
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
        
        print(f"\n🚨 [TRADINGVIEW WEBHOOK RECEIVED] -> {post_data}")

        # Send HTTP 200 OK response to TradingView immediately (< 0.01s)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "success", "message": "Alert received"}')

        # Format and forward alert payload to Telegram
        if not bot_token or not default_chat_id:
            print("⚠️ Missing bot_token or default_chat_id! Unable to forward alert to Telegram.")
            return

        alert_content = post_data.strip()
        formatted_alert = ""

        try:
            payload = json.loads(post_data)
            symbol = payload.get("ticker", payload.get("symbol", payload.get("coin", "CRYPTO"))).upper()
            action = payload.get("action", payload.get("signal", "CẢNH BÁO"))
            price = payload.get("price", payload.get("close", ""))
            msg = payload.get("message", payload.get("note", ""))
            
            lines = [f"🚨 <b>CẢNH BÁO {symbol} (TỪ TRADINGVIEW)</b>\n"]
            if action:
                lines.append(f"▫️ <b>Tín hiệu:</b> {action}")
            if price:
                lines.append(f"▫️ <b>Mức giá:</b> {price} USDT")
            if msg:
                lines.append(f"▫️ <b>Chi tiết:</b> {msg}")

            # Append any remaining extra JSON fields
            extra_fields = []
            for k, v in payload.items():
                if k not in ["ticker", "symbol", "coin", "action", "signal", "price", "close", "message", "note"]:
                    extra_fields.append(f"▫️ <b>{k}:</b> {v}")
            if extra_fields:
                lines.extend(extra_fields)

            formatted_alert = "\n".join(lines)

        except Exception:
            # Plain text alert payload
            formatted_alert = f"🚨 <b>CẢNH BÁO TỪ TRADINGVIEW</b>\n\n{alert_content}"

        # Asynchronously send alert to Telegram
        threading.Thread(
            target=send_message,
            args=(bot_token, default_chat_id, formatted_alert),
            daemon=True
        ).start()

    def log_message(self, format, *args):
        # Mute standard HTTP logs to keep console clean
        return

def start_webhook_server():
    """Starts HTTP Server in background thread for Render Web Service Port Binding."""
    try:
        server_address = ('0.0.0.0', WEBHOOK_PORT)
        httpd = HTTPServer(server_address, WebhookRequestHandler)
        print(f"🌐 TRADINGVIEW WEBHOOK SERVER RUNNING ON PORT: {WEBHOOK_PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ Web Server Exception on port {WEBHOOK_PORT}: {e}")

def handle_update(token, update, bot_username=""):
    """
    Process incoming Telegram update.
    Returns Chat ID and Webhook URL on /start or /chatid command.
    """
    global default_chat_id, config
    
    message = update.get("message")
    if not message:
        return
        
    chat_id = message["chat"]["id"]
    
    # Save chat_id dynamically
    if str(chat_id) != str(default_chat_id):
        default_chat_id = chat_id
        config["group_chat_id"] = chat_id
        save_config(config)
        print(f"✅ Auto-Alert Destination Chat ID updated to: {chat_id}")

    text = message.get("text", "").strip()
    if not text:
        return

    is_command = text.startswith("/")
    is_tagged = bot_username and f"@{bot_username.lower()}" in text.lower()
    
    if not is_command and not is_tagged:
        return

    try:
        clean_text = text.split("@")[0].strip()
        cmd = clean_text.split()[0].lower()
        if cmd.startswith("/"):
            cmd = cmd[1:]
        
        if cmd in ["start", "help", "chatid", "id"]:
            webhook_url = f"{RENDER_URL}/webhook"
            welcome = (
                "🤖 <b>TRỢ LÝ NHẬN CẢNH BÁO TRADINGVIEW WEBHOOK</b>\n\n"
                f"🆔 <b>Chat ID của bạn:</b> <code>{chat_id}</code>\n"
                f"🌐 <b>Webhook URL TradingView:</b>\n<code>{webhook_url}</code>\n\n"
                "📌 <b>HƯỚNG DẪN CẤU HÌNH TRÊN TRADINGVIEW:</b>\n"
                "1. Tạo Alert trên TradingView Chart.\n"
                "2. Ở mục <b>Notifications</b> ➔ Tích chọn <b>Webhook URL</b>.\n"
                f"3. Dán URL: <code>{webhook_url}</code>\n"
                "4. Ở mục <b>Message</b>: Nhập nội dung tin nhắn cảnh báo dạng Text hoặc JSON tùy ý!\n\n"
                "✅ <i>Bot sẽ nhận và bắn tin nhắn cảnh báo về Telegram tức thì (< 0.1 giây)!</i>"
            )
            send_message(token, chat_id, welcome)
            return

        if cmd in ["test", "check"]:
            test_msg = (
                "🧪 <b>BẢN TIN KIỂM TRA WEBHOOK TRADINGVIEW</b>\n\n"
                f"▫️ <b>Chat ID:</b> <code>{chat_id}</code>\n"
                f"▫️ <b>Trạng thái Webhook:</b> 🟢 Sẵn sàng nhận tín hiệu từ TradingView!\n"
                f"▫️ <b>URL:</b> <code>{webhook_url}</code>"
            )
            send_message(token, chat_id, test_msg)
            return

    except Exception as e:
        error_trace = f"❌ <b>LỖI THỰC THI BOT:</b>\n<code>{str(e)}</code>"
        send_message(token, chat_id, error_trace)

def run_bot():
    global bot_token
    config_data = load_config()
    bot_token = config_data.get("telegram_token", "")
    
    if not bot_token:
        print("❌ Chưa có Telegram Bot Token trong config.json hoặc biến TELEGRAM_BOT_TOKEN!")
        sys.exit(1)

    me = telegram_api(bot_token, "getMe")
    if not me or not me.get("ok"):
        print("❌ Token không chính xác hoặc không thể kết nối tới Telegram!")
        sys.exit(1)

    bot_info = me["result"]
    bot_username = bot_info.get('username', '')

    # 1. START HTTP WEB SERVICE SERVER FOR TRADINGVIEW WEBHOOK & RENDER BINDING
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()

    print("\n" + "="*60)
    print(f"🚀 TRADINGVIEW WEBHOOK TELEGRAM BOT ACTIVE 24/7!")
    print(f"• Bot Username: @{bot_username}")
    print(f"• HTTP Port: {WEBHOOK_PORT}")
    print(f"• Webhook Endpoint: POST /webhook")
    print(f"• Health Check: GET / (Status 200 OK)")
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
