import os
import asyncio
import textwrap
import requests
import random
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# Config
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE = "deepdive.group"
HASHTAGS = "#news #breakingnews #currentaffairs #upsc #india #trending"

# High-contrast Gen Z Palettes (Bottom Gradient, Accent Line)
VIBE_PALETTES = [
    {"grad": (0, 255, 127), "line": (0, 255, 127)},   # Spring Green
    {"grad": (255, 20, 147), "line": (255, 20, 147)}, # Deep Pink
    {"grad": (0, 191, 255), "line": (0, 191, 255)},  # Deep Sky Blue
    {"grad": (255, 165, 0), "line": (255, 165, 0)},   # Vivid Orange
    {"grad": (138, 43, 226), "line": (138, 43, 226)}  # Blue Violet
]

# Keywords to strip from caption lines entirely
JUNK_KEYWORDS = ["READ FULL STORY", "RELATED", "JOIN", "SOURCE", "🔗", "HTTP"]

def is_junk_line(line):
    """Return True if this line should be excluded from the card footer text."""
    upper = line.upper()
    return any(k in upper for k in JUNK_KEYWORDS)

def extract_source(lines):
    """Pull the source name from lines like 'Source: The Hindu 🔗' → 'The Hindu'"""
    for line in lines:
        if "SOURCE" in line.upper():
            # Strip emoji, label, URLs
            clean = line
            for prefix in ["Source:", "SOURCE:", "source:"]:
                clean = clean.replace(prefix, "")
            # Remove anything after a URL-ish token
            parts = clean.split()
            name_parts = [p for p in parts if not p.startswith("http") and "🔗" not in p]
            result = " ".join(name_parts).strip()
            if result:
                return result
    return ""

async def generate_premium_card(headline, source, img_path):
    palette = random.choice(VIBE_PALETTES)
    CANVAS_W, CANVAS_H = 1080, 1080
    HEADER_H = 140
    FOOTER_H = 360  # fixed footer height from bottom

    # --- Canvas ---
    canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), color=(10, 10, 10))
    draw = ImageDraw.Draw(canvas)

    # --- Fonts ---
    try:
        f_top  = ImageFont.truetype("Anton-Regular.ttf", 75)
        f_head = ImageFont.truetype("Poppins-SemiBold.ttf", 48)
        f_sub  = ImageFont.truetype("Poppins-Regular.ttf", 30)
    except Exception:
        f_top = f_head = f_sub = ImageFont.load_default()

    # 1. Header (Fixed Red)
    draw.rectangle([0, 0, CANVAS_W, HEADER_H], fill=(211, 47, 47))
    draw.text((CANVAS_W // 2, HEADER_H // 2), "LATEST",
              font=f_top, fill="white", anchor="mm")

    # 2. Main photo — fills the middle, cropped to available space
    photo_area_top = HEADER_H
    photo_area_bottom = CANVAS_H - FOOTER_H
    photo_area_h = photo_area_bottom - photo_area_top  # 580px

    photo = Image.open(img_path).convert("RGB")
    p_w, p_h = photo.size

    # Scale to fill width, then crop height to fit photo area
    scale = CANVAS_W / p_w
    new_w = CANVAS_W
    new_h = int(p_h * scale)
    photo = photo.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # If taller than area, centre-crop; if shorter, just paste at top of area
    if new_h >= photo_area_h:
        crop_top = (new_h - photo_area_h) // 2
        photo = photo.crop((0, crop_top, new_w, crop_top + photo_area_h))
    canvas.paste(photo, (0, photo_area_top))

    # 3. Footer gradient (bottom FOOTER_H pixels)
    footer_top = CANVAS_H - FOOTER_H
    for i in range(FOOTER_H):
        alpha = i / FOOTER_H  # 0 at footer_top → 1 at bottom
        r = int(10 * (1 - alpha) + palette["grad"][0] * (alpha * 0.35))
        g = int(10 * (1 - alpha) + palette["grad"][1] * (alpha * 0.35))
        b = int(10 * (1 - alpha) + palette["grad"][2] * (alpha * 0.35))
        draw.line((0, footer_top + i, CANVAS_W, footer_top + i), fill=(r, g, b))

    # 4. Accent line at top of footer
    ACCENT_H = 8
    draw.rectangle([0, footer_top, CANVAS_W, footer_top + ACCENT_H], fill=palette["line"])

    # 5. Headline text — safe margin so nothing clips
    MARGIN = 60  # px on each side
    MAX_TEXT_W = CANVAS_W - 2 * MARGIN  # 960px

    head_upper = headline.upper().strip()

    # Dynamic wrapping: find the tightest wrap that keeps all lines within MAX_TEXT_W
    def measure_text_width(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    # Start with a loose wrap, tighten until no line overflows
    wrap_chars = 28
    while wrap_chars > 10:
        wrapped = textwrap.wrap(head_upper, width=wrap_chars)
        if all(measure_text_width(line, f_head) <= MAX_TEXT_W for line in wrapped):
            break
        wrap_chars -= 1

    # Calculate total text block height to vertically centre it in the footer
    LINE_H = 65
    text_block_h = len(wrapped) * LINE_H
    # Reserve bottom 70px for source line
    usable_footer_h = FOOTER_H - ACCENT_H - 70
    text_start_y = footer_top + ACCENT_H + (usable_footer_h - text_block_h) // 2

    for i, line in enumerate(wrapped):
        y = text_start_y + i * LINE_H
        draw.text((CANVAS_W // 2, y), line, font=f_head, fill="white", anchor="mm")

    # 6. Source line — pinned 40px from bottom
    if source:
        src_text = f"SOURCE: {source.upper()}"
        draw.text((CANVAS_W // 2, CANVAS_H - 40), src_text,
                  font=f_sub, fill=(200, 200, 200), anchor="mm")

    canvas.save("post_image.jpg", quality=95)
    print("✅ Card saved: post_image.jpg")


async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)
            target = next(
                (u.channel_post for u in reversed(updates)
                 if u.channel_post and u.photo),
                None
            )

            if not target:
                print("No post with photo found.")
                return

            # Download photo
            file = await bot.get_file(target.photo[-1].file_id)
            img_data = requests.get(
                f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            ).content
            with open("temp.jpg", "wb") as f:
                f.write(img_data)

            # Parse caption
            caption = target.caption or ""
            lines = [l.strip() for l in caption.split('\n') if l.strip()]

            headline = lines[0] if lines else "Breaking News"
            source   = extract_source(lines)   # clean source name

            # Generate card
            await generate_premium_card(headline, source, "temp.jpg")

            # IG caption — strip junk lines, keep clean content
            clean_lines = [l for l in lines if not is_junk_line(l)]
            final_caption = "\n".join(clean_lines)
            final_caption += (
                f"\n\n🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗\n\n{HASHTAGS}"
            )

            with open("post_caption.txt", "w", encoding="utf-8") as f:
                f.write(final_caption)

            print("✅ Success: post_image.jpg and post_caption.txt created.")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
