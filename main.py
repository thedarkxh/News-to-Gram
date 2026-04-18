import os
import asyncio
import textwrap
import requests
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# Configuration
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group"
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #facts #india #trending"

async def generate_branded_card(headline, news_brief, tg_image_path):
    print("🎨 Generating premium branded card...")
    # 1. Initialize 1080x1080 Canvas
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img, 'RGBA')

    # 2. Red Header Section (Top 150px)
    draw.rectangle([0, 0, 1080, 150], fill=(211, 47, 47))

    # 3. Font Setup (Using DejaVuSans as a reliable fallback on GitHub Runners)
    try:
        font_latest = ImageFont.truetype("BebasNeue-Regular.ttf", 65)
        font_h = ImageFont.truetype("Montserrat-Bold.ttf", 60)
        font_b = ImageFont.truetype("Montserrat-Medium.ttf", 35)
    except:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_latest = ImageFont.truetype(font_path, 65)
        font_h = ImageFont.truetype(font_path, 60)
        font_b = ImageFont.truetype(font_path.replace("-Bold", ""), 35)

    # 4. Draw Header Text
    w_latest = draw.textlength("LATEST", font=font_latest)
    draw.text(((1080 - w_latest) / 2, 40), "LATEST", font=font_latest, fill=(255, 255, 255))

    # 5. Process and Center Original Image
    bg = Image.open(tg_image_path).convert("RGB")
    r_w, r_h = bg.size
    # Resize to fit 1080 width
    target_h = int(r_h * (1080 / r_w))
    resized_bg = bg.resize((1080, target_h), Image.Resampling.LANCZOS)
    
    # Paste image in the center area (between header and footer)
    img.paste(resized_bg, (0, int(415 - (target_h / 2))))

    # 6. Black Footer Section (Starting at 680px)
    draw.rectangle([0, 680, 1080, 1080], fill=(15, 15, 15))
    draw.rectangle([0, 680, 1080, 685], fill=(211, 47, 47)) # Accent Line

    # 7. Draw Headline (Centered)
    curr_y = 720
    for line in textwrap.wrap(headline.upper(), width=30):
        w_line = draw.textlength(line, font=font_h)
        draw.text(((1080 - w_line) / 2, curr_y), line, font=font_h, fill=(255, 255, 255))
        curr_y += 75
        
    # 8. Draw Brief Body
    curr_y += 20
    for line in textwrap.wrap(news_brief, width=65):
        w_line = draw.textlength(line, font=font_b)
        draw.text(((1080 - w_line) / 2, curr_y), line, font=font_b, fill=(200, 200, 200))
        curr_y += 45

    img.save("post_image.jpg", quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            # FIX: Correctly traverse Update to ChannelPost
            updates = await bot.get_updates(offset=-1, limit=5)
            target_msg = None
            for upd in reversed(updates):
                if upd.channel_post and upd.channel_post.photo:
                    target_msg = upd.channel_post
                    break
            
            if not target_msg:
                print("❌ No photo post found.")
                return

            # Download Media
            file = await bot.get_file(target_msg.photo[-1].file_id)
            tg_img_path = "tg_input.jpg"
            with open(tg_img_path, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Process Text
            raw_lines = [l.strip() for l in (target_msg.caption or "").split('\n') if l.strip()]
            headline = raw_lines[0] if raw_lines else "NEWS UPDATE"
            # Extract first sentence for the image body
            full_body = " ".join(raw_lines[1:])
            brief = full_body.split('.')[0] + '.' if '.' in full_body else full_body[:150]

            # 1. Generate Image Card
            await generate_branded_card(headline, brief, tg_img_path)

            # 2. Generate Instagram Caption (Keeping Source)
            clean_lines = [l for l in raw_lines if not any(w in l.upper() for w in ["READ FULL STORY", "RELATED:", "JOIN"])]
            news_txt = "\n".join(clean_lines)
            cta = f"🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
            
            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(f"{news_txt}\n\n{cta}\n\n{HASHTAGS}")

        except Exception as e:
            print(f"❌ Execution Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
