import os
import asyncio
import requests
from aiogram import Bot
from PIL import Image, ImageDraw, ImageFont

# ── Config ─────────────────────────────────────────────────────────────────────
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
    upper = line.upper()
    return any(k in upper for k in JUNK_KW)


def extract_source(lines: list[str]) -> str:
    for line in lines:
        if "SOURCE" in line.upper():
            clean = line
            for prefix in ["Source:", "SOURCE:", "source:"]:
                clean = clean.replace(prefix, "")
            parts = [p for p in clean.split() if not p.startswith("http") and "🔗" not in p]
            result = " ".join(parts).strip()
            if result:
                return result
    return ""


def wrap_to_px(text: str, font, max_px: int, draw: ImageDraw.ImageDraw) -> list[str]:
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


async def generate_card(headline: str, subtext: str, source: str, photo_path: str):
    W, H = 1080, 1080

    try:
        f_badge = ImageFont.truetype(FONTS["bold"],   30)
        f_head  = ImageFont.truetype(FONTS["bold"],   72)
        f_sub   = ImageFont.truetype(FONTS["reg"],    36)
        f_src   = ImageFont.truetype(FONTS["medium"], 30)
    except Exception:
        f_badge = f_head = f_sub = f_src = ImageFont.load_default()

    # 1. Full-bleed photo background
    photo = Image.open(photo_path).convert("RGBA")
    pw, ph = photo.size
    scale  = max(W / pw, H / ph)
    photo  = photo.resize((int(pw * scale), int(ph * scale)), Image.Resampling.LANCZOS)
    ox = (photo.width  - W) // 2
    oy = (photo.height - H) // 2
    photo = photo.crop((ox, oy, ox + W, oy + H))

    canvas = Image.new("RGBA", (W, H))
    canvas.paste(photo, (0, 0))

    # 2. Transparent-to-black gradient overlay (photo visible at top)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od      = ImageDraw.Draw(overlay)
    START   = int(H * 0.28)
    for y in range(START, H):
        t     = (y - START) / (H - START)
        alpha = int(248 * min(t ** 0.62, 1.0))
        od.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, overlay)

    draw   = ImageDraw.Draw(canvas)
    MARGIN = 50
    MAX_W  = W - 2 * MARGIN

    # 3. LATEST badge
    BX, BY   = 40, 40
    BPX, BPY = 20, 10
    bbox = draw.textbbox((0, 0), "LATEST", font=f_badge)
    bw   = bbox[2] - bbox[0] + BPX * 2
    bh   = bbox[3] - bbox[1] + BPY * 2
    draw.rounded_rectangle([BX, BY, BX + bw, BY + bh], radius=6, fill=(211, 47, 47, 255))
    draw.text((BX + BPX, BY + BPY), "LATEST", font=f_badge, fill="white")

    # 4. Headline
    head_lines = wrap_to_px(headline, f_head, MAX_W, draw)
    LINE_H_H   = 82
    HEAD_Y     = int(H * 0.50)
    for i, line in enumerate(head_lines):
        y = HEAD_Y + i * LINE_H_H
        draw.text((MARGIN + 2, y + 2), line, font=f_head, fill=(0, 0, 0, 160))
        draw.text((MARGIN,     y),     line, font=f_head, fill="white")

    # 5. Subtext
    if subtext:
        sub_lines = wrap_to_px(subtext, f_sub, MAX_W, draw)
        sub_top   = HEAD_Y + len(head_lines) * LINE_H_H + 18
        for i, line in enumerate(sub_lines):
            draw.text((MARGIN, sub_top + i * 50), line.title(),
                      font=f_sub, fill=(215, 215, 215, 255))

    # 6. Source with red dash
    if source:
        src_y = H - 56
        draw.rectangle([MARGIN, src_y + 16, MARGIN + 30, src_y + 19],
                       fill=(211, 47, 47, 255))
        draw.text((MARGIN + 44, src_y), source,
                  font=f_src, fill=(195, 195, 195, 255))

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
            sub_lines = [l for l in lines[1:] if not is_junk_line(l)]
            subtext   = " ".join(sub_lines[:2])

            await generate_card(headline, subtext, source, TEMP_PATH)

            # IG caption
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
            raise


if __name__ == "__main__":
    asyncio.run(main())
