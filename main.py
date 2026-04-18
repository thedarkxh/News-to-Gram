import os
import asyncio
import requests
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import re

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

# Use absolute paths to ensure GitHub Actions finds them
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(BASE_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(BASE_DIR, "temp.jpg")
CAP_PATH   = os.path.join(BASE_DIR, "post_caption.txt")

# CRITICAL: If these files aren't in your repo, the script will use default tiny fonts
# Place Poppins-Bold.ttf in your root folder!
FONT_BOLD = os.path.join(BASE_DIR, "Poppins-Bold.ttf")
FONT_MED  = os.path.join(BASE_DIR, "Poppins-Medium.ttf")

JUNK_KW = ["READ FULL STORY", "RELATED", "JOIN", "SOURCE", "🔗", "HTTP"]

def clean_text(text: str) -> str:
    """Removes emojis and symbols that cause 'boxes' in standard fonts."""
    return re.sub(r'[^\x00-\x7F]+', '', text).strip()

def is_junk_line(line: str) -> bool:
    return any(k in line.upper() for k in JUNK_KW)

def extract_source(lines: list[str]) -> str:
    for line in lines:
        if "SOURCE" in line.upper():
            clean = line.replace("Source:", "").replace("SOURCE:", "").replace("source:", "")
            parts = [p for p in clean.split() if not p.startswith("http") and "🔗" not in p]
            return " ".join(parts).strip()
    return ""

def wrap_to_px(text: str, font, max_px: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.upper().split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_px:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

async def generate_card(headline: str, source: str, photo_path: str):
    W, H = 1080, 1080
    
    # Improved Font Loading
    try:
        f_badge    = ImageFont.truetype(FONT_BOLD, 34)
        f_breaking = ImageFont.truetype(FONT_BOLD, 44)
        f_head     = ImageFont.truetype(FONT_BOLD, 85) # Increased size
        f_src      = ImageFont.truetype(FONT_MED, 38)
    except:
        print("⚠️ Custom fonts not found. Using default.")
        f_badge = f_breaking = f_head = f_src = ImageFont.load_default()

    # 1. Background
    photo = Image.open(photo_path).convert("RGBA")
    scale = max(W / photo.width, H / photo.height)
    photo = photo.resize((int(photo.width * scale), int(photo.height * scale)), Image.Resampling.LANCZOS)
    photo = photo.crop(((photo.width-W)//2, (photo.height-H)//2, (photo.width+W)//2, (photo.height+H)//2))

    # 2. Dark Gradient (Ensures white text is visible)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(400, H): # Gradient starts from middle
        alpha = int(220 * ((y - 400) / 680)**0.6)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    
    canvas = Image.alpha_composite(photo, overlay)
    draw = ImageDraw.Draw(canvas)

    # 3. Text Elements
    margin = 60
    
    # Breaking News Tag
    draw.rectangle([margin, 600, margin + 8, 650], fill=(211, 47, 47, 255))
    draw.text((margin + 20, 605), "BREAKING NEWS", font=f_breaking, fill="white")

    # Headline - Cleaned of emojis to prevent boxes
    clean_head = clean_text(headline)
    head_lines = wrap_to_px(clean_head, f_head, W - (margin * 2), draw)
    
    y_cursor = 670
    for line in head_lines:
        # Shadow for readability
        draw.text((margin+2, y_cursor+2), line, font=f_head, fill=(0,0,0,150))
        draw.text((margin, y_cursor), line, font=f_head, fill="white")
        y_cursor += 100

    # 4. Source
    if source:
        src_text = f"SOURCE: {clean_text(source)}"
        draw.text((margin, H - 100), src_text, font=f_src, fill=(200, 200, 200, 255))

    canvas.convert("RGB").save(IMG_PATH, quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            # Find last post with photo
            target = None
            for u in reversed(updates):
                if u.channel_post and u.channel_post.photo:
                    target = u.channel_post
                    break
            
            if not target:
                print("❌ No photo post found.")
                return

            # Download Photo
            file = await bot.get_file(target.photo[-1].file_id)
            img_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(img_url).content)

            # Process Text
            caption = target.caption or ""
            lines = [l.strip() for l in caption.split("\n") if l.strip()]
            headline = lines[0] if lines else "BREAKING NEWS"
            source = extract_source(lines)

            # Generate the image
            await generate_card(headline, source, TEMP_PATH)

            # Generate the caption file
            clean_lines = [l for l in lines if not is_junk_line(l)]
            final_cap = "\n".join(clean_lines)
            final_cap += f"\n\n🏛️ Read Full Story: Link in Bio @{IG_HANDLE}\n\n{HASHTAGS}"
            
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(final_cap)

            print("✅ Card & Caption generated successfully.")

        except Exception as e:
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
