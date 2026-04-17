import os
import asyncio
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from aiogram import Bot

# --- CONFIGURATION ---
BG_TEMP_NAME = "raw_background.jpg"
OUTPUT_NAME = "output/ig_news_card.jpg"

# --- IMAGE GENERATION LOGIC ---
def get_optimal_font_size(text, font_path, max_width, max_height, initial_size):
    size = initial_size
    while size > 18:
        font = ImageFont.truetype(font_path, size)
        chars_per_line = int(max_width / (size * 0.54))
        lines = textwrap.wrap(text, width=chars_per_line)
        line_height = font.getbbox("HG")[3]
        if (len(lines) * (line_height + 15)) <= max_height:
            return font, size, chars_per_line
        size -= 2
    return ImageFont.load_default(), size, 30

def create_premium_card(headline, brief, bg_path):
    os.makedirs("output", exist_ok=True)
    
    if not os.path.exists(bg_path):
        print(f"Error: {bg_path} not found.")
        return None

    # 1. Background Setup
    bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # 2. Advanced Gradient Mask
    gradient = Image.new('L', (1, 1080), color=0)
    for y in range(380, 1080):
        level = int(255 * (y - 380) / 400) if y < 780 else 255
        gradient.putpixel((0, y), min(level, 255))
    gradient = gradient.resize((1080, 1080))
    black_layer = Image.new('RGB', (1080, 1080), color=(10, 10, 10))
    bg = Image.composite(black_layer, bg, gradient)

    draw = ImageDraw.Draw(bg)
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # 3. Text Sizing & Margins
    header_font, h_size, h_wrap = get_optimal_font_size(headline.upper(), bold_path, 900, 200, 50)
    body_font, b_size, b_wrap = get_optimal_font_size(brief, reg_path, 900, 160, 34)

    # 4. Drawing Text
    curr_y = 670
    for line in textwrap.wrap(headline.upper(), width=h_wrap):
        draw.text((90, curr_y), line, font=header_font, fill=(255, 255, 255))
        curr_y += h_size + 15

    curr_y += 25
    for line in textwrap.wrap(brief, width=b_wrap):
        draw.text((90, curr_y), line, font=body_font, fill=(170, 170, 170))
        curr_y += b_size + 10

    # 5. Branding Footer
    footer_font = ImageFont.truetype(reg_path, 20)
    draw.text((820, 1030), "t.me/tedsxh", font=footer_font, fill=(85, 85, 85))
    draw.rectangle([785, 1040, 810, 1043], fill=(200, 0, 0))

    bg.save(OUTPUT_NAME, quality=100)
    return OUTPUT_NAME

# --- TELEGRAM SYNC LOGIC ---
async def fetch_latest_photo(bot, chat_id):
    """Downloads the most recent image sent to the channel to use as background."""
    print("Connecting to Telegram to fetch background...")
    try:
        chat = await bot.get_chat(chat_id)
        # We fetch the latest message. Note: Bot must be Admin.
        # This approach assumes the latest message contains the photo you want to 'fix'
        updates = await bot.get_updates(limit=1, offset=-1)
        
        # Fallback: In GitHub Actions, we often use the repo file if no new update is found
        if not updates:
            print("No recent updates found, using repository fallback.")
            return "photo_5986512446270672046_y.jpg"

        # Logic to download photo from the last update
        # For simplicity in this workflow, we prioritize the file you provide via GitHub
        return "photo_5986512446270672046_y.jpg"
    except Exception as e:
        print(f"Fetch failed: {e}")
        return "photo_5986512446270672046_y.jpg"

async def sync_to_telegram(photo_path, headline, brief):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    bot = Bot(token=token)
    
    caption = f"<b>{headline.upper()}</b>\n\n{brief}\n\n📢 <i>Stay updated at t.me/tedsxh</i>"
    
    try:
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, parse_mode="HTML")
        print("Success: Post synced to Telegram.")
    except Exception as e:
        print(f"Sync failed: {e}")
    finally:
        await bot.session.close()

# --- MAIN EXECUTION ---
async def main():
    # 1. Content Definition (This can be pulled from an API later)
    headline = "United Opposition Defeats Constitutional Amendment"
    brief = "The bill for Women's Quota was blocked following an intense parliamentary debate. Full story on our Telegram channel."

    # 2. Get Background
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    bot = Bot(token=token)
    
    bg_file = await fetch_latest_photo(bot, chat_id)
    await bot.session.close()

    # 3. Create Card
    print(f"Processing image with background: {bg_file}")
    final_path = create_premium_card(headline, brief, bg_file)

    # 4. Sync Back to Channel
    if final_path:
        await sync_to_telegram(final_path, headline, brief)

if __name__ == "__main__":
    asyncio.run(main())
