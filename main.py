import os
import asyncio
import requests
import textwrap
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(BASE_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(BASE_DIR, "temp.jpg")
CAP_PATH   = os.path.join(BASE_DIR, "post_caption.txt")

# Use DejaVuSans as it is pre-installed on almost all Linux/GitHub environments
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG_FONT  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    """Wraps text accurately based on pixel width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return [l for l in lines if l]

async def generate_optimized_card(headline, source, photo_path):
    # --- SUPER-SAMPLING (Render at 2160x2160 for sharpness) ---
    SCALE = 2
    W, H = 1080 * SCALE, 1080 * SCALE
    MARGIN = 70 * SCALE

    bg = Image.open(photo_path).convert("RGB")
    
    # 1. Resize and Center Crop
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio), int(bg.height*ratio)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))

    # 2. Advanced Gradient Mask (Bottom 40%)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(int(H * 0.55), H):
        # Quadratic fade for premium look
        alpha = int(255 * ((y - (H * 0.55)) / (H * 0.45)) ** 1.4)
        draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 245)))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)

    # 3. Branding "LATEST" Tag
    tag_w, tag_h = 200 * SCALE, 55 * SCALE
    draw.rectangle([MARGIN, 80 * SCALE, MARGIN + tag_w, 80 * SCALE + tag_h], fill=(211, 47, 47))
    draw.text((MARGIN + tag_w//2, 80 * SCALE + tag_h//2), "LATEST", 
              font=get_font(BOLD_FONT, 32 * SCALE), fill="white", anchor="mm")

    # 4. Headline Logic
    h_font = get_font(BOLD_FONT, 78 * SCALE)
    headline_clean = headline.upper().replace("🔗", "").strip()
    wrapped = wrap_text(headline_clean, h_font, W - (MARGIN * 2), draw)
    
    # Position text starting from bottom-middle
    y_cursor = H - (len(wrapped) * (95 * SCALE)) - (160 * SCALE)
    
    for line in wrapped:
        # High-opacity shadow for text pop
        draw.text((MARGIN + 4, y_cursor + 4), line, font=h_font, fill=(0, 0, 0, 220))
        draw.text((MARGIN, y_cursor), line, font=h_font, fill="white")
        y_cursor += 100 * SCALE

    # 5. Source Bar
    if source:
        src_font = get_font(REG_FONT, 34 * SCALE)
        draw.rectangle([MARGIN, H - 100 * SCALE, MARGIN + 100 * SCALE, H - 95 * SCALE], fill=(211, 47, 47))
        draw.text((MARGIN, H - 80 * SCALE), f"SOURCE: {source.upper()}", font=src_font, fill=(190, 190, 190))

    # 6. Final Downscale (This makes text edges look extremely smooth)
    final_img = bg.resize((1080, 1080), Image.Resampling.LANCZOS)
    final_img.save(IMG_PATH, quality=95, subsampling=0)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            post = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not post: return

            # Download
            file = await bot.get_file(post.photo[-1].file_id)
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Text Processing
            caption = post.caption or ""
            lines = [l.strip() for l in caption.split("\n") if l.strip()]
            headline = lines[0] if lines else "BREAKING NEWS"
            source = next((l.split(":")[-1].strip() for l in lines if "SOURCE" in l.upper()), "")

            # SAVE CAPTION FIRST
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(f"{caption}\n\n🏛️ Read Full Story: Link in Bio @{IG_HANDLE}\n\n{HASHTAGS}")

            # GENERATE IMAGE
            await generate_optimized_card(headline, source, TEMP_PATH)
            print("✅ Success: Optimized Card & Caption created.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
