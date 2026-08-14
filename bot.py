#!/usr/bin/env python3
"""
Telegram Bot Engine + TradingView Webhook Listener
Pure Python Implementation. Zero PIP dependencies required!
Compatible with 24/7 Cloud Deployment (Render / Railway / Replit).

Features:
1. /scan : Scans default Watchlist
2. /scan BTC ETH SOL SUI PEPE : Scans custom coin list!
3. /btc, /eth, /sol : Instant single coin report
4. Zero temporary waiting messages, direct clean single-message response.
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

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

        signal_text = ""
        try:
            payload = json.loads(post_data)
            symbol = payload.get("ticker", payload.get("symbol", "CRYPTO")).upper()
            report = get_coin_report(symbol)
            signal_text = report
        except Exception:
            signal_text = f"🚨 **TRADINGVIEW ALERT**\n\n{post_data}"

        if bot_token and default_chat_id:
            send_message(bot_token, default_chat_id, signal_text)
            print(f"✅ Alert forwarded to Telegram Chat ID: {default_chat_id}")

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
    print(f"🌐 TRADINGVIEW WEBHOOK SERVER RUNNING ON PORT: {WEBHOOK_PORT}")
    httpd.serve_forever()

def handle_update(token, update, bot_username=""):
    """
    Process incoming Telegram message.
    Supports /scan and /scan BTC ETH SOL SUI PEPE commands!
    """
    global default_chat_id, config
    
    message = update.get("message")
    if not message:
        return
        
    chat_id = message["chat"]["id"]
    
    if str(chat_id) != str(default_chat_id):
        default_chat_id = chat_id
        config["group_chat_id"] = chat_id
        save_config(config)

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
        
    parts = clean_text.split()
    cmd = parts[0].lower()
    
    if cmd in ["start", "help"]:
        welcome = (
            "🤖 **TRỢ LÝ CHỈ BÁO CRYPTO (CI STUDIO BOT)**\n\n"
            "📌 **CÂU LỆNH SỬ DỤNG:**\n"
            "• `/btc`, `/eth`, `/sol`... : Kiểm tra coin\n"
            "• `/scan` : Quét Watchlist mặc định\n"
            "• `/scan BTC ETH SOL SUI PEPE` : Quét danh sách tùy chọn!\n"
            "• `/help` : Hiển thị hướng dẫn"
        )
        send_message(token, chat_id, welcome)
        return

    if cmd == "scan":
        # Check if custom coin list was passed e.g. /scan BTC ETH SOL SUI PEPE
        custom_coins = parts[1:] if len(parts) > 1 else None
        report = scan_market(custom_coins)
        send_message(token, chat_id, report)
        return

    # Single coin symbol lookup e.g. /btc, /sol
    symbol = cmd.replace("check", "").strip()
    if len(symbol) >= 2 and len(symbol) <= 10 and symbol.isalnum():
        report = get_coin_report(symbol)
        send_message(token, chat_id, report)

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

    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()

    print("\n" + "="*60)
    print(f"🚀 TELEGRAM BOT + TRADINGVIEW WEBHOOK 24/7 ACTIVE!")
    print(f"• Bot Username: @{bot_username}")
    print(f"• Watchlist Scanner support (/scan & /scan BTC ETH SOL...)")
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
