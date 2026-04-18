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

# Output paths — absolute so GitHub Actions always finds them
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(OUTPUT_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(OUTPUT_DIR, "temp.jpg")
CAP_PATH   = os.path.join(OUTPUT_DIR, "post_caption.txt")

# High-contrast Gen Z Palettes (Bottom Gradient, Accent Line)
VIBE_PALETTES = [
    {"grad": (0, 255, 127),   "line": (0, 255, 127)},   # Spring Green
    {"grad": (255, 20, 147),  "line": (255, 20, 147)},  # Deep Pink
    {"grad": (0, 191, 255),   "line": (0, 191, 255)},   # Deep Sky Blue
    {"grad": (255, 165, 0),   "line": (255, 165, 0)},   # Vivid Orange
    {"grad": (138, 43, 226),  "line": (138, 43, 226)},  # Blue Violet
]

# Lines containing these keywords are stripped from both the card and IG caption
JUNK_KEYWORDS = ["READ FULL STORY", "RELATED", "JOIN", "SOURCE", "🔗", "HTTP"]

def is_junk_line(line: str) -> bool:
    upper = line.upper()
    return any(k in upper for k in JUNK_KEYWORDS)

def extract_source(lines: list[str]) -> str:
    """Return a clean source name from lines like 'Source: The Hindu 🔗'."""
    for line in lines:
        if "SOURCE" in line.upper():
            clean = line
            for prefix in ["Source:", "SOURCE:", "source:"]:
                clean = clean.replace(prefix, "")
            parts = clean.split()
            name_parts = [p for p in parts if not p.startswith("http") and "🔗" not in p]
            result = " ".join(name_parts).strip()
            if result:
                return result
    return ""

async def generate_premium_card(headline: str, source: str, img_path: str):
    palette = random.choice(VIBE_PALETTES)
    CANVAS_W, CANVAS_H = 1080, 1080
    HEADER_H = 140
    FOOTER_H = 360   # fixed footer height from bottom

    # --- Canvas ---
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), color=(10, 10, 10))
    draw   = ImageDraw.Draw(canvas)

    # --- Fonts ---
    try:
        f_top  = ImageFont.truetype("Anton-Regular.ttf", 75)
        f_head = ImageFont.truetype("Poppins-SemiBold.ttf", 48)
        f_sub  = ImageFont.truetype("Poppins-Regular.ttf", 30)
    except Exception:
        f_top = f_head = f_sub = ImageFont.load_default()

    # 1. Header
    draw.rectangle([0, 0, CANVAS_W, HEADER_H], fill=(211, 47, 47))
    draw.text((CANVAS_W // 2, HEADER_H // 2), "LATEST",
              font=f_top, fill="white", anchor="mm")

    # 2. Main photo — cropped to fit exactly between header and footer
    photo_area_top = HEADER_H
    photo_area_h   = CANVAS_H - FOOTER_H - HEADER_H   # 580 px

    photo = Image.open(img_path).convert("RGB")
    p_w, p_h = photo.size
    scale = CANVAS_W / p_w
    photo = photo.resize((CANVAS_W, int(p_h * scale)), Image.Resampling.LANCZOS)

    new_h = photo.size[1]
    if new_h >= photo_area_h:
        crop_top = (new_h - photo_area_h) // 2
        photo = photo.crop((0, crop_top, CANVAS_W, crop_top + photo_area_h))
    canvas.paste(photo, (0, photo_area_top))

    # 3. Footer gradient
    footer_top = CANVAS_H - FOOTER_H
    for i in range(FOOTER_H):
        alpha = i / FOOTER_H
        r = int(10 * (1 - alpha) + palette["grad"][0] * alpha * 0.35)
        g = int(10 * (1 - alpha) + palette["grad"][1] * alpha * 0.35)
        b = int(10 * (1 - alpha) + palette["grad"][2] * alpha * 0.35)
        draw.line((0, footer_top + i, CANVAS_W, footer_top + i), fill=(r, g, b))

    # 4. Accent line
    ACCENT_H = 8
    draw.rectangle([0, footer_top, CANVAS_W, footer_top + ACCENT_H], fill=palette["line"])

    # 5. Headline — dynamic pixel-aware wrapping so text never clips edges
    MARGIN       = 60
    MAX_TEXT_W   = CANVAS_W - 2 * MARGIN   # 960 px
    head_upper   = headline.upper().strip()

    def text_width(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    wrap_chars = 28
    while wrap_chars > 8:
        wrapped = textwrap.wrap(head_upper, width=wrap_chars)
        if all(text_width(line, f_head) <= MAX_TEXT_W for line in wrapped):
            break
        wrap_chars -= 1

    LINE_H        = 65
    text_block_h  = len(wrapped) * LINE_H
    usable_h      = FOOTER_H - ACCENT_H - 70   # leave 70 px for source
    text_start_y  = footer_top + ACCENT_H + (usable_h - text_block_h) // 2

    for i, line in enumerate(wrapped):
        draw.text((CANVAS_W // 2, text_start_y + i * LINE_H),
                  line, font=f_head, fill="white", anchor="mm")

    # 6. Source — pinned 40 px from bottom
    if source:
        draw.text((CANVAS_W // 2, CANVAS_H - 40),
                  f"SOURCE: {source.upper()}",
                  font=f_sub, fill=(200, 200, 200), anchor="mm")

    canvas.save(IMG_PATH, quality=95)
    print(f"✅ Card saved → {IMG_PATH}")


async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)

            # FIX: check .photo on channel_post, not on the Update object
            target = next(
                (u.channel_post for u in reversed(updates)
                 if u.channel_post and u.channel_post.photo),
                None
            )

            if not target:
                print("No channel post with a photo found.")
                return

            # Download photo
            file     = await bot.get_file(target.photo[-1].file_id)
            img_data = requests.get(
                f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
            ).content
            with open(TEMP_PATH, "wb") as f:
                f.write(img_data)

            # Parse caption
            caption = target.caption or ""
            lines   = [l.strip() for l in caption.split("\n") if l.strip()]

            headline = lines[0] if lines else "Breaking News"
            source   = extract_source(lines)

            # Generate card
            await generate_premium_card(headline, source, TEMP_PATH)

            # IG caption — strip junk lines
            clean_lines   = [l for l in lines if not is_junk_line(l)]
            final_caption = "\n".join(clean_lines)
            final_caption += (
                f"\n\n🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗\n\n{HASHTAGS}"
            )

            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(final_caption)

            print(f"✅ Caption saved → {CAP_PATH}")

        except Exception as e:
            print(f"Error: {e}")
            raise   # re-raise so GitHub Actions marks the step as failed


if __name__ == "__main__":
    asyncio.run(main())
