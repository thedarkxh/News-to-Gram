import os
import json
import asyncio
import requests
from aiogram import Bot
from instagrapi import Client

# Fetching variables
TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

async def main():
    # --- DEBUGGING LOGS ---
    if not TOKEN:
        print("❌ ERROR: TOKEN environment variable is empty!")
        return
    if not IG_SESSION:
        print("❌ ERROR: IG_SESSION environment variable is empty!")
        return
    
    print("✅ Secrets detected. Starting bot...")

    # Initialize Clients
    try:
        bot = Bot(token=TOKEN)
        print("✅ Telegram Bot initialized.")
    except Exception as e:
        print(f"❌ Telegram Token Error: {e}")
        return

    ig_client = Client()

    # Login Logic
    try:
        print("🔄 Loading IG Session...")
        session_data = json.loads(IG_SESSION)
        ig_client.set_settings(session_data)
        ig_client.get_timeline_feed() # Verification
        print(f"✅ Logged into Instagram as {IG_USERNAME}")
    except Exception as e:
        print(f"❌ Instagram Session Error: {e}")
        # Only fallback if absolutely necessary
        try:
            ig_client.login(IG_USERNAME, IG_PASSWORD)
        except:
            return

    # --- YOUR SYNC LOGIC ---
    # Put your channel scraping / posting code here
    print("🚀 Bot is live and syncing...")

if __name__ == "__main__":
    asyncio.run(main())
