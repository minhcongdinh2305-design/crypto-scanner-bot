#!/usr/bin/env python3
"""
Telegram Bot Engine + TradingView Webhook Listener + Multi-Timeframe Status Report
Pure Python Implementation with zero extra dependencies required.
Compatible with 24/7 Cloud Deployment (Render / Railway / Replit).

Features:
1. Multi-Timeframe Status Report (30M, 1H, 2H, 4H, 8H, 12H, 1D, 1W, 1M)
2. Commands: /btc, /link, /linkscan, /scan link, /btc4h (TradingView chart photo)
3. Direct single-message clean responses.
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
from scanner import get_coin_report, scan_market
from binance_api import get_klines, normalize_symbol
from chart_engine import generate_chart_image, cleanup_chart_image

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

def send_photo(token, chat_id, photo_path, caption=""):
    """Send photo with caption to Telegram Bot API using multipart/form-data."""
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    body = []
    body.append(f"--{boundary}".encode('utf-8'))
    body.append(b'Content-Disposition: form-data; name="chat_id"')
    body.append(b'')
    body.append(str(chat_id).encode('utf-8'))

    if caption:
        body.append(f"--{boundary}".encode('utf-8'))
        body.append(b'Content-Disposition: form-data; name="caption"')
        body.append(b'')
        body.append(caption.encode('utf-8'))

        body.append(f"--{boundary}".encode('utf-8'))
        body.append(b'Content-Disposition: form-data; name="parse_mode"')
        body.append(b'')
        body.append(b'Markdown')

    filename = os.path.basename(photo_path)
    body.append(f"--{boundary}".encode('utf-8'))
    body.append(f'Content-Disposition: form-data; name="photo"; filename="{filename}"'.encode('utf-8'))
    body.append(b'Content-Type: image/png')
    body.append(b'')
    with open(photo_path, 'rb') as f:
        body.append(f.read())

    body.append(f"--{boundary}--".encode('utf-8'))
    body.append(b'')

    payload = b'\r\n'.join(body)
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(payload))
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error sending photo to Telegram: {e}")
        return None

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

def parse_coin_and_tf(cmd_text):
    """
    Parses inputs like:
    - linkscan -> (LINK, None)
    - btc4h -> (BTC, 4h)
    - link3d -> (LINK, 3d)
    - eth1d -> (ETH, 1d)
    - btc 4h -> (BTC, 4h)
    - btc -> (BTC, None)
    """
    clean = cmd_text.strip().lower()
    
    if clean.endswith("scan") and len(clean) > 4:
        sym = clean[:-4].upper()
        return sym, None

    m = re.match(r"^([a-z0-9]+?)(15m|30m|1h|2h|4h|8h|12h|1d|2d|3d|1w)$", clean)
    if m:
        return m.group(1).upper(), m.group(2)

    parts = clean.split()
    if len(parts) >= 2:
        tf_candidate = parts[1].lower()
        if tf_candidate in ["15m", "30m", "1h", "2h", "4h", "8h", "12h", "1d", "2d", "3d", "1w"]:
            return parts[0].upper(), tf_candidate
            
    if len(parts) == 1 and parts[0].isalnum():
        return parts[0].upper(), None
        
    return None, None

def handle_update(token, update, bot_username=""):
    """
    Process incoming Telegram message.
    Outputs Multi-Timeframe Status Report or Chart Photo.
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
            "• `/btc`, `/link`, `/linkscan` : Báo cáo trạng thái 9 khung thời gian!\n"
            "• `/btc4h`, `/link3d`, `/eth1d` : Chụp ảnh CHART TradingView THẬT 100% + Báo cáo!\n"
            "• `/scan` : Quét Watchlist mặc định\n"
            "• `/scan BTC ETH SOL SUI PEPE` : Quét Watchlist tùy chỉnh\n"
            "• `/help` : Hướng dẫn"
        )
        send_message(token, chat_id, welcome)
        return

    if cmd == "scan":
        if len(parts) > 1 and parts[1].lower() not in ["btc", "eth", "sol", "link", "bnb"]:
            # Handle /scan link
            symbol = parts[1].upper()
            report = get_coin_report(symbol)
            send_message(token, chat_id, report)
            return

        custom_coins = parts[1:] if len(parts) > 1 else None
        report = scan_market(custom_coins)
        send_message(token, chat_id, report)
        return

    symbol, timeframe = parse_coin_and_tf(clean_text)
    
    if symbol:
        report = get_coin_report(symbol)
        
        # If timeframe requested (e.g. /btc4h or /link3d), capture TradingView Chart Snapshot!
        if timeframe:
            try:
                photo_path = generate_chart_image(symbol, timeframe)
                if photo_path and os.path.exists(photo_path):
                    res = send_photo(token, chat_id, photo_path, report)
                    cleanup_chart_image(photo_path)
                    if res and res.get("ok"):
                        return
                    else:
                        err_desc = res.get("description", "Không xác định") if res else "Telegram API Timeout"
                        send_message(token, chat_id, f"❌ LỖI GỬI ẢNH TELEGRAM:\n{err_desc}")
                        return
                else:
                    send_message(token, chat_id, f"❌ KHÔNG TẠO ĐƯỢC ẢNH: Lỗi chụp TradingView cho {symbol} ({timeframe})")
                    return
            except Exception as e:
                error_msg = f"❌ LỖI TẠO ẢNH ({symbol} {timeframe}):\n{str(e)}\n\nChi tiết Traceback:\n`{traceback.format_exc()[:700]}`"
                send_message(token, chat_id, error_msg)
                return

        # Return Multi-Timeframe Status Report
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
    print(f"🚀 TELEGRAM BOT + MULTI-TIMEFRAME SCANNER 24/7 ACTIVE!")
    print(f"• Bot Username: @{bot_username}")
    print(f"• Commands: /linkscan, /scan link, /link (Outputs 9-Timeframe Status Report!)")
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
