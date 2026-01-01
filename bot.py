import os
import asyncio
from telethon import TelegramClient, events
from config import Config
from flask import Flask
from threading import Thread

# نظام البقاء حياً لـ Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# إعداد البوت باستخدام ملف الإعداد
bot = TelegramClient('bot_session', Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)

user_clients = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("🚀 مرحباً بك في نسخة السحب الاحترافية.\nأرسل رقمك الآن (مثال: +962...)")

@bot.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()

    # مرحلة التسجيل
    if text.startswith('+'):
        client = TelegramClient(f"user_{uid}", Config.API_ID, Config.API_HASH)
        await client.connect()
        try:
            pw = await client.send_code_request(text)
            user_clients[uid] = {'client': client, 'phone': text, 'hash': pw.phone_code_hash}
            await event.respond("📩 أرسل الكود:")
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    elif text.isdigit() and uid in user_clients and 'hash' in user_clients[uid]:
        try:
            client = user_clients[uid]['client']
            await client.sign_in(user_clients[uid]['phone'], text, phone_code_hash=user_clients[uid]['hash'])
            await event.respond("✅ تم الربط! أرسل رابط القناة الآن.")
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    # مرحلة السحب الشامل
    elif "t.me/" in text:
        if uid not in user_clients:
            return await event.respond("⚠️ سجل دخولك أولاً.")
        
        client = user_clients[uid]['client']
        await event.respond("🌪️ جاري السحب...")
        
        async for message in client.iter_messages(text, limit=None):
            if message.media:
                path = await client.download_media(message)
                await bot.send_file(uid, path, caption=message.text or "")
                if os.path.exists(path): os.remove(path)
                await asyncio.sleep(1)

if __name__ == '__main__':
    keep_alive()
    bot.run_until_disconnected()