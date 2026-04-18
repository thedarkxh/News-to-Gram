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
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not TOKEN or not IG_SESSION or not CHANNEL_ID:
        print("❌ ERROR: Missing Secrets.")
        return

    # 1. Instagram Setup
    ig_client = Client()
    try:
        ig_client.set_settings(json.loads(IG_SESSION))
        print("✅ Instagram Session Loaded")
    except Exception as e:
        print(f"❌ Instagram Auth Error: {e}")
        return

    # 2. Telegram Bot Setup
    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Fetching last post from: {CHANNEL_ID}...")
            
            # Using a very high offset to grab the absolute last update available
            updates = await bot.get_updates(offset=-1, limit=10)
            
            # We filter through the last few updates to find the most recent photo
            target_msg = None
            for update in reversed(updates):
                msg = update.channel_post
                if msg and msg.photo:
                    target_msg = msg
                    break
            
            if not target_msg:
                print("ℹ️ No photo posts found in the Telegram cache.")
                print("👉 Note: Bots can only see history from the moment they are added to the channel.")
                return

            print(f"📸 Found Post: {target_msg.caption[:50]}...")
            
            # Download the highest resolution photo
            photo = target_msg.photo[-1]
            file = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            
            with open("last_news.jpg", "wb") as f:
                f.write(requests.get(url).content)
            
            # Upload to Instagram
            print("📤 Syncing to Instagram...")
            media = ig_client.photo_upload("last_news.jpg", target_msg.caption or "")
            print(f"🚀 SUCCESS! Instagram Post ID: {media.pk}")
            
            os.remove("last_news.jpg")

        except Exception as e:
            print(f"❌ Telegram Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
