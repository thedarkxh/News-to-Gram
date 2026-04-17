import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_optimal_font_size(text, font_path, max_width, max_height, initial_size):
    size = initial_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        # Calculate how many characters fit in max_width based on current font size
        # We use a safety factor of 0.5 to 0.6 for Bold Sans fonts
        chars_per_line = int(max_width / (size * 0.55))
        lines = textwrap.wrap(text, width=chars_per_line)
        
        line_height = font.getbbox("HG")[3]
        if (len(lines) * (line_height + 20)) <= max_height:
            return font, size, chars_per_line
        size -= 2
    return ImageFont.load_default(), size, 30

def create_ultimate_card(headline, brief, bg_path="photo_5986512446270672046_y.jpg"):
    os.makedirs("output", exist_ok=True)
    
    # 1. Background Setup
    bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # 2. Stronger Gradient Mask (Start higher for better legibility)
    gradient = Image.new('L', (1, 1080), color=0)
    for y in range(350, 1080):
        level = int(255 * (y - 350) / 400) if y < 750 else 255
        gradient.putpixel((0, y), min(level, 255))
    gradient = gradient.resize((1080, 1080))
    black_layer = Image.new('RGB', (1080, 1080), color=(10, 10, 10))
    bg = Image.composite(black_layer, bg, gradient)

    draw = ImageDraw.Draw(bg)
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # 3. Modern Tag (Moved slightly to avoid the "Division" text)
    draw.rectangle([50, 50, 220, 85], fill=(200, 0, 0))
    tag_font = ImageFont.truetype(bold_path, 22)
    draw.text((72, 55), "LATEST", font=tag_font, fill=(255, 255, 255))

    # 4. Dynamic Sizing with Dynamic Wrap
    # Safety: width is 900 (giving 90px margin on each side)
    header_font, h_size, h_wrap = get_optimal_font_size(headline.upper(), bold_path, 900, 200, 52)
    body_font, b_size, b_wrap = get_optimal_font_size(brief, reg_path, 900, 160, 36)

    # 5. Render Headline
    curr_y = 660 
    for line in textwrap.wrap(headline.upper(), width=h_wrap):
        # Center checking: If you want left-aligned, use 90. 
        draw.text((90, curr_y), line, font=header_font, fill=(255, 255, 255))
        curr_y += h_size + 15

    # 6. Render Body
    curr_y += 30 
    for line in textwrap.wrap(brief, width=b_wrap):
        draw.text((90, curr_y), line, font=body_font, fill=(170, 170, 170))
        curr_y += b_size + 12

    # 7. Fixed Footer (Bottom Right)
    footer_font = ImageFont.truetype(reg_path, 20)
    draw.text((820, 1025), "t.me/tedsxh", font=footer_font, fill=(80, 80, 80))
    draw.rectangle([785, 1035, 810, 1038], fill=(200, 0, 0))

    bg.save("output/ig_news_card.jpg", quality=100)
    print("Fixed layout generated.")

if __name__ == "__main__":
    # Test with the specific long headline that was cutting off
    head = "United Opposition Defeats Constitutional Amendment in Historic Parliamentary Session"
    desc = "The bill for Women's Quota was blocked following an intense parliamentary debate. Read the full analysis on our Telegram channel."
    create_ultimate_card(head, desc)
