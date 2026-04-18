import os
import asyncio
import requests
import random
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

# Paths
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(OUTPUT_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(OUTPUT_DIR, "temp.jpg")
CAP_PATH   = os.path.join(OUTPUT_DIR, "post_caption.txt")

# Modern Gen Z Accent Colors
ACCENTS = [(0, 255, 127), (255, 20, 147), (0, 191, 255), (255, 165, 0)]

def get_font(name, size):
    """Attempt to load custom fonts from the local directory."""
    font_files = {
        "bold": "Poppins-SemiBold.ttf",
        "medium": "Poppins-Medium.ttf",
        "regular": "Poppins-Regular.ttf",
        "anton": "Anton-Regular.ttf"
    }
    try:
        return ImageFont.truetype(font_files.get(name, "regular"), size)
    except:
        return ImageFont.load_default()

def wrap_text(text, font, max_width):
    """Wrap text to fit within a specific pixel width."""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        # Get width of the line
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

async def generate_card(headline, source, photo_path):
    W, H = 1080, 1080
    accent_color = random.choice(ACCENTS)
    
    # 1. Background Image Processing
    photo = Image.open(photo_path).convert("RGB")
    pw, ph = photo.size
    scale = max(W/pw, H/ph)
    photo = photo.resize((int(pw*scale), int(ph*scale)), Image.LANCZOS)
    photo = photo.crop(((photo.width-W)//2, (photo.height-H)//2, (photo.width+W)//2, (photo.height+H)//2))
    
    # Apply a slight dark tint to the whole image for text readability
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 100))
    photo = Image.alpha_composite(photo.convert("RGBA"), overlay).convert("RGB")
    
    canvas = Image.new("RGB", (W, H), color=(10, 10, 10))
    canvas.paste(photo, (0, 0))
    draw = ImageDraw.Draw(canvas)

    # 2. Header "LATEST" Badge
    draw.rectangle([0, 0, W, 140], fill=(211, 47, 47))
    f_latest = get_font("anton", 75)
    draw.text((W//2, 70), "LATEST", font=f_latest, fill="white", anchor="mm")

    # 3. Text Area Prep
    margin = 60
    max_w = W - (margin * 2)
    
    # 4. Breaking News Tag
    f_break = get_font("bold", 45)
    draw.rectangle([margin, 680, margin + 8, 730], fill=accent_color)
    draw.text((margin + 25, 705), "BREAKING NEWS", font=f_break, fill="white", anchor="lm")

    # 5. Headline Wrapping & Drawing
    f_head = get_font("bold", 72)
    wrapped_lines = wrap_text(headline.upper(), f_head, max_w)
    
    y_text = 760
    for line in wrapped_lines:
        # Subtle Drop Shadow
        draw.text((margin+3, y_text+3), line, font=f_head, fill=(0,0,0,150))
        # Main White Text
        draw.text((margin, y_text), line, font=f_head, fill="white")
        y_text += 85

    # 6. Source & Bottom Accent
    if source:
        f_src = get_font("medium", 35)
        draw.rectangle([margin, 1010, margin + 60, 1015], fill=accent_color)
        draw.text((margin, 1030), f"SOURCE: {source.upper()}", font=f_src, fill=(200, 200, 200))

    canvas.save(IMG_PATH, quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            target = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not target: return

            file = await bot.get_file(target.photo[-1].file_id)
            img_data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content
            with open(TEMP_PATH, "wb") as f: f.write(img_data)

            lines = [l.strip() for l in (target.caption or "").split("\n") if l.strip()]
            headline = lines[0] if lines else "News Update"
            
            # Extract clean source name
            source = ""
            for l in lines:
                if "SOURCE" in l.upper():
                    source = l.upper().replace("SOURCE:", "").replace("🔗", "").strip()

            await generate_card(headline, source, TEMP_PATH)

            # Cleanup Caption for .txt
            junk = ["READ FULL STORY", "RELATED", "JOIN", "🔗"]
            clean_lines = [l for l in lines if not any(j in l.upper() for j in junk)]
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(clean_lines) + f"\n\n🏛️ Read Full Story: Link in Bio @{IG_HANDLE}\n\n{HASHTAGS}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
