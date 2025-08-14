import asyncio
import random
import time
import os
import logging
from collections import deque
from datetime import datetime, timedelta
from pyrogram import Client
from playwright.async_api import async_playwright
import portalsmp as pm

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# --- Environment Vars ---
SESSION_STRING = os.environ.get("SESSION_STRING")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
CHANNEL = os.environ.get("CHANNEL")

MIN_DROP_PERCENT = int(os.environ.get("MIN_DROP_PERCENT", 10))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 200))
MAX_GIFTS = int(os.environ.get("MAX_GIFTS", 5000))
CHECK_INTERVAL = (
    int(os.environ.get("CHECK_MIN", 60)),
    int(os.environ.get("CHECK_MAX", 120))
)
FRESH_SEC = int(os.environ.get("FRESH_SEC", 60))
SEEN_MAX_AGE = FRESH_SEC * 10  # prune old seen IDs

if not SESSION_STRING or not API_ID or not API_HASH or not CHANNEL:
    raise RuntimeError("Не все переменные окружения заданы!")

# --- Track seen items with timestamps ---
seen_ids = deque()

# --- Skip Playwright checks for Railway ---
os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "1"

# --- Utilities ---
def prune_seen_ids():
    """Remove old seen IDs to save memory."""
    now = time.time()
    while seen_ids and now - seen_ids[0][1] > SEEN_MAX_AGE:
        seen_ids.popleft()

def is_seen(gid):
    """Check if item seen recently."""
    return any(item_id == gid for item_id, _ in seen_ids)

def mark_seen(gid):
    seen_ids.append((gid, time.time()))
    prune_seen_ids()

def safe_parse_time(val):
    """Convert timestamp string/int to epoch seconds."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return time.mktime(time.strptime(val.split(".")[0], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            try:
                return float(val)
            except ValueError:
                return None
    return None

def safe_parse_float(val):
    try:
        return float(str(val).replace("~", "").replace(",", "").strip())
    except ValueError:
        return None

# --- Playwright bypass Cloudflare ---
async def bypass_cf():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20A5346a TelegramBot/8.0"
                )
            )
            page = await context.new_page()
            await page.goto("https://portals-market.com", wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(3, 6))
            for _ in range(random.randint(2, 5)):
                await page.mouse.wheel(0, random.randint(300, 700))
                await asyncio.sleep(random.uniform(0.3, 1.0))
            await context.close()
            await browser.close()
            log.info("[CF] Bypass done")
    except Exception as e:
        log.error(f"[CF] Bypass failed: {e}")

# --- Filter fresh gifts ---
def filter_fresh_gifts(items, min_drop, fresh_sec=60):
    out = []
    now = time.time()
    for g in items:
        gid = g.get("id") or g.get("token_id")
        if not gid or is_seen(gid):
            continue

        listed_ts = safe_parse_time(g.get("listed_at"))
        if not listed_ts or now - listed_ts > fresh_sec:
            continue

        price = safe_parse_float(g.get("price"))
        floor = safe_parse_float(g.get("floor_price"))
        if price is None or floor is None or floor <= 0:
            continue

        drop_percent = 100 * (1 - price / floor)
        if drop_percent >= min_drop:
            g["drop_percent"] = round(drop_percent, 1)
            out.append(g)
            mark_seen(gid)
    log.info(f"[FILTER] {len(items)} gifts -> {len(out)} fresh gifts")
    return out

# --- Safe fetch wrapper ---
async def fetch_gifts(token):
    all_gifts = []
    for offset in range(0, MAX_GIFTS, BATCH_SIZE):
        batch = await asyncio.to_thread(
            pm.search, sort="price_asc", limit=BATCH_SIZE, offset=offset, authData=token
        )
        if not batch:
            break
        all_gifts.extend(batch)
    return all_gifts

# --- Main monitoring loop ---
async def monitor_loop():
    async with Client(
        name="my_account",
        session_string=SESSION_STRING,
        api_id=API_ID,
        api_hash=API_HASH
    ) as app:
        log.info("[INFO] Pyrogram connected using SESSION_STRING")
        while True:
            try:
                await asyncio.wait_for(bypass_cf(), timeout=15)
                token = await asyncio.to_thread(pm.update_auth, API_ID, API_HASH)

                all_gifts = await fetch_gifts(token)
                log.info(f"[SEARCH] Total pulled gifts: {len(all_gifts)}")

                filtered = filter_fresh_gifts(all_gifts, MIN_DROP_PERCENT, FRESH_SEC)

                for g in filtered:
                    msg = (
                        f"🎁 <b>{g.get('name','Unknown')}</b>\n"
                        f"💰 Price: {g.get('price')} TON\n"
                        f"🏷 Floor: {g.get('floor_price')} TON\n"
                        f"💸 Drop: {g.get('drop_percent')}%\n"
                        f"🌑 BG: {g.get('backdrop')}\n"
                        f"🔗 <a href='{g.get('photo_url','')}'>Open</a>"
                    )
                    await app.send_message(CHANNEL, msg, disable_web_page_preview=False)
                    log.info(f"[SEND] {g.get('name')} @ {g.get('price')} TON")
                    await asyncio.sleep(random.uniform(0.5, 1.3))

                interval = random.randint(*CHECK_INTERVAL)
                log.info(f"[WAIT] Next check in {interval} seconds...")
                await asyncio.sleep(interval)

            except asyncio.TimeoutError:
                log.warning("[TIMEOUT] Playwright bypass took too long, retrying...")
            except Exception as e:
                log.error(f"[ERROR] {e}, retrying in 30 sec...")
                await asyncio.sleep(30)

# --- Entry point ---
if __name__ == "__main__":
    asyncio.run(monitor_loop())
