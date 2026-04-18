import os
import json
import asyncio
import requests
import warnings
import time
import io
from pathlib import Path
from aiogram import Bot
from instagrapi import Client
from PIL import Image

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ── Secrets ────────────────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN")
IG_SESSION = os.getenv("IG_SESSION")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
CHANNEL_ID  = os.getenv("CHANNEL_ID")

IMAGE_PATH = Path("sync_image.jpg")


# ── Helpers ────────────────────────────────────────────────────────────────────

def prepare_image(path: Path) -> Path:
    """
    Ensure the image meets Instagram's requirements:
      • JPEG format, RGB mode
      • Aspect ratio between 4:5 (portrait) and 1.91:1 (landscape)
      • Minimum 320 px on shortest side
      • Maximum 1440 px on longest side
    Returns the (possibly modified) path.
    """
    img = Image.open(path).convert("RGB")
    w, h = img.size

    # ── Clamp aspect ratio ───────────────────────────────────────────────────
    ratio = w / h
    MIN_RATIO = 4 / 5          # 0.8  (tallest portrait Instagram allows)
    MAX_RATIO = 1.91           # widest landscape Instagram allows

    if ratio < MIN_RATIO:      # too tall → crop top/bottom
        new_h = int(w / MIN_RATIO)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))
    elif ratio > MAX_RATIO:    # too wide → crop sides
        new_w = int(h * MAX_RATIO)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))

    w, h = img.size            # refresh after crop

    # ── Clamp resolution ─────────────────────────────────────────────────────
    MAX_DIM = 1440
    MIN_DIM = 320
    if max(w, h) > MAX_DIM:
        scale = MAX_DIM / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    if min(w, h) < MIN_DIM:
        scale = MIN_DIM / min(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    img.save(path, "JPEG", quality=95, optimize=True)
    w, h = img.size
    print(f"🖼  Image prepared: {w}×{h}px  ratio={w/h:.3f}")
    return path


def ig_login() -> Client | None:
    """
    Authenticate with Instagram.
    Priority: stored session → fresh login.
    Returns a logged-in Client or None on failure.
    """
    cl = Client()
    cl.delay_range = [1, 3]   # randomise request delays (looks more human)
    cl.set_user_agent(
        "Instagram 219.0.0.12.117 Android "
        "(28/9; 480dpi; 1080x1920; OnePlus; OnePlus 6T; en_US)"
    )

    # Attempt 1 — stored session
    if IG_SESSION:
        try:
            print("🔄 Trying stored Instagram session…")
            cl.set_settings(json.loads(IG_SESSION))
            cl.login(IG_USERNAME, IG_PASSWORD)   # reuse session + relogin if expired
            cl.get_timeline_feed()               # light validation call
            print(f"✅ Session valid for @{IG_USERNAME}")
            return cl
        except Exception as e:
            print(f"⚠️  Session login failed: {e}")

    # Attempt 2 — fresh login
    try:
        print(f"🔄 Fresh login for @{IG_USERNAME}…")
        time.sleep(2)
        cl.login(IG_USERNAME, IG_PASSWORD)
        print("✅ Fresh login successful!")
        # Uncomment the next line to print the new session JSON for your secret:
        # print("NEW_SESSION:", json.dumps(cl.get_settings()))
        return cl
    except Exception as e:
        print(f"❌ Instagram auth failed: {e}")
        return None


def ig_upload(cl: Client, image_path: Path, caption: str) -> bool:
    """
    Upload a photo to Instagram with retry logic.
    Returns True on success.
    """
    prepare_image(image_path)

    for attempt in range(1, 4):          # up to 3 attempts
        try:
            print(f"📤 Upload attempt {attempt}/3…")
            media = cl.photo_upload(str(image_path), caption)
            print(f"🚀 SUCCESS! Instagram Media ID: {media.pk}")
            return True
        except Exception as e:
            err = str(e)
            print(f"⚠️  Upload attempt {attempt} failed: {err}")

            if "412" in err or "feedback_required" in err:
                # Instagram rate-limit / challenge — back off longer
                wait = 30 * attempt
                print(f"⏳ Instagram rate-limit detected. Waiting {wait}s…")
                time.sleep(wait)
            elif "login_required" in err.lower():
                print("🔁 Session expired mid-run. Re-authenticating…")
                cl.login(IG_USERNAME, IG_PASSWORD)
            else:
                time.sleep(10 * attempt)

    print("❌ All upload attempts exhausted.")
    return False


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    # Validate secrets
    missing = [k for k, v in {
        "TOKEN": TOKEN, "IG_USERNAME": IG_USERNAME,
        "IG_PASSWORD": IG_PASSWORD, "CHANNEL_ID": CHANNEL_ID
    }.items() if not v]
    if missing:
        print(f"❌ Missing secrets: {', '.join(missing)}")
        return

    # ── Step 1: Instagram login ────────────────────────────────────────────────
    cl = ig_login()
    if cl is None:
        return

    # ── Step 2: Fetch latest photo from Telegram channel ──────────────────────
    target_post = None
    photo_url   = None

    async with Bot(token=TOKEN) as bot:
        try:
            print(f"📡 Fetching last post from channel {CHANNEL_ID}…")

            # get_updates only works if the bot can receive updates;
            # using a large negative offset fetches the most recent batch.
            updates = await bot.get_updates(offset=-1, limit=10, timeout=10)

            for update in reversed(updates):
                msg = update.channel_post
                if msg and str(msg.chat.id) == str(CHANNEL_ID) and msg.photo:
                    target_post = msg
                    break

            if not target_post:
                print("ℹ️  No recent photo post found in the channel.")
                return

            caption_preview = (target_post.caption or "")[:60]
            print(f"📸 Found Post: {caption_preview}…")

            # Highest resolution = last item in photo array
            file      = await bot.get_file(target_post.photo[-1].file_id)
            photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"

        except Exception as e:
            print(f"❌ Telegram fetch error: {e}")
            return

    # ── Step 3: Download image ─────────────────────────────────────────────────
    try:
        print("⬇️  Downloading image…")
        resp = requests.get(photo_url, timeout=30)
        resp.raise_for_status()
        IMAGE_PATH.write_bytes(resp.content)
        print(f"✅ Image saved ({IMAGE_PATH.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"❌ Image download failed: {e}")
        return

    # ── Step 4: Upload to Instagram ───────────────────────────────────────────
    caption = target_post.caption or ""
    success = ig_upload(cl, IMAGE_PATH, caption)

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if IMAGE_PATH.exists():
        IMAGE_PATH.unlink()

    if not success:
        raise SystemExit(1)   # fail the GitHub Actions job on error


if __name__ == "__main__":
    asyncio.run(main())
