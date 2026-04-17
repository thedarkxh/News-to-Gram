import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_premium_card(headline, brief, bg_path="background.jpg"):
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # 1. Load Background Image
    if not os.path.exists(bg_path):
        # Fallback if you haven't uploaded the image yet
        print(f"Warning: {bg_path} not found. Creating dark background.")
        bg = Image.new('RGB', (1080, 1080), color=(20, 20, 20))
    else:
        bg = Image.open(bg_path).convert("RGB")
        bg = bg.resize((1080, 1080), Image.Resampling.LANCZOS)

    # 2. Apply Blur to the bottom area (where text will be)
    # Define the box: (left, top, right, bottom)
    blur_area = (0, 600, 1080, 1080)
    region = bg.crop(blur_area)
    region = region.filter(ImageFilter.GaussianBlur(radius=15))
    bg.paste(region, blur_area)

    # 3. Add a semi-transparent dark overlay to the blurred area
    overlay = Image.new('RGBA', (1080, 480), (0, 0, 0, 160))
    bg.paste(overlay, (0, 600), overlay)

    draw = ImageDraw.Draw(bg)

    # 4. Fonts
    try:
        font_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_h = ImageFont.load_default()
        font_b = ImageFont.load_default()

    # 5. Draw Content
    y_text = 640
    for line in textwrap.wrap(headline, width=28):
        draw.text((60, y_text), line, font=font_h, fill=(255, 255, 255))
        y_text += 80

    y_text += 20
    for line in textwrap.wrap(brief, width=55):
        draw.text((60, y_text), line, font=font_b, fill=(210, 210, 210))
        y_text += 50

    # 6. Save
    save_path = "output/ig_post.jpg"
    bg.save(save_path, quality=95)
    print(f"Success! Image saved to {save_path}")

if __name__ == "__main__":
    # Test Data from your Image 2
    head = "Opposition Defeats Quota Bill"
    desc = "The United Opposition has successfully blocked the Constitutional Amendment Bill for Women's Quota. Full story on Telegram."
    
    create_premium_card(head, desc)
