import os
import json
import asyncio
import requests
import warnings
import time
from aiogram import Bot
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

# Silence deprecation warnings for cleaner logs
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Secrets retrieval from GitHub Environment
TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not all([TOKEN, IG_USERNAME, IG_PASSWORD, CHANNEL_ID]):
        print("❌ ERROR: Missing vital Secrets. Check TOKEN, IG_USERNAME, IG_PASSWORD, and CHANNEL_ID.")
        return

    # --- 1. INSTAGRAM AUTHENTICATION ---
    cl = Client()
    # Adding a realistic user agent can help prevent 403 errors
    cl.set_user_agent("Instagram 219.0.0.12.117 Android (28/9; 480dpi; 1080x1920; OnePlus; OnePlus 6T; en_US)")

    logged_in = False

    # Attempt 1: Use existing session
    if IG_SESSION:
        try:
            print("🔄 Attempting login via stored session...")
            cl.set_settings(json.loads(IG_SESSION))
            cl.get_timeline_feed() # Test the session
            print(f"✅ Session successful for {IG_USERNAME}")
            logged_in = True
        except Exception as e:
            print(f"⚠️ Session login failed: {e}")

    # Attempt 2: Direct Login Fallback
    if not logged_in:
        try:
            print(f"🔄 Attempting fresh login for {IG_USERNAME}...")
            time.sleep(2) # Brief pause to avoid "spammy" behavior
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("✅ Fresh login successful!")
            # Optional: Log the new session string to update your IG_SESSION secret
            # print(f"NEW_SESSION: {json.dumps(cl.get_settings())}")
        except Exception as e:
            print(f"❌ Full Instagram Auth failure: {e}")
            return

    # --- 2. TELEGRAM CONTENT FETCH ---
    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Accessing channel: {CHANNEL_ID}")
            # offset=-1 grabs the absolute latest post in the channel
            updates = await bot.get_updates(offset=-1, limit=5)
            
            target_post = None
            for update in reversed(updates):
                msg = update.channel_post
                if msg and msg.photo:
                    target_post = msg
                    break
            
            if not target_post:
                print("ℹ️ No recent photo posts found. Try forwarding the card to the channel again.")
                return

            print(f"📸 Found Post: {target_post.caption[:40]}...")
            
            # Fetch the highest resolution image
            file = await bot.get_file(target_post.photo[-1].file_id)
            photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            
            # Download temporarily
            img_data = requests.get(photo_url).content
            with open("sync_image.jpg", "wb") as handler:
                handler.write(img_data)

            # --- 3. UPLOAD TO INSTAGRAM ---
            print("📤 Syncing to Instagram...")
            # Using caption from Telegram post
            media = cl.photo_upload("sync_image.jpg", target_post.caption or "")
            print(f"🚀 SUCCESS! Instagram Media ID: {media.pk}")
            
            # Cleanup
            if os.path.exists("sync_image.jpg"):
                os.remove("sync_image.jpg")

        except Exception as e:
            print(f"❌ Telegram Sync Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
