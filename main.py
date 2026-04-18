import os
import asyncio
import requests
import textwrap
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(BASE_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(BASE_DIR, "temp.jpg")
CAP_PATH   = os.path.join(BASE_DIR, "post_caption.txt")

# CRITICAL: We use standard paths for fonts pre-installed on Linux servers
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def sanitize_text(text: str) -> str:
    """Rigorous cleaning to remove emojis, broken chars, and 'weird boxes'."""
    # Keeps ASCII 32-126 (Standard English letters, numbers, and symbols)
    return text.encode('ascii', 'ignore').decode('ascii').strip()

def wrap_text_to_px(text: str, font, max_px: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text precisely, ensuring no line exceeds max_px wide."""
    cleaned = sanitize_text(text).upper()
    words = cleaned.split()
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

async def generate_premium_card(headline, source, photo_path):
    W, H = 1080, 1080
    
    # 1. Image Processing: Full-Bleed Crop
    photo = Image.open(photo_path).convert("RGB")
    pw, ph = photo.size
    scale = max(W / pw, H / ph)
    photo = photo.resize((int(pw * scale), int(ph * scale)), Image.Resampling.LANCZOS)
    photo = photo.crop(((photo.width-W)//2, (photo.height-H)//2, (photo.width+W)//2, (photo.height+H)//2))

    # 2. Add Depth/Overlay (Transparent top → 80% opacity bottom fade)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(400, H):
        # Quadratic blend ensures face visibility while darkening text zone
        alpha = int(210 * ((y - 400) / 680)**1.2)
        od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    
    canvas = Image.alpha_composite(photo.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)

    # 3. Fonts: Dynamically scaled for readability
    try:
        f_badge    = ImageFont.truetype(FONT_PATH, 34)
        f_breaking = ImageFont.truetype(FONT_PATH, 44)
        f_head     = ImageFont.truetype(FONT_PATH, 80) # Increased size for impact
        f_src      = ImageFont.truetype(FONT_PATH, 38)
    except Exception:
        # Fallback if server lacks proper fonts
        f_badge = f_breaking = f_head = f_src = ImageFont.load_default()

    # Text Area Settings
    margin = 60
    
    # 4. Drawing: Brand Elements
    # LATEST Badge
    bbox = draw.textbbox((0,0), "LATEST", font=f_badge)
    b_w = (bbox[2] - bbox[0]) + 40 # text width + padding
    draw.rectangle([margin, 60, margin + b_w, 115], fill=(211, 47, 47))
    draw.text((margin + 20, 68), "LATEST", font=f_badge, fill="white")

    # Breaking News Tag
    draw.rectangle([margin, 700, margin + 8, 750], fill=(211, 47, 47))
    draw.text((margin + 25, 706), "BREAKING NEWS", font=f_breaking, fill="white")

    # 5. Drawing: Headline with Shadow (to prevent invisible text on white background)
    wrapped_lines = wrap_text_to_px(headline, f_head, W - (margin * 2), draw)
    
    current_y = 770
    for line in wrapped_lines:
        # Subtle Drop Shadow (Black with 150 opacity)
        draw.text((margin + 3, current_y + 3), line, font=f_head, fill=(0, 0, 0, 150))
        # Main Text
        draw.text((margin, current_y), line, font=f_head, fill="white")
        current_y += 100

    # 6. Drawing: Source Footer
    if source:
        # Use sanitized source text for footer
        draw.text((margin, H - 100), f"SOURCE: {sanitize_text(source).upper()}", font=f_src, fill=(200, 200, 200))

    canvas.convert("RGB").save(IMG_PATH, quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            target = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not target:
                print("No recent photo post found.")
                return

            # Download Photo
            file_info = await bot.get_file(target.photo[-1].file_id)
            img_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(img_url).content)

            # Process Caption Text
            raw_text = target.caption or ""
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            
            headline = lines[0] if lines else "BREAKING NEWS"
            
            # Smart Source extraction: find the line with 'SOURCE' and isolate the name
            raw_source = next((l for l in lines if "SOURCE" in l.upper()), "Various")
            source_name = raw_source.upper().replace("SOURCE:", "").strip()

            # 1. CREATE IMAGE: Clean, professional, dynamic formatting
            await generate_premium_card(headline, source_name, TEMP_PATH)

            # 2. CREATE CAPTION: Generate the .txt file for Instagram upload
            junk_keywords = ["READ FULL STORY", "RELATED", "JOIN", "🔗"]
            clean_lines = [l for l in lines if not any(j in l.upper() for j in junk_keywords)]
            final_cap = "\n".join(clean_lines).strip()
            final_cap += f"\n\n🏛️ Read Full Story: Link in Bio @{IG_HANDLE}\n\n{HASHTAGS}"
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(final_cap)

            print("✅ Success: Card and Caption generated.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
