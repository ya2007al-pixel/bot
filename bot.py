import os
import asyncio
import random
import string
from telethon import TelegramClient, events
from config import Config
from flask import Flask
from threading import Thread

# تثبيت سيرفر الويب
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل باستقرار"
def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# تشغيل البوت الأساسي
bot = TelegramClient('main_bot', Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
user_sessions = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("🚀 أهلاً بك! أرسل رقم هاتفك الآن (مثال: +962...)")

@bot.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()

    if text.startswith('+'):
        # إنشاء اسم جلسة عشوائي لضمان عدم حدوث تضارب (حل مشكلة الرمز المنتهي)
        random_id = ''.join(random.choices(string.ascii_letters, k=5))
        session_name = f"user_{uid}_{random_id}"
        
        client = TelegramClient(session_name, Config.API_ID, Config.API_HASH, device_model="iPhone 15 Pro")
        await client.connect()
        try:
            res = await client.send_code_request(text)
            user_sessions[uid] = {'client': client, 'phone': text, 'hash': res.phone_code_hash, 's_name': session_name}
            await event.respond("📩 أرسل الكود الآن (يجب إدخال الكود بسرعة):")
        except Exception as e:
            await event.respond(f"❌ خطأ: {e}")

    elif text.isdigit() and uid in user_sessions:
        try:
            data = user_sessions[uid]
            await data['client'].sign_in(data['phone'], text, phone_code_hash=data['hash'])
            await event.respond("✅ تم الدخول بنجاح! أرسل الآن رابط القناة.")
        except Exception as e:
            # إذا فشل، نمسح ملف الجلسة فوراً للمحاولة من جديد بنظافة
            if os.path.exists(f"{data['s_name']}.session"):
                os.remove(f"{data['s_name']}.session")
            await event.respond(f"❌ فشل: الرمز منتهي. السبب غالباً تأخير من السيرفر.\nإليك الحل: أرسل الرقم مرة أخرى وجرب الآن فوراً.")

    elif "t.me/" in text:
        if uid not in user_sessions: return
        client = user_sessions[uid]['client']
        await event.respond("⏳ جاري سحب المحتوى...")
        async for msg in client.iter_messages(text, limit=100):
            if msg.media:
                path = await client.download_media(msg)
                await bot.send_file(uid, path, caption=msg.text or "")
                if os.path.exists(path): os.remove(path)
        await event.respond("✨ تم السحب!")

if __name__ == '__main__':
    keep_alive()
    bot.run_until_disconnected()
