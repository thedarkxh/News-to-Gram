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
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #india #trending"

# High-contrast Gen Z Palettes (Bottom Gradient, Accent Line)
VIBE_PALETTES = [
    {"grad": (0, 255, 127), "line": (0, 255, 127)},   # Spring Green
    {"grad": (255, 20, 147), "line": (255, 20, 147)}, # Deep Pink
    {"grad": (0, 191, 255), "line": (0, 191, 255)},  # Deep Sky Blue
    {"grad": (255, 165, 0), "line": (255, 165, 0)},   # Vivid Orange
    {"grad": (138, 43, 226), "line": (138, 43, 226)}  # Blue Violet
]

async def generate_premium_card(headline, source, img_path):
    palette = random.choice(VIBE_PALETTES)
    # Start with a solid black canvas
    canvas = Image.new('RGB', (1080, 1080), color=(10, 10, 10))
    draw = ImageDraw.Draw(canvas)

    # 1. Header (Fixed Red)
    draw.rectangle([0, 0, 1080, 140], fill=(211, 47, 47))
    
    # 2. Dynamic Text Margins & Wrapping
    try:
        f_top = ImageFont.truetype("Anton-Regular.ttf", 75)
        f_head = ImageFont.truetype("Poppins-SemiBold.ttf", 52)
        f_sub = ImageFont.truetype("Poppins-Regular.ttf", 32)
    except:
        f_top = f_head = f_sub = ImageFont.load_default()

    draw.text((540, 70), "LATEST", font=f_top, fill="white", anchor="mm")

    # 3. Handle Main Photo (Resize to fit the middle section)
    photo = Image.open(img_path).convert("RGB")
    # Resize photo to fit width while keeping aspect ratio
    p_w, p_h = photo.size
    ratio = 1080 / p_w
    photo = photo.resize((1080, int(p_h * ratio)), Image.Resampling.LANCZOS)
    
    # Paste photo right under the header
    canvas.paste(photo, (0, 140))

    # 4. The Footer (This is where the colors and text go)
    # We calculate the footer height based on the text
    head_upper = headline.upper().strip()
    wrapped_head = textwrap.wrap(head_upper, width=24) # Narrower width to prevent border crossing
    
    # Draw the gradient from the bottom up
    for i in range(450):
        alpha = i / 450
        # Blend black with the chosen vibe color
        r = int(10 * (1 - alpha) + palette["grad"][0] * (alpha * 0.3))
        g = int(10 * (1 - alpha) + palette["grad"][1] * (alpha * 0.3))
        b = int(10 * (1 - alpha) + palette["grad"][2] * (alpha * 0.3))
        draw.line((0, 1080-i, 1080, 1080-i), fill=(r, g, b))

    # 5. Accent Line & Text Placement
    footer_top = 700 
    draw.rectangle([0, footer_top, 1080, footer_top + 8], fill=palette["line"])
    
    # Draw Headline
    current_y = footer_top + 60
    for line in wrapped_head:
        draw.text((540, current_y), line, font=f_head, fill="white", anchor="mm")
        current_y += 70

    # Draw Source at the very bottom
    if source:
        clean_source = source.replace("🔗", "").replace("Source:", "").strip()
        draw.text((540, 1020), f"SOURCE: {clean_source.upper()}", font=f_sub, fill=(200, 200, 200), anchor="mm")

    canvas.save("post_image.jpg", quality=95)

async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            target = next((u.channel_post for u in reversed(updates) if u.channel_post and u.photo), None)
            
            if not target:
                print("No post found")
                return

            # Download
            file = await bot.get_file(target.photo[-1].file_id)
            img_data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content
            with open("temp.jpg", "wb") as f:
                f.write(img_data)

            # Text Processing
            caption = target.caption or ""
            lines = [l.strip() for l in caption.split('\n') if l.strip()]
            
            headline = lines[0]
            # Identify the Source line
            source_line = next((l for l in lines if "SOURCE" in l.upper()), "")

            # Generate the Card
            await generate_premium_card(headline, source_line, "temp.jpg")

            # IG Caption Filtering
            # Removes "Full Story", "Related", etc but keeps everything else
            junk_keywords = ["READ FULL STORY", "RELATED:", "JOIN"]
            clean_caption_lines = [l for l in lines if not any(k in l.upper() for k in junk_keywords)]
            
            final_caption = "\n".join(clean_caption_lines)
            final_caption += f"\n\n🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗\n\n{HASHTAGS}"

            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(final_caption)

            print("✅ Success: post_image.jpg and post_caption.txt created.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
