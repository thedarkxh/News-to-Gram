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
        if (len(lines) * (line_height + 20)) <= max_height:
            return font, size
        size -= 2
    return ImageFont.load_default(), size

def create_ultimate_card(headline, brief, bg_path="photo_5986512446270672046_y.jpg"):
    os.makedirs("output", exist_ok=True)
    
    # 1. Background Setup
    bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)
    
    # 2. Smooth Gradient Mask (Refined for a more subtle transition)
    gradient = Image.new('L', (1, 1080), color=0)
    for y in range(500, 1080):
        level = int(255 * (y - 500) / 400) if y < 900 else 255
        gradient.putpixel((0, y), min(level, 255))
    gradient = gradient.resize((1080, 1080))

    black_layer = Image.new('RGB', (1080, 1080), color=(12, 12, 12))
    bg = Image.composite(black_layer, bg, gradient)

    draw = ImageDraw.Draw(bg)
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # 3. Refined Breaking Tag (Thinner, more modern)
    draw.rectangle([40, 45, 280, 85], fill=(220, 0, 0))
    tag_font = ImageFont.truetype(bold_path, 28)
    draw.text((65, 50), "BREAKING", font=tag_font, fill=(255, 255, 255))

    # 4. Dynamic Sizing (Reduced max_height for Headline to keep it smaller)
    # We lowered initial_size to 55 and max_height to 200 for a tighter header
    header_font, h_size = get_optimal_font_size(headline.upper(), bold_path, 940, 200, 55)
    body_font, b_size = get_optimal_font_size(brief, reg_path, 940, 180, 36)

    # 5. Render Text with Premium Spacing
    curr_y = 660 # Lowered starting point slightly
    h_wrap_width = int(940 / (h_size * 0.55))
    for line in textwrap.wrap(headline.upper(), width=h_wrap_width):
        draw.text((60, curr_y), line, font=header_font, fill=(255, 255, 255))
        curr_y += h_size + 18 # Balanced leading

    curr_y += 20
    b_wrap_width = int(940 / (b_size * 0.52))
    for line in textwrap.wrap(brief, width=b_wrap_width):
        draw.text((60, curr_y), line, font=body_font, fill=(170, 170, 170))
        curr_y += b_size + 12

    # 6. Minimal Footer Branding
    footer_font = ImageFont.truetype(reg_path, 22)
    draw.rectangle([60, 1015, 120, 1018], fill=(220, 0, 0))
    draw.text((135, 1003), "t.me/tedsxh", font=footer_font, fill=(90, 90, 90))

    bg.save("output/ig_news_card.jpg", quality=100, subsampling=0)
    print("Final polished card generated.")

if __name__ == "__main__":
    head = "United Opposition Defeats Constitutional Amendment in Historic Session"
    desc = "The bill for Women's Quota was blocked following an intense parliamentary debate. Read the full analysis on our Telegram channel."
    create_ultimate_card(head, desc)
