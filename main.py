import os
import asyncio
import requests
from aiogram import Bot

# Secrets pulled from GitHub Environment
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

async def main():
    if not TOKEN or not CHANNEL_ID:
        print("❌ ERROR: Missing TOKEN or CHANNEL_ID in GitHub Secrets.")
        return

    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Scanning Telegram channel: {CHANNEL_ID}...")
            
            # offset=-1 grabs the absolute latest message in the chat
            updates = await bot.get_updates(offset=-1, limit=5)
            
            target_msg = None
            for update in reversed(updates):
                msg = update.channel_post
                if msg and msg.photo:
                    target_msg = msg
                    break
            
            if not target_msg:
                print("ℹ️ No photo posts found in the Telegram history.")
                return

            print(f"📸 Found News Card: {target_msg.caption[:50]}...")
            
            # 1. Download Image
            photo = target_msg.photo[-1]
            file = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{TOKEN}/{file.path}"
            
            with open("post_image.jpg", "wb") as f:
                f.write(requests.get(url).content)
            
            # 2. Save Caption
            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(target_msg.caption or "")

            print("✅ Files generated: post_image.jpg and post_caption.txt")

        except Exception as e:
            print(f"❌ Telegram Fetch Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
