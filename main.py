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

# Standard paths for Linux/GitHub Actions
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_fitted_font(text, max_w, max_h, font_path, start_size):
    """Shrinks font size until the text fits the designated frame."""
    size = start_size
    draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        # Calculate wrap based on current font size
        char_w = font.getbbox("A")[2] - font.getbbox("A")[0]
        wrap_chars = max(1, int(max_w / char_w))
        lines = textwrap.wrap(text, width=wrap_chars)
        
        line_h = font.getbbox("HG")[3] - font.getbbox("HG")[1]
        total_h = len(lines) * (line_h + 10)
        
        if total_h <= max_h:
            return font, lines, line_h
        size -= 2
    return ImageFont.load_default(), [text], 20

async def generate_framed_card(body_text, source_name, photo_path):
    W, H = 1080, 1080
    bg = Image.open(photo_path).convert("RGB")
    
    # 1. Square Crop
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio), int(bg.height*ratio)), Image.LANCZOS)
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width+W)//2, (bg.height+H)//2))

    # 2. Dark Gradient (Bottom 50%)
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(500, H):
        alpha = int(240 * ((y - 500) / 580) ** 1.2)
        draw_ov.line([(0, y), (W, y)], fill=(0, 0, 0, min(alpha, 255)))
    bg.paste(overlay, (0, 0), overlay)

    draw = ImageDraw.Draw(bg)
    margin = 80 # Generous margin to keep text "In Frame"

    # 3. Branding Tag
    draw.rectangle([margin, 60, margin + 180, 110], fill=(211, 47, 47))
    draw.text((margin + 90, 85), "LATEST", font=ImageFont.truetype(FONT_BOLD, 28), fill="white", anchor="mm")

    # 4. BREAKING NEWS Sub-header
    draw.rectangle([margin, 650, margin + 6, 695], fill=(211, 47, 47))
    draw.text((margin + 20, 655), "BREAKING NEWS", font=ImageFont.truetype(FONT_BOLD, 36), fill="white")

    # 5. DYNAMIC BODY TEXT (The "Suited" size)
    # We define a "Safe Frame": 920px wide, 250px high
    clean_body = body_text.encode('ascii', 'ignore').decode('ascii').strip().upper()
    b_font, b_lines, line_h = get_fitted_font(clean_body, W - (margin * 2), 250, FONT_BOLD, 68)
    
    y_cursor = 720
    for line in b_lines:
        # Subtle stroke for readability
        for off in [(-1,-1), (1,-1), (-1,1), (1,1)]:
            draw.text((margin + off[0], y_cursor + off[1]), line, font=b_font, fill="black")
        draw.text((margin, y_cursor), line, font=b_font, fill="white")
        y_cursor += line_h + 12

    # 6. Source
    if source_name:
        s_font = ImageFont.truetype(FONT_REG, 28)
        draw.text((margin, H - 80), f"SOURCE: {source_name.upper()}", fill=(180, 180, 180), font=s_font)

    bg.save(IMG_PATH, quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            post = next((u.channel_post for u in reversed(updates) if u.channel_post and u.channel_post.photo), None)
            
            if not post: return

            # Download photo
            file = await bot.get_file(post.photo[-1].file_id)
            with open(TEMP_PATH, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Process Text
            raw_caption = post.caption or ""
            lines = [l.strip() for l in raw_caption.split("\n") if l.strip()]
            
            # The "Body" is usually everything after the first line (Headline)
            # Or if it's short, just use the main highlight line
            body = lines[1] if len(lines) > 1 else lines[0]
            source = next((l.split(":")[-1].strip() for l in lines if "SOURCE" in l.upper()), "Various")

            # 1. GENERATE THE .TXT CAPTION (With Hashtags)
            full_caption = f"{raw_caption}\n\n🏛️ Follow @{IG_HANDLE} for more.\n\n{HASHTAGS}"
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(full_caption)

            # 2. GENERATE THE IMAGE (Body part only)
            await generate_framed_card(body, source, TEMP_PATH)
            
            print("✅ Card framed & Caption file created with hashtags.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
