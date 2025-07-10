
import os
import time
import requests
import hmac
import hashlib
import json
import threading
from fastapi import FastAPI
import telebot

# === ENVIRONMENT VARIABLES ===
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BASE_URL = "https://fapi.binance.com"
app = FastAPI()
bot = telebot.TeleBot(BOT_TOKEN)

# === SIGNAL ENGINE ===
def get_price():
    try:
        res = requests.get(f"{BASE_URL}/fapi/v1/ticker/price?symbol=BTCUSDT")
        return float(res.json()['price'])
    except:
        return None

def get_ma():
    klines = requests.get(f"{BASE_URL}/fapi/v1/klines?symbol=BTCUSDT&interval=1m&limit=50").json()
    closes = [float(k[4]) for k in klines]
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20
    return ma10, ma20

def check_signal():
    ma10, ma20 = get_ma()
    if ma10 > ma20:
        return "LONG"
    elif ma10 < ma20:
        return "SHORT"
    return None

# === BINANCE FUTURES EXECUTION ===
def send_order(side: str, quantity=0.01):
    url = f"{BASE_URL}/fapi/v1/order"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": "BTCUSDT",
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": timestamp
    }
    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    headers = {"X-MBX-APIKEY": API_KEY}
    final_url = f"{url}?{query}&signature={signature}"
    res = requests.post(final_url, headers=headers)
    return res.json()

# === CORE LOGIC ===
trading_active = False

def trading_loop():
    global trading_active
    bot.send_message(CHAT_ID, "🤖 เริ่มระบบ OverHuman Commander แล้ว!")
    while trading_active:
        signal = check_signal()
        price = get_price()
        if signal == "LONG":
            result = send_order("BUY")
            bot.send_message(CHAT_ID, f"✅ เข้า LONG @ {price}\n{result}")
        elif signal == "SHORT":
            result = send_order("SELL")
            bot.send_message(CHAT_ID, f"✅ เข้า SHORT @ {price}\n{result}")
        else:
            bot.send_message(CHAT_ID, f"📊 ยังไม่มีสัญญาณ | BTC = {price}")
        time.sleep(60)

# === TELEGRAM COMMANDS ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    global trading_active
    if not trading_active:
        trading_active = True
        threading.Thread(target=trading_loop).start()
        bot.reply_to(message, "✅ เริ่มระบบแล้ว")
    else:
        bot.reply_to(message, "🚀 ระบบกำลังทำงานอยู่แล้ว")

@bot.message_handler(commands=['stop'])
def stop_handler(message):
    global trading_active
    trading_active = False
    bot.reply_to(message, "🛑 หยุดระบบเรียบร้อยแล้ว")

@bot.message_handler(commands=['status'])
def status_handler(message):
    bot.reply_to(message, f"📡 ระบบกำลัง {'ทำงานอยู่ ✅' if trading_active else 'หยุดอยู่ 🛑'}")

# === BACKGROUND THREAD FOR BOT ===
def run_bot():
    bot.polling(non_stop=True)

threading.Thread(target=run_bot, daemon=True).start()

@app.get("/")
def read_root():
    return {"status": "OverHuman Commander is running"}

# === HOLD MAIN THREAD ===
while True:
    time.sleep(10)
