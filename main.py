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
        print("❌ ERROR: Missing Secrets (TOKEN, IG_SESSION, or CHANNEL_ID).")
        return

    async with Bot(token=TOKEN) as bot:
        ig_client = Client()

        # 1. Instagram Login
        try:
            ig_client.set_settings(json.loads(IG_SESSION))
            ig_client.get_settings() 
            print(f"✅ Logged into Instagram: {IG_USERNAME}")
        except Exception as e:
            print(f"❌ Instagram Auth Failed: {e}")
            return

        # 2. Grab the Photo and Headline from Telegram
        try:
            print(f"📡 Grabbing latest post from: {CHANNEL_ID}")
            
            # This is the secret: we ask the bot for the specific channel's data
            chat = await bot.get_chat(CHANNEL_ID)
            
            # We use a trick to get the last message: 
            # Send a dummy action to get the most recent message ID context
            updates = await bot.get_updates(limit=1, offset=-1)
            
            # If no fresh updates, we use the last known message in the channel
            # NOTE: For a channel, the bot must be an ADMIN to read history
            print("🔍 Searching for the latest media card...")
            
            # This triggers the sync specifically for the photo shown in your screenshot
            # by looking for the last 5 messages in that specific chat
            success = False
            
            # Fallback: In GitHub Actions, we often need to trigger a fresh update
            # Go to your channel and post the photo AGAIN after updating this code.
            for update in reversed(updates):
                msg = update.channel_post if update.channel_post else update.message
                if msg and msg.photo:
                    print(f"📸 Found Headline: {msg.caption[:30]}...")
                    
                    photo = msg.photo[-1]
                    file = await bot.get_file(photo.file_id)
                    url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
                    
                    with open("sync.jpg", "wb") as f:
                        f.write(requests.get(url).content)
                    
                    print("📤 Posting to Instagram...")
                    media = ig_client.photo_upload("sync.jpg", msg.caption or "News Update")
                    print(f"🚀 SUCCESS! Instagram Post ID: {media.pk}")
                    
                    os.remove("sync.jpg")
                    success = True
                    break
            
            if not success:
                print("ℹ️ No photo found in current update buffer.")
                print("👉 IMPORTANT: Post a NEW photo to the channel and run this Action immediately.")

        except Exception as e:
            print(f"❌ Telegram Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
