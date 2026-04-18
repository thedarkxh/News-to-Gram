import os
import asyncio
import requests
import random
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(OUTPUT_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(OUTPUT_DIR, "temp.jpg")
CAP_PATH   = os.path.join(OUTPUT_DIR, "post_caption.txt")

# Standard Gen Z Palettes
ACCENTS = [(0, 255, 127), (255, 20, 147), (0, 191, 255), (255, 165, 0)]

def get_font(name, size):
    """Fallback font loader to prevent 'None' errors."""
    font_map = {
        "bold": "Poppins-SemiBold.ttf",
        "medium": "Poppins-Medium.ttf",
        "anton": "Anton-Regular.ttf"
    }
    try:
        return ImageFont.truetype(font_map.get(name, "Poppins-SemiBold.ttf"), size)
    except:
        return ImageFont.load_default()

def wrap_text(text, font, max_px):
    """Wraps text properly so it doesn't bleed off the edges."""
    words = text.split()
    lines = []
    curr_line = ""
    d = ImageDraw.Draw(Image.new('RGB', (1,1)))
    
    for word in words:
        test = f"{curr_line} {word}".strip()
        bbox = d.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_px:
            curr_line = test
        else:
            lines.append(curr_line)
            curr_line = word
    lines.append(curr_line)
    return lines

async def generate_card(headline, source, photo_path):
    W, H = 1080, 1080
    accent = random.choice(ACCENTS)
    
    # 1. Background Image
    bg = Image.open(photo_path).convert("RGB")
    scale = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*scale), int(bg.height*scale)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))
    
    # Add a darkening overlay so white text pops
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 120)) # Darker tint
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    
    draw = ImageDraw.Draw(bg)

    # 2. Top "LATEST" Bar
    draw.rectangle([0, 0, W, 130], fill=(211, 47, 47))
    draw.text((W//2, 65), "LATEST", font=get_font("anton", 75), fill="white", anchor="mm")

    # 3. Breaking News Label
    margin = 60
    draw.rectangle([margin, 695, margin + 10, 745], fill=accent)
    draw.text((margin + 25, 720), "BREAKING NEWS", font=get_font("bold", 48), fill="white", anchor="lm")

    # 4. Headline (The part that was missing)
    f_head = get_font("bold", 75)
    wrapped = wrap_text(headline.upper(), f_head, W - (margin * 2))
    
    y_start = 770
    for line in wrapped:
        # Drawing a shadow first for readability
        draw.text((margin + 3, y_start + 3), line, font=f_head, fill=(0, 0, 0, 180))
        # Drawing the actual text
        draw.text((margin, y_start), line, font=f_head, fill="white")
        y_start += 90

    # 5. Source
    if source:
        f_src = get_font("medium", 36)
        draw.rectangle([margin, 1010, margin + 80, 1016], fill=accent)
        draw.text((margin, 1025), f"SOURCE: {source.upper()}", font=f_src, fill=(220, 220, 220))

    bg.save(IMG_PATH, quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            # Find the message with the photo
            post = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not post:
                print("No photo found in channel.")
                return

            # Download
            file = await bot.get_file(post.photo[-1].file_id)
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Parse Caption
            lines = [l.strip() for l in (post.caption or "").split("\n") if l.strip()]
            headline = lines[0] if lines else "BREAKING NEWS"
            
            # Clean source logic
            source = ""
            for l in lines:
                if "SOURCE" in l.upper():
                    source = l.upper().replace("SOURCE:", "").replace("🔗", "").replace("THE HINDU", "THE HINDU").strip()

            await generate_card(headline, source, TEMP_PATH)
            print("✅ Success: Image saved with Headline.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
