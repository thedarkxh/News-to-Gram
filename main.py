import os
import json
import asyncio
import requests
import warnings
from aiogram import Bot
from instagrapi import Client

# Ignore cleanup warnings in logs
warnings.filterwarnings("ignore", category=DeprecationWarning)

TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not TOKEN or not IG_SESSION:
        print("❌ ERROR: Missing Secrets.")
        return

    print("✅ Secrets verified. Initializing sync...")
    # 'async with' ensures the Telegram connection closes properly
    async with Bot(token=TOKEN) as bot:
        ig_client = Client()

        # 1. Instagram Auth
        try:
            session_data = json.loads(IG_SESSION)
            ig_client.set_settings(session_data)
            ig_client.get_settings() 
            print(f"✅ Logged into Instagram as: {IG_USERNAME}")
        except Exception as e:
            print(f"⚠️ Session failed: {e}. Trying fallback...")
            try:
                ig_client.login(IG_USERNAME, IG_PASSWORD)
            except:
                return

        # 2. Telegram Scraper
        try:
            print(f"📡 Scanning channel: {CHANNEL_ID}...")
            # Increased limit to 30 to look further back in history
            updates = await bot.get_updates(limit=30, allowed_updates=["channel_post"])
            
            for update in reversed(updates):
                if update.channel_post and update.channel_post.photo:
                    print("📸 Photo found! Preparing for Instagram...")
                    
                    photo = update.channel_post.photo[-1]
                    file_info = await bot.get_file(photo.file_id)
                    photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                    
                    # Download and Upload
                    with open("temp_news.jpg", "wb") as f:
                        f.write(requests.get(photo_url).content)
                    
                    caption = update.channel_post.caption or "News Update"
                    print("📤 Uploading...")
                    media = ig_client.photo_upload("temp_news.jpg", caption)
                    print(f"🚀 SUCCESS! IG Post ID: {media.pk}")
                    
                    os.remove("temp_news.jpg")
                    return # Stop after the first (newest) post
            
            print("ℹ️ No recent photo posts detected. Post a new image to the channel and try again.")
        except Exception as e:
            print(f"❌ Sync Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
