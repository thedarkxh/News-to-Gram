import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_optimal_font_size(text, font_path, max_width, max_height, initial_size):
    """Calculates the largest font size that fits within a specific area."""
    size = initial_size
    font = ImageFont.truetype(font_path, size)
    
    # Decrease font size until the wrapped text fits the max_height
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        lines = textwrap.wrap(text, width=int(max_width / (size * 0.5)))
        line_height = font.getbbox("HG")[3] # Get approximate height of a line
        total_height = len(lines) * (line_height + 10)
        
        if total_height <= max_height:
            break
        size -= 2
    return font, size

def create_premium_card(headline, brief, bg_path="photo_5986512446270672046_y.jpg"):
    os.makedirs("output", exist_ok=True)
    
    # 1. Load Background
    if not os.path.exists(bg_path):
        bg = Image.new('RGB', (1080, 1080), color=(20, 20, 20))
    else:
        bg = Image.open(bg_path).convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS)

    # 2. Blur & Overlay Logic
    blur_area = (0, 600, 1080, 1080)
    region = bg.crop(blur_area).filter(ImageFilter.GaussianBlur(radius=25))
    bg.paste(region, blur_area)
    overlay = Image.new('RGBA', (1080, 480), (0, 0, 0, 180))
    bg.paste(overlay, (0, 600), overlay)
    draw = ImageDraw.Draw(bg)

    # 3. Paths to fonts (Standard Ubuntu paths for GitHub Actions)
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    reg_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    # 4. Dynamic Sizing for Headline (Max area: 960x200px)
    header_font, h_size = get_optimal_font_size(headline, bold_path, 960, 200, 70)
    
    # 5. Dynamic Sizing for Paragraph (Max area: 960x180px)
    body_font, b_size = get_optimal_font_size(brief, reg_path, 960, 180, 42)

    # 6. Draw Content
    y_text = 640
    # Wrap text based on the calculated font size
    h_wrap = int(960 / (h_size * 0.55))
    for line in textwrap.wrap(headline, width=h_wrap):
        draw.text((60, y_text), line, font=header_font, fill=(255, 255, 255))
        y_text += h_size + 15

    y_text += 10
    b_wrap = int(960 / (b_size * 0.52))
    for line in textwrap.wrap(brief, width=b_wrap):
        draw.text((60, y_text), line, font=body_font, fill=(210, 210, 210))
        y_text += b_size + 10

    # 7. Save
    save_path = "output/ig_news_card.jpg"
    bg.save(save_path, quality=95)
    print(f"Success! Auto-adjusted card saved to {save_path}")

if __name__ == "__main__":
    # Test with a very long headline to check auto-adjustment
    head = "UNITED OPPOSITION DEFEATS CONSTITUTIONAL AMENDMENT BILL IN A HISTORIC PARLIAMENTARY SESSION"
    desc = "The bill intended for Women's Quota has been successfully blocked after intense debate. This marks a significant turn in the current legislative period."
    
    create_premium_card(head, desc)
