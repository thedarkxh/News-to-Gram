import os
import json
import asyncio
import requests
from aiogram import Bot
from instagrapi import Client

# Load environment variables
TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    # 1. Validation
    if not TOKEN or not IG_SESSION:
        print(f"❌ Missing Secrets! TOKEN: {bool(TOKEN)}, SESSION: {bool(IG_SESSION)}")
        return

    print("✅ Secrets loaded. Initializing...")
    bot = Bot(token=TOKEN)
    ig_client = Client()

    # 2. Authenticate Instagram via Session
    try:
        session_data = json.loads(IG_SESSION)
        ig_client.set_settings(session_data)
        ig_client.get_timeline_feed() 
        print(f"✅ Authenticated as {IG_USERNAME}")
    except Exception as e:
        print(f"❌ Instagram Session Failed: {e}")
        # Fallback to login if session is totally dead
        try:
            print("🔄 Attempting password fallback...")
            ig_client.login(IG_USERNAME, IG_PASSWORD)
        except:
            return

    # 3. Fetch from Telegram & Sync
    try:
        print(f"📡 Checking channel: {CHANNEL_ID}")
        # Fetch latest updates
        updates = await bot.get_updates(limit=10, allowed_updates=["channel_post"])
        
        # Search for the most recent photo
        for update in reversed(updates):
            if update.channel_post and update.channel_post.photo:
                print("📸 News photo found! Processing...")
                
                # Get high-res image
                photo = update.channel_post.photo[-1]
                file_info = await bot.get_file(photo.file_id)
                photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                
                # Download image locally
                photo_path = "sync_content.jpg"
                with open(photo_path, "wb") as f:
                    f.write(requests.get(photo_url).content)
                
                # Use TG caption or default
                caption = update.channel_post.caption or "Latest Update"
                
                print("📤 Uploading to Instagram...")
                media = ig_client.photo_upload(photo_path, caption)
                print(f"🚀 Success! Post ID: {media.pk}")
                
                # Cleanup and exit loop
                os.remove(photo_path)
                return 
        
        print("ℹ️ No new photo posts found in the last 10 updates.")
                
    except Exception as e:
        print(f"❌ Sync Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
