import os
import json
import asyncio
import requests
import warnings
from aiogram import Bot
from instagrapi import Client

warnings.filterwarnings("ignore", category=DeprecationWarning)

TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not TOKEN or not IG_SESSION or not CHANNEL_ID:
        print("❌ ERROR: Missing Secrets.")
        return

    async with Bot(token=TOKEN) as bot:
        ig_client = Client()

        # 1. Instagram Auth
        try:
            ig_client.set_settings(json.loads(IG_SESSION))
            ig_client.get_settings() 
            print(f"✅ Logged into Instagram: {IG_USERNAME}")
        except Exception as e:
            print(f"❌ IG Auth Failed: {e}")
            return

        # 2. Grab the specific news card
        try:
            print(f"📡 Fetching latest from channel: {CHANNEL_ID}")
            
            # Using get_chat to verify connection
            chat = await bot.get_chat(CHANNEL_ID)
            print(f"🔗 Connected to: {chat.title}")

            # Looking for the most recent message in the channel buffer
            updates = await bot.get_updates(limit=10, offset=-1)
            
            found = False
            for update in reversed(updates):
                msg = update.channel_post
                if msg and msg.chat.id == int(CHANNEL_ID) and msg.photo:
                    print(f"📸 Found headline: {msg.caption[:50]}...")
                    
                    photo = msg.photo[-1]
                    file = await bot.get_file(photo.file_id)
                    url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
                    
                    img_data = requests.get(url).content
                    with open("news_card.jpg", "wb") as f:
                        f.write(img_data)
                    
                    print("📤 Uploading to Instagram...")
                    media = ig_client.photo_upload("news_card.jpg", msg.caption)
                    print(f"🚀 SUCCESS! Post ID: {media.pk}")
                    
                    os.remove("news_card.jpg")
                    found = True
                    break

            if not found:
                print("ℹ️ No media found. Try posting a NEW photo to the channel now.")

        except Exception as e:
            print(f"❌ Telegram Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
