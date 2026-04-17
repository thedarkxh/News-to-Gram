import os
import asyncio
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from aiogram import Bot

# --- IMAGE GENERATION LOGIC ---
def get_optimal_font_size(text, font_path, max_width, max_height, initial_size):
    size = initial_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        chars_per_line = int(max_width / (size * 0.55))
        lines = textwrap.wrap(text, width=chars_per_line)
        line_height = font.getbbox("HG")[3]
        if (len(lines) * (line_height + 15)) <= max_height:
            return font, size, chars_per_line
        size -= 2
    return ImageFont.load_default(), size, 30

def create_card(headline, brief, bg_path="photo_5986512446270672046_y.jpg"):
    os.makedirs("output", exist_ok=True)
    bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # Gradient Mask
    gradient = Image.new('L', (1, 1080), color=0)
    for y in range(350, 1080):
        level = int(255 * (y - 350) / 400) if y < 750 else 255
        gradient.putpixel((0, y), min(level, 255))
    gradient = gradient.resize((1080, 1080))
    bg = Image.composite(Image.new('RGB', (1080, 1080), color=(10, 10, 10)), bg, gradient)

    draw = ImageDraw.Draw(bg)
    bold_p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_p = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # Headline & Body
    h_font, h_size, h_wrap = get_optimal_font_size(headline.upper(), bold_p, 900, 200, 52)
    b_font, b_size, b_wrap = get_optimal_font_size(brief, reg_p, 900, 160, 36)

    curr_y = 660
    for line in textwrap.wrap(headline.upper(), width=h_wrap):
        draw.text((90, curr_y), line, font=h_font, fill=(255, 255, 255))
        curr_y += h_size + 15
    
    curr_y += 30
    for line in textwrap.wrap(brief, width=b_wrap):
        draw.text((90, curr_y), line, font=b_font, fill=(170, 170, 170))
        curr_y += b_size + 12

    save_path = "output/ig_news_card.jpg"
    bg.save(save_path, quality=100)
    return save_path

# --- TELEGRAM SYNC LOGIC ---
async def send_to_telegram(photo_path, caption):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Missing Telegram credentials. Skipping upload.")
        return

    bot = Bot(token=token)
    try:
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, parse_mode="HTML")
        print("Successfully posted to Telegram!")
    except Exception as e:
        print(f"Failed to post: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    head = "United Opposition Defeats Constitutional Amendment"
    desc = "The bill for Women's Quota was blocked following an intense parliamentary debate. Check the full report."
    
    # 1. Generate the image
    img_path = create_card(head, desc)
    
    # 2. Upload to Telegram
    asyncio.run(send_to_telegram(img_path, f"<b>{head}</b>\n\n{desc}"))
