import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_optimal_font_size(text, font_path, max_width, max_height, initial_size):
    size = initial_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
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
    
    # 2. Create the Gradient Fade (The "Secret Sauce")
    # This creates a smooth transition from transparent to dark black
    gradient = Image.new('L', (1, 1080), color=0)
    for y in range(550, 1080):
        # Gradual increase in darkness from y=550 to y=850
        level = int(255 * (y - 550) / 300) if y < 850 else 255
        gradient.putpixel((0, y), min(level, 255))
    gradient = gradient.resize((1080, 1080))

    black_layer = Image.new('RGB', (1080, 1080), color=(10, 10, 10))
    bg = Image.composite(black_layer, bg, gradient)

    draw = ImageDraw.Draw(bg)
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # 3. Add Branding Tag (Top Left)
    draw.rectangle([40, 40, 320, 90], fill=(255, 0, 0)) # Red "BREAKING" box
    tag_font = ImageFont.truetype(bold_path, 30)
    draw.text((60, 48), "BREAKING", font=tag_font, fill=(255, 255, 255))

    # 4. Dynamic Headlines & Body
    header_font, h_size = get_optimal_font_size(headline.upper(), bold_path, 960, 250, 65)
    body_font, b_size = get_optimal_font_size(brief, reg_path, 960, 200, 38)

    # 5. Render Text with better Spacing
    curr_y = 650
    for line in textwrap.wrap(headline.upper(), width=int(960 / (h_size * 0.55))):
        draw.text((60, curr_y), line, font=header_font, fill=(255, 255, 255))
        curr_y += h_size + 20

    curr_y += 15
    for line in textwrap.wrap(brief, width=int(960 / (b_size * 0.52))):
        draw.text((60, curr_y), line, font=body_font, fill=(180, 180, 180))
        curr_y += b_size + 12

    # 6. Final Accent Line (Bottom)
    draw.rectangle([60, 1020, 160, 1025], fill=(255, 0, 0))
    draw.text((180, 1008), "t.me/tedsxh", font=ImageFont.truetype(reg_path, 24), fill=(100, 100, 100))

    bg.save("output/ig_news_card.jpg", quality=100, subsampling=0)
    print("Ultimate card generated successfully.")

if __name__ == "__main__":
    head = "United Opposition Defeats Constitutional Amendment in Historic Session"
    desc = "The bill for Women's Quota was blocked following an intense parliamentary debate. Read the full analysis on our Telegram channel."
    create_ultimate_card(head, desc)
