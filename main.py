import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_premium_card(headline, brief, bg_path="photo_5986512446270672046_y.jpg"):
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # 1. Load Background Image
    if not os.path.exists(bg_path):
        print(f"Error: {bg_path} not found in the root directory!")
        # Fallback to a solid color if image is missing so the action doesn't crash
        bg = Image.new('RGB', (1080, 1080), color=(20, 20, 20))
    else:
        bg = Image.open(bg_path).convert("RGB")
        # Resize and crop to square 1080x1080
        bg = bg.resize((1080, 1080), Image.Resampling.LANCZOS)

    # 2. Apply professional blur to the bottom area (Bottom 45%)
    # Box: (left, top, right, bottom)
    blur_area = (0, 600, 1080, 1080)
    region = bg.crop(blur_area)
    region = region.filter(ImageFilter.GaussianBlur(radius=20))
    bg.paste(region, blur_area)

    # 3. Add a semi-transparent dark overlay to make text pop
    # (0,0,0,160) is Black with 60% opacity
    overlay = Image.new('RGBA', (1080, 480), (0, 0, 0, 160))
    bg.paste(overlay, (0, 600), overlay)

    draw = ImageDraw.Draw(bg)

    # 4. Load Fonts (Ubuntu Runner Path)
    try:
        font_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
    except:
        font_h = ImageFont.load_default()
        font_b = ImageFont.load_default()

    # 5. Draw Headline (Wrapped)
    y_text = 640
    for line in textwrap.wrap(headline, width=28):
        draw.text((60, y_text), line, font=font_h, fill=(255, 255, 255))
        y_text += 75

    # 6. Draw Brief (Wrapped)
    y_text += 20
    for line in textwrap.wrap(brief, width=52):
        draw.text((60, y_text), line, font=font_b, fill=(220, 220, 220))
        y_text += 45

    # 7. Save to the output folder for GitHub Artifacts
    save_path = "output/ig_news_card.jpg"
    bg.save(save_path, quality=95)
    print(f"Success! Created {save_path} using {bg_path}")

if __name__ == "__main__":
    # Content extracted from your Telegram post (Image 2)
    news_head = "UNITED OPPOSITION DEFEATS CONSTITUTIONAL AMENDMENT"
    news_brief = "The Bill for Women's Quota has been blocked by the United Opposition in a major session. Full story on Telegram."
    
    create_premium_card(news_head, news_brief)
