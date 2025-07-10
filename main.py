
import os
import time
import hmac
import hashlib
import requests
import json
from fastapi import FastAPI, Request
import telebot

# === ENVIRONMENT VARIABLES ===
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
APP_URL = os.getenv("APP_URL")  # ใช้ domain ของ Railway เช่น https://xxx.up.railway.app

BASE_URL = "https://fapi.binance.com"
bot = telebot.TeleBot(BOT_TOKEN)
app = FastAPI()

trading_active = False

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

# === TELEGRAM HANDLERS ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    global trading_active
    if not trading_active:
        trading_active = True
        bot.reply_to(message, "✅ เริ่มระบบแล้ว (Webhook)")
    else:
        bot.reply_to(message, "🚀 ระบบกำลังทำงานอยู่แล้ว")

@bot.message_handler(commands=['stop'])
def stop_handler(message):
    global trading_active
    trading_active = False
    bot.reply_to(message, "🛑 หยุดระบบเรียบร้อยแล้ว")

@bot.message_handler(commands=['status'])
def status_handler(message):
    bot.reply_to(message, f"📡 ระบบกำลัง {'ทำงาน ✅' if trading_active else 'หยุดอยู่ 🛑'}")

# === FASTAPI ROUTES ===
@app.get("/")
def root():
    return {"message": "OverHuman Commander Webhook Active"}

@app.post("/webhook")
async def telegram_webhook(req: Request):
    body = await req.body()
    update = telebot.types.Update.de_json(body.decode("utf-8"))
    bot.process_new_updates([update])
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    # Delete old webhook (ถ้ามี)
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    # ตั้ง webhook ใหม่
    webhook_url = f"{APP_URL}/webhook"
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}")
