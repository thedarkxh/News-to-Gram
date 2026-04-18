import os
import asyncio
import requests
import textwrap
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(BASE_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(BASE_DIR, "temp.jpg")

# Standard paths for Linux/GitHub Actions
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def clean_and_format(text):
    """Removes boxes/emojis and returns clean uppercase string."""
    # Strips non-ASCII characters that cause white boxes
    return text.encode('ascii', 'ignore').decode('ascii').strip().upper()

async def generate_premium_card(headline_text, source_name, photo_path):
    W, H = 1080, 1080
    bg = Image.open(photo_path).convert("RGB")
    
    # 1. Square Crop Logic
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio), int(bg.height*ratio)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))

    # 2. Gradient Overlay for Text Readability
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(500, H):
        alpha = int(220 * ((y - 500) / 580) ** 1.1)
        draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 255)))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)
    margin = 70

    # 3. 'LATEST' Brand Tag
    draw.rectangle([margin, 60, margin + 220, 120], fill=(211, 47, 47))
    draw.text((margin + 110, 92), "LATEST", font=ImageFont.truetype(FONT_BOLD, 36), fill="white", anchor="mm")

    # 4. 'BREAKING NEWS' Header
    draw.rectangle([margin, 680, margin + 8, 730], fill=(211, 47, 47))
    draw.text((margin + 25, 685), "BREAKING NEWS", font=ImageFont.truetype(FONT_BOLD, 42), fill="white")

    # 5. Main Highlighted Line (The Dynamic Headline)
    h_font = ImageFont.truetype(FONT_BOLD, 74)
    # Wrap text to ensure it fits the width
    wrapped_headline = textwrap.wrap(clean_and_format(headline_text), width=22)
    
    y_cursor = 760
    for line in wrapped_headline:
        # Subtle stroke for legibility
        for off in [(-2,-2), (2,-2), (-2,2), (2,2)]:
            draw.text((margin + off[0], y_cursor + off[1]), line, font=h_font, fill="black")
        draw.text((margin, y_cursor), line, font=h_font, fill="white")
        y_cursor += 85

    # 6. Source Footer
    if source_name:
        s_font = ImageFont.truetype(FONT_REG, 32)
        draw.text((margin, H - 80), f"SOURCE: {clean_and_format(source_name)}", fill=(180, 180, 180), font=s_font)

    bg.save(IMG_PATH, quality=98)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            post = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not post: return

            # Download photo from Telegram
            file = await bot.get_file(post.photo[-1].file_id)
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # --- Logic to extract the Highlighted Line ---
            lines = [l.strip() for l in post.caption.split("\n") if l.strip()]
            
            # The highlighted line is usually the first line after 'BREAKING NEWS' 
            # or the first substantive sentence
            headline = lines[1] if len(lines) > 1 else lines[0]
            source = next((l.split(":")[-1].strip() for l in lines if "SOURCE" in l.upper()), "Various")

            await generate_premium_card(headline, source, TEMP_PATH)
            print("✅ Success: Card generated with highlighted headline.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
