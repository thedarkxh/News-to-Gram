import os
import json
import asyncio
import requests
import warnings
from aiogram import Bot
from instagrapi import Client

# Suppress messy warnings in logs
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Secrets from GitHub Environment
TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not TOKEN or not IG_SESSION:
        print("❌ Missing Secrets! Check your GitHub Actions settings.")
        return

    print("✅ Secrets verified. Initializing sync...")
    bot = Bot(token=TOKEN)
    ig_client = Client()

    # 1. Instagram Authentication
    try:
        print("🔄 Attempting login via session...")
        session_data = json.loads(IG_SESSION)
        ig_client.set_settings(session_data)
        
        # Test session validity with a light request
        ig_client.get_settings() 
        print(f"✅ Successfully logged into Instagram as: {IG_USERNAME}")
    except Exception as e:
        print(f"⚠️ Session login failed: {e}")
        print("🔄 Attempting password fallback (this may trigger a block)...")
        try:
            ig_client.login(IG_USERNAME, IG_PASSWORD)
            print("✅ Password login successful!")
        except Exception as login_err:
            print(f"❌ Full Authentication Failure: {login_err}")
            await (await bot.get_session()).close()
            return

    # 2. Telegram Sync Logic
    try:
        print(f"📡 Scanning channel: {CHANNEL_ID} for news...")
        # Search the last 20 messages to find the most recent photo
        updates = await bot.get_updates(limit=20, allowed_updates=["channel_post"])
        
        sync_success = False
        for update in reversed(updates):
            if update.channel_post and update.channel_post.photo:
                print("📸 News post found! Syncing to Instagram...")
                
                # Download high-res photo
                photo = update.channel_post.photo[-1]
                file_info = await bot.get_file(photo.file_id)
                photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                
                photo_path = "instagram_upload.jpg"
                with open(photo_path, "wb") as f:
                    f.write(requests.get(photo_url).content)
                
                caption = update.channel_post.caption or "Breaking News Update"
                
                # Upload
                print("📤 Uploading media...")
                media = ig_client.photo_upload(photo_path, caption)
                print(f"🚀 SUCCESS! Post live at ID: {media.pk}")
                
                os.remove(photo_path)
                sync_success = True
                break # Only sync the single newest post
        
        if not sync_success:
            print("ℹ️ No photo posts found in the recent Telegram history.")

    except Exception as e:
        print(f"❌ Sync Process Error: {e}")
    
    finally:
        # Properly close the bot session
        session = await bot.get_session()
        await session.close()

if __name__ == "__main__":
    asyncio.run(main())
