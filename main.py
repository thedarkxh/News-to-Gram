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
    if not TOKEN or not IG_SESSION:
        print("❌ ERROR: Secrets not found.")
        return

    async with Bot(token=TOKEN) as bot:
        ig_client = Client()

        # 1. Instagram Login
        try:
            ig_client.set_settings(json.loads(IG_SESSION))
            ig_client.get_settings() 
            print(f"✅ Logged into Instagram: {IG_USERNAME}")
        except Exception as e:
            print(f"⚠️ Session failed: {e}")
            return

        # 2. Advanced Telegram Search
        try:
            print(f"📡 Force-scanning channel: {CHANNEL_ID}")
            
            # We use a very high limit to ensure we catch the morning posts
            updates = await bot.get_updates(limit=100, offset=-1)
            
            if not updates:
                # If get_updates is empty, we try a fallback check
                print("⚠️ get_updates returned nothing. Try posting a NEW photo now.")
                return

            for update in reversed(updates):
                # Check for channel posts specifically
                content = update.channel_post if update.channel_post else update.message
                
                if content and content.photo:
                    print("📸 Found the News Card! Downloading...")
                    
                    photo = content.photo[-1]
                    file = await bot.get_file(photo.file_id)
                    url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
                    
                    with open("upload.jpg", "wb") as f:
                        f.write(requests.get(url).content)
                    
                    caption = content.caption or "News Update"
                    
                    print("📤 Syncing to Instagram...")
                    media = ig_client.photo_upload("upload.jpg", caption)
                    print(f"🚀 SUCCESS! Post live: {media.pk}")
                    
                    os.remove("upload.jpg")
                    return 

            print("ℹ️ Still no photos found. Telegram is hiding old updates from the bot.")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
