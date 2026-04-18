import os
import asyncio
import requests
import textwrap
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(BASE_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(BASE_DIR, "temp.jpg")
CAP_PATH   = os.path.join(BASE_DIR, "post_caption.txt")

def get_safe_font(size):
    """
    Tries multiple Linux system fonts to ensure readability.
    GitHub Runners usually have DejaVu or Liberation.
    """
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "Poppins-Bold.ttf" # If you uploaded it
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

async def generate_fixed_card(headline, source, photo_path):
    W, H = 1080, 1080
    
    # 1. Background Setup
    bg = Image.open(photo_path).convert("RGB")
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio), int(bg.height*ratio)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))

    # 2. Heavy Gradient (Ensures readability on ANY image)
    # We are making the bottom half significantly darker
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(450, H):
        # Steeper curve for maximum contrast
        alpha = int(255 * ((y - 450) / 630) ** 1.1)
        draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 255)))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)
    
    # 3. Forced Headline Rendering
    # Using a slightly smaller character width (18) to ensure it doesn't bleed off
    headline_clean = headline.upper().strip()
    wrapped_lines = textwrap.wrap(headline_clean, width=18) 
    
    # Determine Font Size - Large for impact
    font_size = 82
    h_font = get_safe_font(font_size)
    
    # Start drawing from the bottom up based on line count
    margin_x = 70
    line_spacing = 95
    total_text_height = len(wrapped_lines) * line_spacing
    current_y = (H - 150) - total_text_height 

    for line in wrapped_lines:
        # HIGH VISIBILITY: Draw a thick black border/shadow around the text
        # This is the 'secret sauce' for readability on parliament/busy backgrounds
        for offset in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            draw.text((margin_x + offset[0], current_y + offset[1]), line, font=h_font, fill="black")
        
        # Main White Text
        draw.text((margin_x, current_y), line, font=h_font, fill="white")
        current_y += line_spacing

    # 4. Source Bar (Pinned to bottom)
    if source:
        src_font = get_safe_font(30)
        draw.rectangle([margin_x, H-100, margin_x+80, H-95], fill=(211, 47, 47))
        draw.text((margin_x, H-80), f"SOURCE: {source.upper()}", font=src_font, fill=(200, 200, 200))

    # 5. LATEST Tag (Top Left)
    draw.rectangle([margin_x, 60, margin_x+200, 110], fill=(211, 47, 47))
    draw.text((margin_x+100, 85), "LATEST", font=get_safe_font(32), fill="white", anchor="mm")

    bg.save(IMG_PATH, quality=98)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            post = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not post:
                print("No photo post found.")
                return

            # Download Photo
            file = await bot.get_file(post.photo[-1].file_id)
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Process Text
            caption = post.caption or ""
            lines = [l.strip() for l in caption.split("\n") if l.strip()]
            headline = lines[0] if lines else "NEWS UPDATE"
            source = next((l.split(":")[-1].strip() for l in lines if "SOURCE" in l.upper()), "")

            # 1. ALWAYS save caption first so you don't lose it
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(f"{caption}\n\n🏛️ Read Full Story: Link in Bio @{IG_HANDLE}\n\n{HASHTAGS}")

            # 2. Generate Image with high-contrast logic
            await generate_fixed_card(headline, source, TEMP_PATH)
            print("✅ Fixed: Headline rendered with outline for readability.")

        except Exception as e:
            print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
