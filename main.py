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
        print("❌ ERROR: Missing Secrets.")
        return

    async with Bot(token=TOKEN) as bot:
        ig_client = Client()

        # 1. Instagram Login
        try:
            ig_client.set_settings(json.loads(IG_SESSION))
            ig_client.get_settings() 
            print(f"✅ Logged into Instagram: {IG_USERNAME}")
        except Exception as e:
            print(f"❌ IG Auth Failed: {e}")
            return

        # 2. Fetching the specific post from the channel
        try:
            print(f"📡 Accessing channel: {CHANNEL_ID}")
            
            # Direct check for the chat to ensure bot is an admin
            chat = await bot.get_chat(CHANNEL_ID)
            print(f"🔗 Targeted Channel: {chat.title}")

            # We fetch updates WITHOUT offset. 
            # This looks at the absolute latest message the bot has access to.
            updates = await bot.get_updates(limit=10)
            
            # Filter updates specifically for your channel ID
            target_msg = None
            for update in reversed(updates):
                msg = update.channel_post
                if msg and (str(msg.chat.id) == str(CHANNEL_ID) or msg.chat.username == str(CHANNEL_ID).replace('@','')):
                    if msg.photo:
                        target_msg = msg
                        break

            if target_msg:
                print(f"📸 Found headline: {target_msg.caption[:50]}...")
                
                photo = target_msg.photo[-1]
                file = await bot.get_file(photo.file_id)
                url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
                
                with open("sync_card.jpg", "wb") as f:
                    f.write(requests.get(url).content)
                
                print("📤 Syncing to Instagram...")
                media = ig_client.photo_upload("sync_card.jpg", target_msg.caption)
                print(f"🚀 SUCCESS! IG Post ID: {media.pk}")
                
                os.remove("sync_card.jpg")
            else:
                print("ℹ️ No media found in the buffer. Please post the news card to the channel AGAIN while this script is starting.")

        except Exception as e:
            print(f"❌ Telegram Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
