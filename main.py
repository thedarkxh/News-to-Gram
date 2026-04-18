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
        print(f"❌ Instagram Error: {e}")
        return

    # 2. Telegram Bot Setup
    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Scanning channel: {CHANNEL_ID}...")
            
            # offset=-1 forces the bot to skip all old messages 
            # and look ONLY at the absolute latest update in the server's queue.
            updates = await bot.get_updates(offset=-1, limit=1, timeout=10)
            
            if not updates:
                print("⚠️ No fresh updates found in the Telegram queue.")
                print("👉 FIX: Post the news card to your channel NOW, then run this Action.")
                return

            for update in updates:
                # We check both channel_post and regular message
                msg = update.channel_post if update.channel_post else update.message
                
                if msg and msg.photo:
                    print(f"📸 Found Post: {msg.caption[:50]}...")
                    
                    # Get high-res photo
                    photo = msg.photo[-1]
                    file = await bot.get_file(photo.file_id)
                    url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
                    
                    # Download
                    with open("temp_post.jpg", "wb") as f:
                        f.write(requests.get(url).content)
                    
                    # Upload to IG
                    print("📤 Syncing to Instagram...")
                    media = ig_client.photo_upload("temp_post.jpg", msg.caption or "")
                    print(f"🚀 SUCCESS! Instagram ID: {media.pk}")
                    
                    os.remove("temp_post.jpg")
                    return
                else:
                    print("ℹ️ Found an update, but it wasn't a photo post.")

        except Exception as e:
            print(f"❌ Telegram Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
