import os
import asyncio
import textwrap
import requests
import random
from aiogram import Bot
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# Config pulled from Secrets
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group"
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #genz #trending #india"

# --- GEN Z COLOR SCHEMES ---
# Define vibrant, gradient pairs (Background, Text Color, Accent Line Color)
GEN_Z_PALETTES = [
    {"name": "Neon Ocean", "bg": ((0, 10, 30), (0, 100, 180)), "text": (255, 255, 255), "accent": (0, 255, 255)}, # Dark Blue to Aqua
    {"name": "Synthwave", "bg": ((20, 0, 40), (120, 0, 180)), "text": (255, 255, 255), "accent": (255, 100, 255)}, # Deep Purple to Violet
    {"name": "Matcha Latte", "bg": ((10, 30, 10), (80, 160, 80)), "text": (255, 255, 255), "accent": (200, 255, 200)}, # Forest Green to Lime
    {"name": "Cyberpunk Sunset", "bg": ((40, 10, 0), (180, 10, 0)), "text": (255, 255, 255), "accent": (255, 200, 0)}, # Burnt Orange to Red
    {"name": "Cloud Violet", "bg": ((30, 20, 50), (160, 120, 220)), "text": (255, 255, 255), "accent": (255, 255, 255)} # Dark Lavender to Soft Violet
]

def create_gen_z_background(width, height):
    """Generates a random gradient background."""
    palette = random.choice(GEN_Z_PALETTES)
    print(f"🎨 Selected Palette: {palette['name']}")
    
    # Create the gradient (requests vertical gradient: 0, 0, 0, height)
    base = Image.new('RGB', (width, height), color=palette["bg"][0])
    draw = ImageDraw.Draw(base, 'RGBA')
    
    c1 = palette["bg"][0]
    c2 = palette["bg"][1]
    
    # Draw simple vertical gradient lines
    for y in range(height):
        r = int(c1[0] + (c2[0] - c1[0]) * y / height)
        g = int(c1[1] + (c2[1] - c1[1]) * y / height)
        b = int(c1[2] + (c2[2] - c1[2]) * y / height)
        draw.line((0, y, width, y), fill=(r, g, b))
        
    return base, palette

async def generate_premium_card(headline, news_brief, source_line, tg_image_path):
    print("🎨 Generating Gen Z branded card...")
    # 1. Generate Random Gradient Background
    width, height = 1080, 1080
    img, palette = create_gen_z_background(width, height)
    draw = ImageDraw.Draw(img, 'RGBA')
    text_color = palette["text"]
    accent_color = palette["accent"]

    # 2. Add Red Header Bar (15% height) - Keep brand color
    draw.rectangle([0, 0, 1080, 150], fill=(211, 47, 47))

    # 3. Load Project Fonts (Fallback to standard on missing)
    try:
        font_latest = ImageFont.truetype("Anton-Regular.ttf", 65)
        font_h = ImageFont.truetype("Poppins-SemiBold.ttf", 60)
        font_b = ImageFont.truetype("Poppins-SemiBold.ttf", 35) # Same for main body
        font_s = ImageFont.truetype("Poppins-Regular.ttf", 30) # For source line
    except:
        font_p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_latest = ImageFont.truetype(font_p, 65)
        font_h = ImageFont.truetype(font_p, 60)
        font_b = ImageFont.truetype(font_p, 35)
        font_s = ImageFont.truetype(font_p.replace("-Bold",""), 30)

    # 4. Draw Header Text
    w_latest = draw.textlength("LATEST", font=font_latest)
    # X, Y coordinates, centered in header
    draw.text(((1080 - w_latest) / 2, 45), "LATEST", font=font_latest, fill=(255, 255, 255))

    # 5. Place and Center the original Telegram photo
    bg = Image.open(tg_image_path).convert("RGB")
    r_w, r_h = bg.size
    target_w = 1080
    target_h = int(r_h * (target_w / r_w))
    resized_bg = bg.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Define vertical center of middle area
    middle_y_center = (150 + 680) / 2 
    img.paste(resized_bg, (0, int(middle_y_center - (target_h / 2))))

    # 6. Separator line between image and text footer
    draw.line((50, 680, 1030, 680), fill=accent_color, width=4)

    # 7. Draw Headline (Bold, CAPS, centered)
    # Start text from a better margin
    curr_y = 720
    # Wraps by character count. Montserrat can handle ~28 characters per line
    w_h = 28 
    headline_lines = textwrap.wrap(headline.upper(), width=w_h)
    
    for line in headline_lines:
        # draw.textlength is precise, we use it to calculate true center
        w_line = draw.textlength(line, font=font_h)
        # Margin: left margin is (Canvas - TextWidth) / 2
        draw.text(((1080 - w_line) / 2, curr_y), line, font=font_h, fill=text_color)
        curr_y += 75
        
    # 8. Draw Brief (News Body)
    curr_y += 20
    # Wraps by character count. SemiBold can handle ~60 characters per line
    w_b = 60 
    body_lines = textwrap.wrap(news_brief, width=w_b)
    for line in body_lines:
        w_line = draw.textlength(line, font=font_b)
        draw.text(((1080 - w_line) / 2, curr_y), line, font=font_b, fill=(210, 210, 210))
        curr_y += 45
        
    # 9. Draw Source Line (NEW line, smaller font, centered)
    curr_y += 30
    if source_line:
        w_s = draw.textlength(source_line, font=font_s)
        # Place centered at bottom, above hashtags margin
        draw.text(((1080 - w_s) / 2, 1010), source_line, font=font_s, fill=(180, 180, 180))

    img.save("post_image.jpg", quality=95)
    print("✅ All assets ready.")

async def main():
    if not TOKEN or not CHANNEL_ID:
        print("❌ ERROR: Missing secrets.")
        return

    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            target_msg = next((u.channel_post for u in reversed(updates) if u.channel_post and u.photo), None)
            
            if not target_msg:
                print("❌ No recent news card found.")
                return

            # Download Media
            file = await bot.get_file(target_msg.photo[-1].file_id)
            tg_img_path = "tg_original.jpg"
            with open(tg_img_path, "wb") as f:
                f.write(requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content)

            # Process Caption Text
            raw_text = target_msg.caption or ""
            lines = [l for l in raw_text.split('\n') if l.strip()]
            
            # 1. Extract Headline and Brief (First sentence) for IMAGE
            headline = lines[0] if lines else "NEWS UPDATE"
            # Get the raw brief (all body text)
            raw_brief = " ".join(lines[1:])
            # Extract first sentence for the *image text only* (keep it brief on the graphic)
            brief_sentence = raw_brief.split('.')[0] + '.' if '.' in raw_brief else raw_brief[:120]
            
            # 2. Extract and Isolate the SOURCE line
            # It usually starts with "Source:" or has it in the middle. We'll find it.
            source_line = next((l for l in lines if "SOURCE:" in l.upper()), None)
            
            # 3. Generate the Dynamic Branded Image
            await generate_premium_card(headline, brief_sentence, source_line, tg_img_path)

            # 4. Process Caption for IG (unchanged: scrubs junk, keeps source, adds CTA)
            # Remove "Full Story", "Related", "Join" etc. but keep "Source"
            clean_lines = [l for l in lines if not any(w in l.upper() for w in ["READ FULL STORY", "RELATED:", "JOIN"])]
            news_content = "\n".join(clean_lines).strip()
            new_cta = f"🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
            
            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(f"{news_content}\n\n{new_cta}\n\n{HASHTAGS}")

        except Exception as e:
            print(f"❌ Execution Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
