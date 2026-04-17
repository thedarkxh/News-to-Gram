import os
import json
import asyncio
from aiogram import Bot
from instagrapi import Client

# Load environment variables (GitHub Secrets)
TOKEN = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

bot = Bot(token=TOKEN)
ig_client = Client()

def login_ig():
    """Bypasses login using the saved session."""
    try:
        if IG_SESSION:
            print("Loading IG Session...")
            session_data = json.loads(IG_SESSION)
            ig_client.set_settings(session_data)
            # This check ensures the session is still valid
            ig_client.login(IG_USERNAME, IG_PASSWORD)
            return True
    except Exception as e:
        print(f"Session failed, attempting fresh login: {e}")
        try:
            ig_client.login(IG_USERNAME, IG_PASSWORD)
            return True
        except:
            return False

async def main():
    if not login_ig():
        print("Could not log into Instagram.")
        return

    print("Success! Ready to sync posts.")
    
    # --- ADD YOUR NEWS FETCHING LOGIC HERE ---
    # When you find a news item with an image URL:
    # 1. Download image: requests.get(url).content -> save to "post.jpg"
    # 2. Post to IG: ig_client.photo_upload("post.jpg", "Your Caption")
    # ------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
