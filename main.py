import os
import json
import asyncio
import requests
from aiogram import Bot
from instagrapi import Client

TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not TOKEN or not IG_SESSION:
        print("❌ Missing Secrets!")
        return

    print("✅ Secrets loaded. Initializing...")
    bot = Bot(token=TOKEN)
    ig_client = Client()

    # Authenticate
    try:
        session_data = json.loads(IG_SESSION)
        ig_client.set_settings(session_data)
        # Use a lighter check to keep session alive
        ig_client.get_settings() 
        print(f"✅ Authenticated as {IG_USERNAME}")
    except Exception as e:
        print(f"❌ Instagram Session Failed: {e}")
        return

    # Sync Logic
    try:
        print(f"📡 Checking channel: {CHANNEL_ID}")
        # Increased limit to 20 to find older photos
        updates = await bot.get_updates(limit=20, allowed_updates=["channel_post"])
        
        found = False
        for update in reversed(updates):
            if update.channel_post and update.channel_post.photo:
                print("📸 News photo found! Downloading...")
                photo = update.channel_post.photo[-1]
                file_info = await bot.get_file(photo.file_id)
                photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                
                with open("sync.jpg", "wb") as f:
                    f.write(requests.get(photo_url).content)
                
                caption = update.channel_post.caption or "News Update"
                print("📤 Uploading to Instagram...")
                ig_client.photo_upload("sync.jpg", caption)
                print("🚀 SUCCESS! Check your Instagram feed.")
                
                os.remove("sync.jpg")
                found = True
                break 
        
        if not found:
            print("ℹ️ No photos found. Try posting a NEW photo to the channel now.")
                
    except Exception as e:
        print(f"❌ Sync Error: {e}")
    finally:
        # Close the bot session properly to avoid the 'Unclosed client session' warning
        session = await bot.get_session()
        if session:
            await session.close()

if __name__ == "__main__":
    asyncio.run(main())
