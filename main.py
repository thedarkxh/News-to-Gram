import os
import asyncio
import requests
import textwrap
import shutil
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
# This is the main folder where everything will be compiled
OUTPUT_DIR = os.path.join(BASE_DIR, "output") 

# Font Paths (Standard for Linux environments)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_fitted_font(text, max_w, max_h, font_path, start_size):
    size = start_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        char_w = font.getbbox("A")[2] - font.getbbox("A")[0]
        wrap_chars = max(1, int(max_w / char_w))
        lines = textwrap.wrap(text, width=wrap_chars)
        line_h = font.getbbox("HG")[3] - font.getbbox("HG")[1]
        if (len(lines) * (line_h + 12)) <= max_h:
            return font, lines, line_h
        size -= 2
    return ImageFont.load_default(), [text], 20

async def generate_card(body_text, source, photo_path, save_path):
    W, H = 1080, 1080
    bg = Image.open(photo_path).convert("RGB")
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio), int(bg.height*ratio)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))

    # Dark Gradient Overlay
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(550, H):
        alpha = int(255 * ((y - 550) / 530) ** 1.1)
        draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 255)))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)
    margin = 80

    # Red "LATEST" tag
    draw.rectangle([margin, 60, margin + 180, 115], fill=(211, 47, 47))
    draw.text((margin + 90, 87), "LATEST", font=ImageFont.truetype(FONT_BOLD, 30), fill="white", anchor="mm")

    # Body Text (Only the body, scaled to fit)
    clean_body = body_text.encode('ascii', 'ignore').decode('ascii').strip().upper()
    b_font, b_lines, line_h = get_fitted_font(clean_body, W - (margin * 2), 300, FONT_BOLD, 65)
    
    y_cursor = 680
    for line in b_lines:
        draw.text((margin, y_cursor), line, font=b_font, fill="white")
        y_cursor += line_h + 15

    # Source info at bottom
    draw.text((margin, H - 80), f"SOURCE: {source.upper()}", fill=(200, 200, 200), font=ImageFont.truetype(FONT_REG, 26))
    bg.save(save_path, quality=95)

async def main():
    if os.path.exists(OUTPUT_DIR): shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    async with Bot(token=TOKEN) as bot:
        updates = await bot.get_updates(offset=-15, limit=15)
        # Filters for the last 4 posts with photos
        photo_posts = [u.channel_post for u in updates if u.channel_post and u.channel_post.photo][-4:]
        
        for i, post in enumerate(photo_posts, 1):
            folder_path = os.path.join(OUTPUT_DIR, f"post_{i}")
            os.makedirs(folder_path)

            file = await bot.get_file(post.photo[-1].file_id)
            temp_img = os.path.join(folder_path, "raw.jpg")
            with open(temp_img, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            raw_cap = post.caption or ""
            lines = [l.strip() for l in raw_cap.split("\n") if l.strip()]
            
            # Extracting "Body" and "Source"
            body = lines[1] if len(lines) > 1 else lines[0]
            source = next((l.split(":")[-1].strip() for l in lines if "SOURCE" in l.upper()), "The Hindu")

            # Save Image and Caption into the folder
            await generate_card(body, source, temp_img, os.path.join(folder_path, "post_image.jpg"))
            
            with open(os.path.join(folder_path, "post_caption.txt"), "w", encoding="utf-8") as f:
                f.write(f"{raw_cap}\n\n🏛️ Follow @{IG_HANDLE}\n\n{HASHTAGS}")

            os.remove(temp_img)
            print(f"✅ Processed post {i} into /output/post_{i}")

if __name__ == "__main__":
    asyncio.run(main())
