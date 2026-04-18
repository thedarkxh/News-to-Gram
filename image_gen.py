import os
import asyncio
import textwrap
import requests
import random
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# Config
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group"
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #genz #trending #india"

# Modern vibrant palettes
PALETTES = [
    {"bg": (20, 20, 20), "accent": (0, 255, 150), "grad": (40, 80, 70)},  # Cyber Green
    {"bg": (15, 10, 25), "accent": (255, 0, 150), "grad": (80, 40, 90)},  # Synth Pink
    {"bg": (10, 20, 30), "accent": (0, 200, 255), "grad": (30, 60, 100)}, # Electric Blue
    {"bg": (25, 15, 10), "accent": (255, 100, 0), "grad": (100, 50, 30)}, # Nuclear Orange
]

async def generate_premium_card(headline, brief, source, img_path):
    palette = random.choice(PALETTES)
    img = Image.new('RGB', (1080, 1080), color=palette["bg"])
    draw = ImageDraw.Draw(img)

    # 1. Background Gradient (Bottom Up)
    for i in range(400):
        alpha = i / 400
        r = int(palette["bg"][0] * (1 - alpha) + palette["grad"][0] * alpha)
        g = int(palette["bg"][1] * (1 - alpha) + palette["grad"][1] * alpha)
        b = int(palette["bg"][2] * (1 - alpha) + palette["grad"][2] * alpha)
        draw.line((0, 1080-i, 1080, 1080-i), fill=(r, g, b))

    # 2. Header
    draw.rectangle([0, 0, 1080, 140], fill=(211, 47, 47))
    try:
        f_top = ImageFont.truetype("Anton-Regular.ttf", 70)
        f_head = ImageFont.truetype("Poppins-SemiBold.ttf", 55)
        f_sub = ImageFont.truetype("Poppins-Regular.ttf", 35)
    except:
        f_top = f_head = ImageFont.load_default()
        f_sub = ImageFont.load_default()

    draw.text((540, 70), "LATEST", font=f_top, fill="white", anchor="mm")

    # 3. Main Photo (Dynamic Sizing)
    photo = Image.open(img_path).convert("RGB")
    aspect = photo.height / photo.width
    photo = photo.resize((1080, int(1080 * aspect)), Image.Resampling.LANCZOS)
    
    # We paste the photo but leave room for the text at the bottom
    img.paste(photo, (0, 140))

    # 4. Content Area (Fixed footer height to prevent overflow)
    footer_start = 720
    draw.rectangle([0, footer_start, 1080, 1080], fill=palette["bg"])
    draw.rectangle([0, footer_start, 1080, footer_start+5], fill=palette["accent"])

    # Wrap Headline - width adjusted to prevent border crossing
    lines = textwrap.wrap(headline.upper(), width=25)
    y = footer_start + 50
    for line in lines:
        draw.text((540, y), line, font=f_head, fill="white", anchor="mm")
        y += 70

    # Source on a new line at the very bottom
    if source:
        draw.text((540, 1020), source.strip(), font=f_sub, fill=(180, 180, 180), anchor="mm")

    img.save("post_image.jpg")

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            target = next((u.channel_post for u in reversed(updates) if u.channel_post and u.photo), None)
            if not target: return

            file = await bot.get_file(target.photo[-1].file_id)
            with open("temp.jpg", "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            lines = [l.strip() for l in (target.caption or "").split('\n') if l.strip()]
            headline = lines[0]
            source = next((l for l in lines if "SOURCE" in l.upper()), "")
            
            # Remove "Full Story" and "Related" junk
            clean_lines = [l for l in lines if not any(x in l.upper() for x in ["READ FULL STORY", "RELATED:", "JOIN"])]
            
            await generate_premium_card(headline, "", source, "temp.jpg")
            
            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(clean_lines) + f"\n\n🔗 Link in Bio @{IG_HANDLE}\n\n{HASHTAGS}")

        except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
