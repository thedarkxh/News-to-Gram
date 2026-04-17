from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_news_card(headline, brief, output_path="post.jpg"):
    # Create a 1080x1080 square (Instagram standard)
    width, height = 1080, 1080
    background_color = (18, 18, 18)  # Dark theme
    accent_color = (255, 215, 0)     # Gold/Yellow accent
    
    img = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts (Ensure you have .ttf files in your project folder)
    try:
        header_font = ImageFont.truetype("Roboto-Bold.ttf", 80)
        body_font = ImageFont.truetype("Roboto-Regular.ttf", 45)
    except:
        header_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Draw Accent Bar
    draw.rectangle([50, 100, 150, 110], fill=accent_color)

    # Wrap and Draw Headline
    lines = textwrap.wrap(headline, width=20)
    y_text = 150
    for line in lines:
        draw.text((50, y_text), line, font=header_font, fill=(255, 255, 255))
        y_text += 90

    # Draw Brief
    y_text += 50
    body_lines = textwrap.wrap(brief, width=40)
    for line in body_lines:
        draw.text((50, y_text), line, font=body_font, fill=(200, 200, 200))
        y_text += 60

    img.save(output_path, quality=95)
    print(f"Card saved to {output_path}")

# Example usage
create_news_card("AI Breakthrough", "Gemini 3 Flash now powers autonomous news agents with zero-latency processing.")
