"""
main.py — News-to-Gram
──────────────────────
Fetches the latest photo from a Telegram channel → posts to Instagram.
Runs on GitHub Actions. Session-only auth (no login calls).
"""

import os
import json
import asyncio
import requests
import warnings
import time
from pathlib import Path

from aiogram import Bot
from instagrapi import Client
from PIL import Image

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ── Secrets ────────────────────────────────────────────────────────────────────
TOKEN       = os.getenv("TOKEN")
IG_SESSION  = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
CHANNEL_ID  = os.getenv("CHANNEL_ID")

IMAGE_PATH = Path("sync_image.jpg")


# ══════════════════════════════════════════════════════════════════════════════
# INSTAGRAM
# ══════════════════════════════════════════════════════════════════════════════

def ig_build_client():
    """Restore Instagram client from session JSON. Never calls login()."""
    if not IG_SESSION:
        print("❌  IG_SESSION secret is missing.")
        return None

    cl = Client()
    cl.delay_range = [2, 5]
    cl.set_user_agent(
        "Instagram 219.0.0.12.117 Android "
        "(28/9; 480dpi; 1080x1920; OnePlus; OnePlus 6T; en_US)"
    )

    try:
        settings = json.loads(IG_SESSION)
        cl.set_settings(settings)
        print("🔄  Restoring Instagram session…")
        info = cl.account_info()
        print(f"✅  Instagram session active: @{info.username}")
        return cl
    except Exception as e:
        print(f"❌  Instagram session restore failed: {e}")
        print("    → Re-run run_once_extract_session.py locally and update IG_SESSION.")
        return None


def prepare_image(path: Path) -> None:
    """Crop/resize image to meet Instagram's upload requirements."""
    img = Image.open(path).convert("RGB")
    w, h = img.size

    MIN_R, MAX_R = 4 / 5, 1.91
    r = w / h
    if r < MIN_R:
        new_h = int(w / MIN_R)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    elif r > MAX_R:
        new_w = int(h * MAX_R)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))

    w, h = img.size
    if max(w, h) > 1440:
        scale = 1440 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    elif min(w, h) < 320:
        scale = 320 / min(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    img.save(path, "JPEG", quality=95, optimize=True)
    w, h = img.size
    print(f"🖼   Image ready: {w}×{h}px  ratio={w/h:.2f}")


def ig_upload(cl: Client, path: Path, caption: str) -> bool:
    """Upload photo to Instagram with retry logic."""
    prepare_image(path)

    for attempt in range(1, 4):
        try:
            print(f"📤  Upload attempt {attempt}/3…")
            media = cl.photo_upload(str(path), caption)
            print(f"🚀  Posted! Instagram media ID: {media.pk}")
            return True
        except Exception as e:
            msg = str(e).lower()
            print(f"⚠️   Attempt {attempt} failed: {e}")

            if "login_required" in msg or "not authorized" in msg or "authorization" in msg:
                print("❌  Session rejected by Instagram. Update IG_SESSION secret.")
                return False

            wait = 30 * attempt
            print(f"⏳  Waiting {wait}s before retry…")
            time.sleep(wait)

    print("❌  All upload attempts failed.")
    return False


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM  (completely isolated — Instagram code never runs inside here)
# ══════════════════════════════════════════════════════════════════════════════

async def telegram_fetch():
    """
    Returns (image_bytes, caption) or (None, '') on failure.
    Fully separated from Instagram logic.
    """
    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡  Fetching latest post from channel {CHANNEL_ID}…")

            updates = await bot.get_updates(
                offset=-1,
                limit=10,
                timeout=15,
                allowed_updates=["channel_post"],
            )

            target = None
            for upd in reversed(updates):
                msg = upd.channel_post
                if msg and msg.photo and str(msg.chat.id) == str(CHANNEL_ID):
                    target = msg
                    break

            # Fallback: search without channel filter
            if not target:
                updates = await bot.get_updates(offset=-1, limit=50, timeout=15)
                for upd in reversed(updates):
                    msg = upd.channel_post
                    if msg and msg.photo:
                        target = msg
                        break

            if not target:
                print("ℹ️   No recent photo post found in the channel.")
                return None, ""

            caption = target.caption or ""
            print(f"📸  Found: {caption[:60]}…")

            file = await bot.get_file(target.photo[-1].file_id)
            photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"

            resp = requests.get(photo_url, timeout=30)
            resp.raise_for_status()
            print(f"⬇️   Downloaded image ({len(resp.content) // 1024} KB)")
            return resp.content, caption

        except Exception as e:
            print(f"❌  Telegram error: {e}")
            return None, ""


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    required = {
        "TOKEN": TOKEN, "IG_SESSION": IG_SESSION,
        "IG_USERNAME": IG_USERNAME, "CHANNEL_ID": CHANNEL_ID
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌  Missing GitHub secrets: {', '.join(missing)}")
        raise SystemExit(1)

    # Step 1: Instagram session (completely separate from Telegram)
    cl = ig_build_client()
    if cl is None:
        raise SystemExit(1)

    # Step 2: Telegram fetch (completely separate from Instagram)
    image_bytes, caption = await telegram_fetch()
    if image_bytes is None:
        raise SystemExit(1)

    # Step 3: Save image to disk
    IMAGE_PATH.write_bytes(image_bytes)

    # Step 4: Upload to Instagram
    success = ig_upload(cl, IMAGE_PATH, caption)

    # Cleanup
    if IMAGE_PATH.exists():
        IMAGE_PATH.unlink()

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
