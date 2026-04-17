import os
import asyncio
import requests
from aiogram import Bot
from instagrapi import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv("TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
# Channel/User to send the TG update to
TG_CHAT_ID = os.getenv("TG_CHAT_ID") 

# Initialize Clients
bot = Bot(token=TELEGRAM_TOKEN)
ig_client = Client()

def login_instagram():
    """Handles Instagram login with simple error catching."""
    try:
        print("Logging into Instagram...")
        ig_client.login(IG_USERNAME, IG_PASSWORD)
        print("Instagram login successful.")
    except Exception as e:
        print(f"Instagram login failed: {e}")
        return False
    return True

async def download_image(url, save_path="temp_image.jpg"):
    """Downloads an image from a URL to a local path."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response:
                f.write(chunk)
        return save_path
    return None

async def process_news_and_post(image_url, caption):
    """Posts to both Telegram and Instagram."""
    
    # 1. Post to Telegram
    try:
        await bot.send_photo(chat_id=TG_CHAT_ID, photo=image_url, caption=caption)
        print("Posted to Telegram.")
    except Exception as e:
        print(f"Telegram error: {e}")

    # 2. Post to Instagram
    local_path = await download_image(image_url)
    if local_path:
        try:
            # instagrapi is synchronous, so we run in a thread or just call it 
            # if the script's primary job is this single loop.
            media = ig_client.photo_upload(local_path, caption)
            print(f"Posted to Instagram: {media.pk}")
        except Exception as e:
            print(f"Instagram Upload error: {e}")
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

async def main():
    # Attempt IG Login
    if not login_instagram():
        return

    # Logic to fetch your news (placeholder for your specific scraper/API)
    # Example:
    news_data = [
        {
            "image": "https://example.com/news_image.jpg",
            "text": "Breaking News: Automated posting is live! #tech #news"
        }
    ]

    for news in news_data:
        await process_news_and_post(news["image"], news["text"])

if __name__ == "__main__":
    asyncio.run(main())
