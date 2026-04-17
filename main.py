import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_card(headline, brief, filename):
    # Setup directory
    os.makedirs("output", exist_ok=True)
    
    # 1080x1080 is the IG standard
    img = Image.new('RGB', (1080, 1080), color=(15, 15, 15))
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font logic for GitHub Ubuntu Runners
    try:
        # Ubuntu runners usually have DejaVuSans
        font_head = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_head = ImageFont.load_default()
        font_body = ImageFont.load_default()

    # Draw headline (wrapped)
    y_offset = 200
    for line in textwrap.wrap(headline, width=20):
        draw.text((100, y_offset), line, font=font_head, fill=(255, 255, 255))
        y_offset += 80

    # Draw brief (wrapped)
    y_offset += 60
    for line in textwrap.wrap(brief, width=45):
        draw.text((100, y_offset), line, font=font_body, fill=(200, 200, 200))
        y_offset += 50

    # Save locally
    save_path = f"output/{filename}"
    img.save(save_path)
    print(f"Successfully saved {save_path}")

if __name__ == "__main__":
    # Test Data
    test_headline = "GitHub Action Test"
    test_brief = "This image was generated within a GitHub Ubuntu runner and saved as an artifact for local review."
    
    create_card(test_headline, test_brief, "test_news_card.jpg")
