import os
import asyncio
import textwrap
import requests
from aiogram import Bot
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# Configuration from Secrets
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group"
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #facts #india #trending"

async def generate_premium_card(headline, news_body, tg_image_path):
    # 1. Open and resize background to Instagram Square
    bg = Image.open(tg_image_path).convert("RGB")
    bg = bg.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # 2. Create a Blurred Area for Text (Bottom 45%)
    blur_box = (0, 550, 1080, 1080)
    region = bg.crop(blur_box)
    region = region.filter(ImageFilter.GaussianBlur(radius=30))
    bg.paste(region, blur_box)
    
    # 3. Add Dark Overlay for readability
    draw = ImageDraw.Draw(bg, 'RGBA')
    draw.rectangle(blur_box, fill=(0, 0, 0, 160)) 
    
    # 4. Load Fonts (Falling back to default if not found)
    try:
        # GitHub Runners usually have DejaVuSans installed
        font_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except:
        font_h = ImageFont.load_default()
        font_b = ImageFont.load_default()

    # 5. Draw Headline
    curr_y = 600
    for line in textwrap.wrap(headline.upper(), width=28):
        draw.text((60, curr_y), line, font=font_h, fill=(255, 255, 255))
        curr_y += 70
        
    # 6. Draw Brief (News Body)
    curr_y += 20
    for line in textwrap.wrap(news_body, width=55):
        draw.text((60, curr_y), line, font=font_b, fill=(230, 230, 230))
        curr_y += 45

    bg.save("post_image.jpg", quality=95)
    print("🎨 Premium news card generated: post_image.jpg")

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Fetching from {CHANNEL_ID}...")
            updates = await bot.get_updates(offset=-1, limit=5)
            target_msg = next((u.channel_post for u in reversed(updates) if u.channel_post and u.photo), None)
            
            if not target_msg:
                print("❌ No news card found.")
                return

            # Download Original Image
            file = await bot.get_file(target_msg.photo[-1].file_id)
            tg_img_path = "tg_original.jpg"
            with open(tg_img_path, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Process Text
            raw_text = target_msg.caption or ""
            lines = [l for l in raw_text.split('\n') if l.strip()]
            
            # Use first line as Headline, rest as Brief
            headline = lines[0] if lines else "NEWS UPDATE"
            # Keep the "Source" line in the caption, but maybe not on the image
            brief = " ".join(lines[1:3]) if len(lines) > 1 else ""

            # 1. Generate the Premium Image
            await generate_premium_card(headline, brief, tg_img_path)

            # 2. Generate the Caption for IG
            clean_lines = [l for l in lines if not any(w in l.upper() for w in ["READ FULL STORY", "RELATED:", "JOIN"])]
            news_content = "\n".join(clean_lines).strip()
            new_cta = f"🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
            
            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(f"{news_content}\n\n{new_cta}\n\n{HASHTAGS}")

            print("✅ All assets ready.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
