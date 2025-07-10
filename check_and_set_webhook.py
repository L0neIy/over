import os
import requests

def print_env():
    print("=== Environment Variables ===")
    for k, v in os.environ.items():
        print(f"{k} = {v}")
    print("=============================")

def set_webhook():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    app_url = os.getenv("APP_URL")

    if not bot_token or not app_url:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN หรือ APP_URL ยังไม่ได้ตั้งค่าใน environment variables")
        return

    webhook_url = f"{app_url}/webhook"
    print(f"Setting webhook to: {webhook_url}")

    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/setWebhook",
        params={"url": webhook_url}
    )

    if response.ok:
        print("✅ Webhook set successfully:")
        print(response.json())
    else:
        print("❌ Failed to set webhook:")
        print(response.text)

if __name__ == "__main__":
    print_env()
    set_webhook()
