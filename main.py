import os
import asyncio
import requests
from aiogram import Bot

# Config
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group" 

# Relevant tags
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #facts #india #trending #knowledge"

async def main():
    if not TOKEN or not CHANNEL_ID:
        print("❌ ERROR: Missing TOKEN or CHANNEL_ID.")
        return

    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Fetching latest card from {CHANNEL_ID}...")
            updates = await bot.get_updates(offset=-1, limit=5)
            
            target_msg = None
            for upd in reversed(updates):
                msg = upd.channel_post 
                if msg and msg.photo:
                    target_msg = msg
                    break
            
            if not target_msg:
                print("ℹ️ No recent news cards found.")
                return

            # 1. Download Image
            photo = target_msg.photo[-1]
            file = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            
            img_data = requests.get(url).content
            with open("post_image.jpg", "wb") as f:
                f.write(img_data)
            
            # 2. Process Caption
            raw_caption = target_msg.caption or ""
            lines = raw_caption.split('\n')
            
            # Updated Filter: Keeps "SOURCE:" but removes the long links/related promos
            clean_lines = [
                line for line in lines 
                if line.strip() and not any(word in line.upper() for word in ["READ FULL STORY", "RELATED:", "JOIN"])
            ]
            
            news_content = "\n".join(clean_lines).strip()
            
            # Unified CTA with redirect
            new_cta = f"🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
            
            # Final assembly: News Content (includes Source) + CTA + Tags
            final_caption = f"{news_content}\n\n{new_cta}\n\n{HASHTAGS}"

            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(final_caption)

            print(f"✅ Success! Caption generated with Source, CTA, and Tags.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
