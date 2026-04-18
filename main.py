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
# Defined here so the script doesn't throw a NameError
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
# Ensure this matches exactly with your .yml path
OUTPUT_DIR = os.path.join(BASE_DIR, "compiled_posts")

# Font Paths (Standard for GitHub Ubuntu Runners)
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_fitted_font(text, max_w, max_h, font_path, start_size):
    size = start_size
    draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
    while size > 22:
        font = ImageFont.truetype(font_path, size)
        char_w = font.getbbox("A")[2] - font.getbbox("A")[0]
        wrap_chars = max(1, int(max_w / char_w))
        lines = textwrap.wrap(text, width=wrap_chars)
        
        line_h = font.getbbox("HG")[3] - font.getbbox("HG")[1]
        if (len(lines) * (line_h + 10)) <= max_h:
            return font, lines, line_h
        size -= 2
    return ImageFont.load_default(), [text], 20

async def generate_card(body_text, source, photo_path, save_path):
    W, H = 1080, 1080
    bg = Image.open(photo_path).convert("RGB")
    
    # Square Crop & Resize
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio), int(bg.height*ratio)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))

    # Gradient Overlay
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(550, H):
        alpha = int(245 * ((y - 550) / 530) ** 1.2)
        draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 255)))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)
    margin = 85

    # "LATEST" Header
    draw.rectangle([margin, 60, margin + 180, 110], fill=(211, 47, 47))
    draw.text((margin + 90, 85), "LATEST", font=ImageFont.truetype(FONT_BOLD, 28), fill="white", anchor="mm")

    # Breaking News Tag
    draw.rectangle([margin, 660, margin + 6, 705], fill=(211, 47, 47))
    draw.text((margin + 20, 665), "BREAKING NEWS", font=ImageFont.truetype(FONT_BOLD, 36), fill="white")

    # Body Text (Auto-scaling to keep "In Frame")
    clean_body = body_text.encode('ascii', 'ignore').decode('ascii').strip().upper()
    b_font, b_lines, line_h = get_fitted_font(clean_body, W - (margin * 2), 240, FONT_BOLD, 62)
    
    y_cursor = 730
    for line in b_lines:
        for off in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            draw.text((margin + off[0], y_cursor + off[1]), line, font=b_font, fill="black")
        draw.text((margin, y_cursor), line, font=b_font, fill="white")
        y_cursor += line_h + 12

    # Source Footer
    s_font = ImageFont.truetype(FONT_REG, 26)
    draw.text((margin, H - 85), f"SOURCE: {source.upper()}", fill=(200, 200, 200), font=s_font)

    bg.save(save_path, quality=95)

async def main():
    # Fresh start for the output directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-15, limit=15)
            # Find last 4 unique photo posts
            photo_posts = [u.channel_post for u in updates if u.channel_post and u.channel_post.photo][-4:]
            
            if not photo_posts:
                print("No recent photo posts found.")
                return

            for i, post in enumerate(photo_posts, 1):
                post_folder = os.path.join(OUTPUT_DIR, f"post_{i}")
                os.makedirs(post_folder, exist_ok=True)

                # Download Image
                file = await bot.get_file(post.photo[-1].file_id)
                temp_img = os.path.join(post_folder, "raw.jpg")
                with open(temp_img, "wb") as f:
                    f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

                # Process Caption
                raw_caption = post.caption or "Breaking News Update"
                lines = [l.strip() for l in raw_caption.split("\n") if l.strip()]
                
                # Logic to grab the main "Body" news line
                body = lines[1] if len(lines) > 1 else lines[0]
                source = next((l.split(":")[-1].strip() for l in lines if "SOURCE" in l.upper()), "The Hindu")

                # Files for this folder
                img_final = os.path.join(post_folder, "post_image.jpg")
                cap_final = os.path.join(post_folder, "post_caption.txt")

                # 1. Create Image
                await generate_card(body, source, temp_img, img_final)

                # 2. Create Caption with Hashtags
                with open(cap_final, "w", encoding="utf-8") as f:
                    f.write(f"{raw_caption}\n\n🏛️ Follow @{IG_HANDLE}\n\n{HASHTAGS}")

                os.remove(temp_img)
                print(f"✅ Post {i} processed successfully.")

        except Exception as e:
            print(f"❌ Batch Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
