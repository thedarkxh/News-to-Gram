import os
import asyncio
import textwrap
import requests
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# Configuration from Secrets
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group"
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #facts #india #trending"

async def generate_branded_card(headline, news_brief, tg_image_path):
    print("🎨 Generating branded card...")
    # 1. Initialize 1080x1080 Template (Black background)
    width, height = 1080, 1080
    background_color = (0, 0, 0)
    img = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(img, 'RGBA')

    # 2. Add Red Header Bar (15% height)
    draw.rectangle([0, 0, 1080, 150], fill=(211, 47, 47)) # Dark Red

    # 3. Handle Fonts (Fallback to DejaVuSans installed on Linux if project fonts missing)
    try:
        # Try project local fonts first
        font_latest = ImageFont.truetype("BebasNeue-Regular.ttf", 60)
        font_h = ImageFont.truetype("Montserrat-SemiBold.ttf", 60)
        font_b = ImageFont.truetype("Montserrat-SemiBold.ttf", 35) # Same font, smaller size
    except:
        # Fallback to standard system fonts on GitHub Runner
        print("⚠️ Custom fonts not found, using fallbacks.")
        font_latest = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)

    # 4. Draw Header Text ("LATEST")
    # Centering logic
    w_latest = draw.textlength("LATEST", font=font_latest)
    draw.text(((1080 - w_latest) / 2, 45), "LATEST", font=font_latest, fill=(255, 255, 255))

    # 5. Place the downloaded original image (Centered)
    bg = Image.open(tg_image_path).convert("RGB")
    # Resize keeping aspect ratio, max width 1080
    r_w, r_h = bg.size
    target_w = 1080
    target_h = int(r_h * (target_w / r_w))
    
    # Check if height exceeds available space (Header: 150, Footer: 400. Middle space: 530)
    # We allow the middle image to be a bit flexible, we can adjust the target_h if needed.
    resized_bg = bg.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Define vertical center of middle area
    middle_y_center = (150 + 680) / 2 
    img.paste(resized_bg, (0, int(middle_y_center - (target_h / 2))))

    # 6. Add Dark Gray Footer Gradient/Box for text readability
    draw.rectangle([0, 680, 1080, 1080], fill=(28, 28, 28)) # Off-Black
    draw.rectangle([0, 680, 1080, 710], fill=(211, 47, 47, 100)) # Thin red line accent (translucent)

    # 7. Draw Headline (Bold, all caps)
    curr_y = 730
    w_h = 30 # Wrap width for Montserrat Bold
    # The wrap width is character-based, we need to convert your headline to character count
    headline_lines = textwrap.wrap(headline.upper(), width=w_h)
    
    # Center each line of headline
    for line in headline_lines:
        w_line = draw.textlength(line, font=font_h)
        draw.text(((1080 - w_line) / 2, curr_y), line, font=font_h, fill=(255, 255, 255))
        curr_y += 75
        
    # 8. Draw Brief (News Body)
    curr_y += 25
    w_b = 60 # Wrap width for Montserrat SemiBold small
    # Get the brief from the caption processing (see main)
    body_lines = textwrap.wrap(news_brief, width=w_b)
    for line in body_lines:
        w_line = draw.textlength(line, font=font_b)
        draw.text(((1080 - w_line) / 2, curr_y), line, font=font_b, fill=(200, 200, 200))
        curr_y += 45

    img.save("post_image.jpg", quality=95)
    print("✅ All assets ready.")

async def main():
    if not TOKEN or not CHANNEL_ID:
        print("❌ ERROR: Missing secrets.")
        return

    async with Bot(token=TOKEN) as bot:
        try:
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

            # Process Caption Text
            raw_text = target_msg.caption or ""
            lines = [l for l in raw_text.split('\n') if l.strip()]
            
            # The headline is the first line
            headline = lines[0] if lines else "NEWS UPDATE"
            # The brief is the body. We'll grab the first sentence of the body for the image text.
            raw_brief = " ".join(lines[1:3]) if len(lines) > 1 else ""
            brief_sentence = raw_brief.split('.')[0] + '.' if '.' in raw_brief else raw_brief

            # 1. Generate the Branded Image (Uses downloaded original, headline, brief)
            await generate_branded_card(headline, brief_sentence, tg_img_path)

            # 2. Generate the Caption for IG (unchanged, still cleans clutter and adds CTA)
            clean_lines = [l for l in lines if not any(w in l.upper() for w in ["READ FULL STORY", "RELATED:", "JOIN"])]
            news_content = "\n".join(clean_lines).strip()
            new_cta = f"🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
            
            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(f"{news_content}\n\n{new_cta}\n\n{HASHTAGS}")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
