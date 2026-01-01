import os
import asyncio
from telethon import TelegramClient, events, errors
from config import Config
from flask import Flask
from threading import Thread

# Flask server for Render stability
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# Initialize the Bot
bot = TelegramClient('bot_session', Config.API_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)

# Dictionary to store user login sessions
user_clients = {}

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Welcome! Send your phone number with country code to start (e.g., +123456789)")

@bot.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()

    # Login Logic
    if text.startswith('+'):
        client = TelegramClient(f"user_{uid}", Config.API_ID, Config.API_HASH)
        await client.connect()
        try:
            pw = await client.send_code_request(text)
            user_clients[uid] = {'client': client, 'phone': text, 'hash': pw.phone_code_hash}
            await event.respond("Please enter the verification code sent to your Telegram:")
        except Exception as e:
            await event.respond(f"Error: {e}")

    elif text.isdigit() and uid in user_clients and 'hash' in user_clients[uid]:
        try:
            client = user_clients[uid]['client']
            await client.sign_in(user_clients[uid]['phone'], text, phone_code_hash=user_clients[uid]['hash'])
            await event.respond("Successfully logged in! Now send the link of the restricted post or channel.")
        except Exception as e:
            await event.respond(f"Login Failed: {e}")

    # Content Downloader Logic
    elif "t.me/" in text:
        if uid not in user_clients:
            return await event.respond("Please log in first using your phone number.")
        
        client = user_clients[uid]['client']
        await event.respond("Scanning and downloading content... Please wait.")
        
        try:
            async for message in client.iter_messages(text, limit=None):
                if message.media:
                    path = await client.download_media(message)
                    await bot.send_file(uid, path, caption=message.text or "")
                    if os.path.exists(path): os.remove(path)
                    await asyncio.sleep(1) # Delay to avoid flood
            await event.respond("Process Completed Successfully!")
        except Exception as e:
            await event.respond(f"Failed to fetch content: {e}")

if __name__ == '__main__':
    keep_alive()
    print("Bot is starting...")
    bot.run_until_disconnected()