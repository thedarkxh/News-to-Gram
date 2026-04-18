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

        # 1. Instagram Authentication
        try:
            ig_client.set_settings(json.loads(IG_SESSION))
            ig_client.get_settings() 
            print(f"✅ Logged into Instagram: {IG_USERNAME}")
        except Exception as e:
            print(f"❌ IG Auth Failed: {e}")
            return

        # 2. Fetching from Channel History
        try:
            print(f"📡 Accessing channel history: {CHANNEL_ID}")
            
            # Using get_chat to confirm we have the right ID
            chat = await bot.get_chat(CHANNEL_ID)
            print(f"🔗 Targeted Channel: {chat.title}")

            # Fetch the most recent message directly from the channel
            # offset=-1 tells Telegram to start from the very last message
            updates = await bot.get_updates(offset=-1, limit=1)
            
            if not updates:
                print("ℹ️ No new updates found. Post a NEW photo to the channel and run again.")
                return

            for update in updates:
                msg = update.channel_post
                if msg and msg.photo:
                    print(f"📸 Found headline: {msg.caption[:50]}...")
                    
                    # Get the highest resolution photo
                    photo = msg.photo[-1]
                    file = await bot.get_file(photo.file_id)
                    url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
                    
                    # Download locally
                    img_data = requests.get(url).content
                    with open("sync_card.jpg", "wb") as f:
                        f.write(img_data)
                    
                    # Upload to Instagram
                    print("📤 Posting to Instagram...")
                    media = ig_client.photo_upload("sync_card.jpg", msg.caption)
                    print(f"🚀 SUCCESS! IG Post ID: {media.pk}")
                    
                    os.remove("sync_card.jpg")
                    return # Exit after one successful sync

        except Exception as e:
            print(f"❌ Telegram Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
