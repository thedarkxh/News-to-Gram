import os
import textwrap
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from aiogram import Bot

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_USERNAME = "@tedsxh"

async def generate_premium_card(headline, brief, tg_image_path):
    # 1. Open and resize background
    bg = Image.open(tg_image_path).convert("RGB")
    bg = bg.resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # 2. Create a Blurred Area for Text (Bottom 40%)
    blur_box = (0, 600, 1080, 1080)
    region = bg.crop(blur_box)
    region = region.filter(ImageFilter.GaussianBlur(radius=20))
    bg.paste(region, blur_box)
    
    # 3. Add Dark Overlay for contrast
    draw = ImageDraw.Draw(bg, 'RGBA')
    draw.rectangle(blur_box, fill=(0, 0, 0, 100)) # Semi-transparent black
    
    # 4. Draw Content
    try:
        font_h = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
        font_b = ImageFont.truetype("DejaVuSans.ttf", 35)
    except:
        font_h = ImageFont.load_default()
        font_b = ImageFont.load_default()

    # Draw Headline
    curr_h = 650
    for line in textwrap.wrap(headline, width=25):
        draw.text((60, curr_h), line, font=font_h, fill=(255, 255, 255))
        curr_h += 75
        
    # Draw Brief
    curr_h += 20
    for line in textwrap.wrap(brief, width=50):
        draw.text((60, curr_h), line, font=font_b, fill=(220, 220, 220))
        curr_h += 45

    bg.save("output/ig_post.jpg")
    return "output/ig_post.jpg"

async def fetch_latest_news():
    bot = Bot(token=TELEGRAM_TOKEN)
    # Get the last message from the channel
    chat = await bot.get_chat(CHANNEL_USERNAME)
    # Note: Fetching the actual last message requires a listener or specific ID
    # For testing, we assume you have the message ID from your bot logic
    msg_id = 123 
    tg_link = f"https://t.me/{CHANNEL_USERNAME.replace('@','')}/{msg_id}"
    
    # Placeholder for Gemini logic
    headline = "Opposition Defeats Quota Bill"
    brief = "The United Opposition has successfully blocked the Constitutional Amendment for Women's Quota in a major legislative shift."
    
    return headline, brief, tg_link
