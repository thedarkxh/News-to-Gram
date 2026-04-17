import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_optimal_font_size(text, font_path, max_width, max_height, initial_size):
    size = initial_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        # Using a slightly tighter wrap for a cleaner look
        lines = textwrap.wrap(text, width=int(max_width / (size * 0.52)))
        line_height = font.getbbox("HG")[3]
        if (len(lines) * (line_height + 15)) <= max_height:
            return font, size
        size -= 2
    return ImageFont.load_default(), size

def create_ultimate_card(headline, brief, bg_path="photo_5986512446270672046_y.jpg"):
    os.makedirs("output", exist_ok=True)
    
    # 1. Background Setup
    bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # 2. Stronger Gradient Mask
    # We start the fade higher (y=400) but make the bottom (y=700+) fully black
    gradient = Image.new('L', (1, 1080), color=0)
    for y in range(400, 1080):
        level = int(255 * (y - 400) / 350) if y < 750 else 255
        gradient.putpixel((0, y), min(level, 255))
    gradient = gradient.resize((1080, 1080))

    black_layer = Image.new('RGB', (1080, 1080), color=(10, 10, 10))
    bg = Image.composite(black_layer, bg, gradient)

    draw = ImageDraw.Draw(bg)
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # 3. Modern Breaking Tag
    draw.rectangle([50, 50, 240, 85], fill=(200, 0, 0))
    tag_font = ImageFont.truetype(bold_path, 24)
    draw.text((70, 54), "LATEST", font=tag_font, fill=(255, 255, 255))

    # 4. Refined Sizing (Headlines should be clear but NOT cover the center)
    # Area: 920px wide, max 180px tall
    header_font, h_size = get_optimal_font_size(headline.upper(), bold_path, 920, 180, 48)
    body_font, b_size = get_optimal_font_size(brief, reg_path, 920, 150, 34)

    # 5. Render Text with Manual Padding
    # We move the text lower (starting at y=680) to avoid the center of the image
    curr_y = 680 
    h_wrap = int(920 / (h_size * 0.55))
    for line in textwrap.wrap(headline.upper(), width=h_wrap):
        draw.text((80, curr_y), line, font=header_font, fill=(255, 255, 255))
        curr_y += h_size + 15

    curr_y += 25 # Gap between headline and body
    b_wrap = int(920 / (b_size * 0.52))
    for line in textwrap.wrap(brief, width=b_wrap):
        draw.text((80, curr_y), line, font=body_font, fill=(160, 160, 160))
        curr_y += b_size + 10

    # 6. Fixed Footer (Moved to the very bottom right)
    footer_font = ImageFont.truetype(reg_path, 22)
    draw.text((840, 1020), "t.me/tedsxh", font=footer_font, fill=(70, 70, 70))
    draw.rectangle([800, 1032, 830, 1035], fill=(200, 0, 0))

    bg.save("output/ig_news_card.jpg", quality=100)
    print("Final tuned card generated.")

if __name__ == "__main__":
    head = "United Opposition Defeats Constitutional Amendment in Historic Session"
    desc = "The bill for Women's Quota was blocked following an intense parliamentary debate. Read the full analysis on our Telegram channel."
    create_ultimate_card(head, desc)
