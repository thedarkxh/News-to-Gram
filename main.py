import os
import asyncio
import requests
from aiogram import Bot

# Config
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group" # Your IG handle for the redirect

# Relevant tags for the news niche
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #facts #india #trending #knowledge"

async def main():
    if not TOKEN or not CHANNEL_ID:
        print("❌ ERROR: Missing TOKEN or CHANNEL_ID.")
        return

    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Fetching latest card from {CHANNEL_ID}...")
            updates = await bot.get_updates(offset=-1, limit=5)
            target_msg = next((u.channel_post for u in reversed(updates) if u.channel_post and u.photo), None)
            
            if not target_msg:
                print("ℹ️ No recent news cards found.")
                return

            # 1. Download Image
            photo = target_msg.photo[-1]
            file = await bot.get_file(photo.file_id)
            url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            
            with open("post_image.jpg", "wb") as f:
                f.write(requests.get(url).content)
            
            # 2. Process Caption & Merge Last Lines
            original_lines = (target_msg.caption or "").split('\n')
            
            # Filter: Removes Source, Read Full Story, and Related Channel info
            clean_lines = [
                line for line in original_lines 
                if not any(word in line.upper() for word in ["SOURCE:", "READ FULL STORY", "RELATED:", "JOIN"])
            ]
            
            # Clean up empty lines at the end
            news_content = "\n".join(clean_lines).strip()
            
            # Create the combined CTA you described
            # Redirects audience to your bio link while tagging your account
            new_cta = f"🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
            
            # Construct Final Caption
            final_caption = f"{news_content}\n\n{new_cta}\n\n{HASHTAGS}"

            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(final_caption)

            print(f"✅ Post Ready! Image saved and caption updated with CTA & Tags.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
