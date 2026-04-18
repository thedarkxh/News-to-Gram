import os
import json
import asyncio
import requests
import warnings
from aiogram import Bot
from instagrapi import Client

# Clean logs
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Secrets
TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID") 

async def main():
    if not TOKEN or not IG_USERNAME or not IG_PASSWORD:
        print("❌ ERROR: Missing vital Secrets (TOKEN, IG_USERNAME, or IG_PASSWORD).")
        return

    # --- LAYER 1: INSTAGRAM AUTH ---
    ig_client = Client()
    logged_in = False

    # Try Session First
    if IG_SESSION:
        try:
            print("🔄 Attempting Session Login...")
            ig_client.set_settings(json.loads(IG_SESSION))
            ig_client.get_settings() # Validation call
            print(f"✅ Session Valid: {IG_USERNAME}")
            logged_in = True
        except Exception as e:
            print(f"⚠️ Session expired: {e}")

    # Fallback to Password Login
    if not logged_in:
        try:
            print("🔄 Attempting Password Login Fallback...")
            ig_client.login(IG_USERNAME, IG_PASSWORD)
            print(f"✅ Password Login Successful for: {IG_USERNAME}")
            # Optional: Print this to update your IG_SESSION secret manually one last time
            # print(f"DEBUG: New Session Data: {json.dumps(ig_client.get_settings())}")
        except Exception as e:
            print(f"❌ Instagram Totally Blocked: {e}")
            return

    # --- LAYER 2: TELEGRAM FETCH ---
    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Force-scanning channel: {CHANNEL_ID}")
            
            # offset=-1 tells Telegram to give us the absolute last message in the chat
            updates = await bot.get_updates(offset=-1, limit=10)
            
            target_msg = None
            for update in reversed(updates):
                msg = update.channel_post
                if msg and msg.photo:
                    target_msg = msg
                    break
            
            if not target_msg:
                print("ℹ️ No photo posts found in the Telegram buffer.")
                return

            print(f"📸 Found News Card: {target_msg.caption[:50]}...")
            
            # Download
            photo = target_msg.photo[-1]
            file = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            
            with open("upload.jpg", "wb") as f:
                f.write(requests.get(url).content)
            
            # --- LAYER 3: SYNC ---
            print("📤 Syncing to Instagram...")
            media = ig_client.photo_upload("upload.jpg", target_msg.caption or "")
            print(f"🚀 SUCCESS! Post Live ID: {media.pk}")
            
            os.remove("upload.jpg")

        except Exception as e:
            print(f"❌ Telegram Sync Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
