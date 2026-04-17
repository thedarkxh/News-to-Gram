import os
import json
import asyncio
import requests
from aiogram import Bot
from instagrapi import Client

# 1. Load Credentials from GitHub Secrets
TOKEN = os.getenv("TOKEN")             # Telegram Bot Token
IG_SESSION = os.getenv("IG_SESSION")   # The content of your session.json
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID")   # e.g., "@tedshx" or "-100..."

bot = Bot(token=TOKEN)
ig_client = Client()

def login_ig():
    """Bypasses login using the saved session to avoid IP blacklist."""
    if not IG_SESSION:
        print("❌ Error: IG_SESSION secret is missing!")
        return False
    
    try:
        print("🔄 Loading Instagram session...")
        session_data = json.loads(IG_SESSION)
        ig_client.set_settings(session_data)
        
        # Test if the session is still valid
        ig_client.get_timeline_feed() 
        print(f"✅ Logged in as: {IG_USERNAME}")
        return True
    except Exception as e:
        print(f"⚠️ Session expired: {e}")
        # Only try fresh login as absolute last resort
        try:
            print("🔄 Attempting fresh login fallback...")
            ig_client.login(IG_USERNAME, IG_PASSWORD)
            return True
        except Exception as err:
            print(f"❌ Instagram Auth Failed: {err}")
            return False

async def fetch_and_post():
    """Finds the latest photo in the TG channel and posts it to IG."""
    try:
        # Get the latest message from the channel
        # Note: We use get_updates for simplicity, 
        # but in a real loop, you'd track the last 'message_id'
        updates = await bot.get_updates(limit=10, allowed_updates=["channel_post"])
        
        for update in reversed(updates):
            if update.channel_post and update.channel_post.photo:
                print("📸 Found a photo post in Telegram!")
                
                # Get the highest resolution version of the photo
                photo = update.channel_post.photo[-1]
                file_info = await bot.get_file(photo.file_id)
                photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                
                # Download locally for upload
                photo_path = "temp_post.jpg"
                with open(photo_path, 'wb') as f:
                    f.write(requests.get(photo_url).content)
                
                # Prepare Caption
                caption = update.channel_post.caption or ""
                # Clean up specific Telegram tags if needed
                caption += "\n\n#news #update" 

                # Upload to Instagram
                print("📤 Uploading to Instagram...")
                media = ig_client.photo_upload(photo_path, caption)
                print(f"🚀 Success! IG Post ID: {media.pk}")
                
                # Cleanup
                os.remove(photo_path)
                return # Stop after the first successful sync
                
    except Exception as e:
        print(f"❌ Sync Error: {e}")

async def main():
    if login_ig():
        await fetch_and_post()

if __name__ == "__main__":
    asyncio.run(main())
