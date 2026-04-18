import os
import asyncio
import requests
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Config ─────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
IG_HANDLE  = "deepdive.group"
HASHTAGS   = "#news #breakingnews #currentaffairs #upsc #india #trending"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_PATH   = os.path.join(OUTPUT_DIR, "post_image.jpg")
TEMP_PATH  = os.path.join(OUTPUT_DIR, "temp.jpg")
CAP_PATH   = os.path.join(OUTPUT_DIR, "post_caption.txt")

FONTS = {
    "bold":   "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "medium": "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
    "reg":    "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
}

JUNK_KW = ["READ FULL STORY", "RELATED", "JOIN", "SOURCE", "🔗", "HTTP"]


def is_junk_line(line: str) -> bool:
    return any(k in line.upper() for k in JUNK_KW)


def extract_source(lines: list[str]) -> str:
    for line in lines:
        if "SOURCE" in line.upper():
            clean = line
            for prefix in ["Source:", "SOURCE:", "source:"]:
                clean = clean.replace(prefix, "")
            parts = [p for p in clean.split()
                     if not p.startswith("http") and "🔗" not in p]
            result = " ".join(parts).strip()
            if result:
                return result
    return ""


def wrap_to_px(text: str, font, max_px: int,
               draw: ImageDraw.ImageDraw) -> list[str]:
    """Word-wrap text (uppercased) so no line exceeds max_px wide."""
    words = text.upper().split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_px:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


async def generate_card(headline: str, source: str, photo_path: str):
    W, H = 1080, 1080

    try:
        f_badge    = ImageFont.truetype(FONTS["bold"],   34)
        f_breaking = ImageFont.truetype(FONTS["bold"],   44)
        f_head     = ImageFont.truetype(FONTS["bold"],   78)
        f_src      = ImageFont.truetype(FONTS["medium"], 38)
    except Exception:
        f_badge = f_breaking = f_head = f_src = ImageFont.load_default()

    # 1. Full-bleed photo background
    photo = Image.open(photo_path).convert("RGBA")
    pw, ph = photo.size
    scale  = max(W / pw, H / ph)
    photo  = photo.resize((int(pw * scale), int(ph * scale)),
                          Image.Resampling.LANCZOS)
    ox = (photo.width  - W) // 2
    oy = (photo.height - H) // 2
    photo = photo.crop((ox, oy, ox + W, oy + H))

    # 2. Blur the middle band to erase any baked-in text from source image
    photo_rgb = photo.convert("RGB")
    band = photo_rgb.crop((0, 440, W, 730))
    band = band.filter(ImageFilter.GaussianBlur(radius=18))
    photo_rgb.paste(band, (0, 440))
    photo = photo_rgb.convert("RGBA")

    canvas = Image.new("RGBA", (W, H))
    canvas.paste(photo, (0, 0))

    # 3. Dark gradient overlay (transparent top → nearly opaque bottom)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od      = ImageDraw.Draw(overlay)
    START   = int(H * 0.18)
    for y in range(START, H):
        t     = (y - START) / (H - START)
        alpha = int(252 * min(t ** 0.42, 1.0))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    draw   = ImageDraw.Draw(canvas)

    MARGIN = 52
    MAX_W  = W - 2 * MARGIN

    # 4. LATEST badge (top-left red pill)
    BX, BY   = MARGIN, 48
    BPX, BPY = 22, 12
    bbox = draw.textbbox((0, 0), "LATEST", font=f_badge)
    bw   = bbox[2] - bbox[0] + BPX * 2
    bh   = bbox[3] - bbox[1] + BPY * 2
    draw.rounded_rectangle([BX, BY, BX + bw, BY + bh],
                           radius=8, fill=(211, 47, 47, 255))
    draw.text((BX + BPX, BY + BPY), "LATEST", font=f_badge, fill="white")

    # 5. BREAKING NEWS label with red left-bar accent
    BREAK_Y = int(H * 0.50)
    draw.rectangle([MARGIN, BREAK_Y + 6, MARGIN + 6, BREAK_Y + 46],
                   fill=(211, 47, 47, 255))
    draw.text((MARGIN + 18, BREAK_Y), "BREAKING NEWS",
              font=f_breaking, fill="white")

    # 6. Headline — large bold all-caps, pixel-safe wrapping
    head_lines = wrap_to_px(headline, f_head, MAX_W, draw)
    LINE_H_H   = 90
    HEAD_Y     = BREAK_Y + 72

    for i, line in enumerate(head_lines):
        y = HEAD_Y + i * LINE_H_H
        draw.text((MARGIN + 2, y + 2), line, font=f_head, fill=(0, 0, 0, 190))
        draw.text((MARGIN,     y),     line, font=f_head, fill="white")

    # 7. Source — red bar + grey text, pinned to bottom
    if source:
        bar_y = H - 100
        draw.rectangle([MARGIN, bar_y, MARGIN + 50, bar_y + 5],
                       fill=(211, 47, 47, 255))
        draw.text((MARGIN, bar_y + 14), source,
                  font=f_src, fill=(210, 210, 210, 255))

    canvas.convert("RGB").save(IMG_PATH, quality=96)
    print(f"✅ Card saved → {IMG_PATH}")


async def main():
    async with Bot(token=TOKEN) as bot:
        try:
            updates = await bot.get_updates(offset=-1, limit=5)

            # FIX: check .photo on channel_post, NOT on the Update object
            target = next(
                (u.channel_post for u in reversed(updates)
                 if u.channel_post and u.channel_post.photo),
                None,
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

            await generate_card(headline, source, TEMP_PATH)

            # IG caption — strip junk lines
            clean_lines   = [l for l in lines if not is_junk_line(l)]
            final_caption = "\n".join(clean_lines)
            final_caption += (
                f"\n\n🏛️ Read the Full Story: Link in Bio @{IG_HANDLE} 🔗"
                f"\n\n{HASHTAGS}"
            )
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                f.write(final_caption)

            print(f"✅ Caption saved → {CAP_PATH}")

        except Exception as e:
            print(f"Error: {e}")
            raise   # re-raise so GitHub Actions marks step as failed


if __name__ == "__main__":
    asyncio.run(main())
