#!/usr/bin/env python3
"""
Dedicated BTC 4H 24/7/365 Auto-Monitor & Self Keep-Alive Bot Engine
Pure Python Implementation. Zero PIP dependencies required!
Compatible with 24/7 Render / Railway / Replit Web Services.

Features:
1. Instant test command /check & /test.
2. Self-ping Keep-Alive mechanism preventing Render Free tier spin down.
3. Explicit Console Logs: [4H Scan] BTC: {price} | Blue: {blue} | Red: {red} | Status: OK.
4. Silent 24/7 background monitor with 60-minute anti-spam cooldown.
"""
import urllib.request
import urllib.parse
import json
import time
import os
import sys
import threading
import re
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from scanner import get_btc_4h_check_report, check_btc_4h_signal
from ta_engine import format_price_level

CONFIG_FILE = "config.json"
WEBHOOK_PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://crypto-scanner-bot-zs2j.onrender.com")

# ANTI-SPAM COOLDOWN STATE
last_alert_type = None
last_alert_time = 0

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
        with urllib.request.urlopen(req, timeout=15) as response:
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

def scan_coin(symbol="BTC"):
    return get_btc_4h_check_report()

# GLOBAL STATE
config = load_config()
bot_token = config.get("telegram_token", "")
default_chat_id = config.get("group_chat_id", "")

class WebhookRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler to fulfill Render Web Service Health Checks."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Dedicated BTC 4H 24/7/365 Keep-Alive Web Service is Active!</h1></body></html>")

    def log_message(self, format, *args):
        return

def start_webhook_server():
    """Starts HTTP Server in background thread for Render Web Service Port Binding."""
    try:
        server_address = ('0.0.0.0', WEBHOOK_PORT)
        httpd = HTTPServer(server_address, WebhookRequestHandler)
        print(f"🌐 HTTP Web Service is running on port {WEBHOOK_PORT}")
        httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ HTTP Server Exception on port {WEBHOOK_PORT}: {e}")

def keep_alive_self_ping():
    """Self-ping HTTP GET request to keep Render Web Service awake 24/7/365."""
    try:
        req = urllib.request.Request(RENDER_URL, headers={"User-Agent": "RenderKeepAlive/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            pass
    except Exception:
        pass

def btc_4h_auto_monitor_loop():
    """
    24/7/365 SILENT BACKGROUND AUTO-MONITOR & KEEP-ALIVE FOR BTC 4H.
    Scans every 1 minute (60s).
    Prints console heartbeats for Render Logs.
    Self-pings Render URL to prevent spin down.
    """
    global last_alert_type, last_alert_time, bot_token, default_chat_id
    
    print("🤖 24/7/365 BACKGROUND AUTO-MONITOR & KEEP-ALIVE INITIALIZED!")
    
    while True:
        try:
            time.sleep(60) # Scan every 1 minute
            
            # Keep-Alive Self Ping
            threading.Thread(target=keep_alive_self_ping, daemon=True).start()

            triggered, signal_type, alert_msg, curr_price, val_blue, val_red = check_btc_4h_signal()
            
            # Explicit Heartbeat Console Log for Render Logs Tab
            p_curr = format_price_level(curr_price)
            p_blue = format_price_level(val_blue)
            p_red = format_price_level(val_red)
            status_text = signal_type if triggered else "OK (Floating)"
            print(f"[4H Scan] BTC: {p_curr} | Blue: {p_blue} | Red: {p_red} | Status: {status_text}")

            if triggered and alert_msg and bot_token and default_chat_id:
                now = time.time()
                # 60-Minute Cooldown (3600s) or new signal type
                if signal_type != last_alert_type or (now - last_alert_time > 3600):
                    print(f"🚨 ALERT TRIGGERED: {signal_type} -> Sending alert to Chat ID {default_chat_id}")
                    send_message(bot_token, default_chat_id, alert_msg)
                    last_alert_type = signal_type
                    last_alert_time = now
        except Exception as e:
            print(f"⚠️ Error in BTC 4H Auto-Monitor Loop: {e}")
            time.sleep(10)

def handle_update(token, update, bot_username=""):
    """
    Process incoming Telegram message.
    Automatically captures chat_id on any message or /start command.
    """
    global default_chat_id, config
    
    message = update.get("message")
    if not message:
        return
        
    chat_id = message["chat"]["id"]
    
    # DYNAMIC CHAT ID CAPTURE
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
        parts = clean_text.split()
        cmd = parts[0].lower()
        if cmd.startswith("/"):
            cmd = cmd[1:]
        
        if cmd in ["start", "help"]:
            welcome = (
                "🤖 <b>TRỢ LÝ CẢNH BÁO TỰ ĐỘNG BTC 4H (24/7/365)</b>\n\n"
                "📌 <b>CƠ CHẾ HOẠT ĐỘNG:</b>\n"
                "• Bot chạy ngầm im lặng quét BTC 4H mỗi 1 phút/lần.\n"
                "• Tích hợp Keep-Alive tự kích hoạt giữ Render hoạt động 24/7/365 không bị ngủ đông.\n"
                "• Chỉ tự động bắn cảnh báo khi BTC chạm Mốc Blue 🔵 (Hỗ trợ) hoặc Red 🔴 (Cản) trong phạm vi 0.8%.\n\n"
                "📌 <b>CÂU LỆNH KIỂM TRA:</b>\n"
                "• <code>/check</code> hoặc <code>/test</code> : Kiểm tra ngay kết nối Telegram & lấy bản tin test BTC 4H."
            )
            send_message(token, chat_id, welcome)
            return

        if cmd in ["check", "test", "btc", "scan"]:
            report = get_btc_4h_check_report()
            send_message(token, chat_id, report)
            return

    except Exception as e:
        error_trace = f"❌ <b>LỖI THỰC THI BOT:</b>\n<code>{str(e)}</code>\n\n<b>Chi tiết Traceback:</b>\n<pre>{traceback.format_exc()[:700]}</pre>"
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

    # 1. START HTTP WEB SERVICE SERVER FOR RENDER PORT BINDING
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()

    # 2. START SILENT 24/7/365 BTC 4H AUTO-MONITOR BACKGROUND THREAD
    monitor_thread = threading.Thread(target=btc_4h_auto_monitor_loop, daemon=True)
    monitor_thread.start()

    print("\n" + "="*60)
    print(f"🚀 SILENT BTC 4H 24/7/365 AUTO-MONITOR & KEEP-ALIVE BOT ACTIVE!")
    print(f"• Bot Username: @{bot_username}")
    print(f"• HTTP Port: {WEBHOOK_PORT}")
    print(f"• Test Command: /check or /test")
    print(f"• Self Ping URL: {RENDER_URL}")
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
