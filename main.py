import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

def create_premium_card(headline, brief, filename="ig_post.jpg"):
    # 1. CRITICAL: Create the output directory explicitly
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # 2. Create the Canvas (Instagram Square)
    width, height = 1080, 1080
    # Using a deep dark gradient-like color for a premium feel
    bg_color = (15, 15, 15) 
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 3. Font Loading Logic for GitHub Ubuntu Runners
    # Ubuntu runners have DejaVuSans installed by default
    try:
        font_h = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
        print("Loaded DejaVu fonts.")
    except:
        font_h = ImageFont.load_default()
        font_b = ImageFont.load_default()
        print("Warning: Using default fonts. Image may look plain.")

    # 4. Draw Accent Element (Left vertical bar)
    draw.rectangle([40, 150, 55, 400], fill=(0, 120, 255)) # Tech Blue accent

    # 5. Draw Headline
    y_text = 150
    header_lines = textwrap.wrap(headline, width=20)
    for line in header_lines:
        draw.text((80, y_text), line, font=font_h, fill=(255, 255, 255))
        y_text += 90

    # 6. Draw Brief
    y_text += 60
    body_lines = textwrap.wrap(brief, width=40)
    for line in body_lines:
        draw.text((80, y_text), line, font=font_b, fill=(200, 200, 200))
        y_text += 60

    # 7. Final Save
    save_path = os.path.join(output_dir, filename)
    img.save(save_path, quality=95)
    print(f"Successfully saved image to: {save_path}")
    
    # List files to verify for GitHub logs
    print("Current output directory contents:", os.listdir(output_dir))

if __name__ == "__main__":
    # Test Content
    sample_head = "GitHub Actions Fix"
    sample_brief = "The output directory is now explicitly created and verified. Your artifact will appear in the Summary tab."
    
    create_premium_card(sample_head, sample_brief)
