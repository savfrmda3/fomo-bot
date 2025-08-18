# main.py
import asyncio
import random
import time
import os
import pickle
import logging
from pyrogram import Client
from pyrogram.errors import Unauthorized
from playwright.async_api import async_playwright
import portalsmp as pm

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- ENV ---
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
BOT_TOKEN      = os.environ.get("BOT_TOKEN", "").strip()
API_ID         = int(os.environ["API_ID"])
API_HASH       = os.environ["API_HASH"]
CHANNEL        = os.environ["CHANNEL"]

MIN_DROP_PERCENT = int(os.environ.get("MIN_DROP_PERCENT", 10))
BATCH_SIZE       = int(os.environ.get("BATCH_SIZE", 200))
MAX_GIFTS        = int(os.environ.get("MAX_GIFTS", 5000))
CHECK_INTERVAL   = (int(os.environ.get("CHECK_MIN", 60)), int(os.environ.get("CHECK_MAX", 120)))
FRESH_SEC        = int(os.environ.get("FRESH_SEC", 60))

os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "1"

# --- Seen IDs ---
SEEN_FILE = 'seen_ids.pickle'
seen_ids = set()
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, 'rb') as f:
        seen_ids = pickle.load(f)

def save_seen_ids():
    with open(SEEN_FILE, 'wb') as f:
        pickle.dump(seen_ids, f)

# --- Telegram Client ---
def make_client(use_bot=False):
    if not use_bot and SESSION_STRING and len(SESSION_STRING) > 100 and SESSION_STRING.startswith(("BA","CA","DA")):
        return Client(
            name="user_session",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING
        )
    elif BOT_TOKEN:
        return Client(
            name="bot_session",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
    else:
        raise RuntimeError("Нет ни SESSION_STRING, ни BOT_TOKEN")

# --- Cloudflare bypass ---
async def bypass_cf():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20A5346a TelegramBot/8.0"
        ))
        page = await ctx.new_page()
        await page.goto("https://portals-market.com", wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(3, 6))
        for _ in range(random.randint(2, 5)):
            await page.mouse.wheel(0, random.randint(300, 700))
            await asyncio.sleep(random.uniform(0.3, 1.0))
        await browser.close()
        logging.info("[CF] Bypass done")

# --- Filter fresh gifts ---
def filter_fresh_gifts(items, min_drop, seen, fresh_sec=60):
    out, now = [], time.time()
    for g in items:
        gid = g.get("id") or g.get("token_id")
        if not gid or gid in seen:
            continue
        listed_at = g.get("listed_at")
        if not listed_at:
            continue
        try:
            listed_ts = float(listed_at)
        except ValueError:
            try:
                listed_ts = time.mktime(time.strptime(str(listed_at).split(".")[0], "%Y-%m-%dT%H:%M:%S"))
            except ValueError:
                logging.warning(f"[FILTER] Invalid listed_at: {listed_at}")
                continue
        if now - listed_ts > fresh_sec:
            continue
        try:
            price = float(str(g.get("price",0)).replace("~","").strip())
            floor = float(str(g.get("floor_price",0)).replace("~","").strip())
        except ValueError:
            logging.warning(f"[FILTER] Invalid price/floor: {g.get('price')} / {g.get('floor_price')}")
            continue
        drop_percent = 100*(1-price/floor) if floor>0 else 0
        if drop_percent >= min_drop:
            g["drop_percent"] = round(drop_percent,1)
            out.append(g)
            seen.add(gid)
    logging.info(f"[FILTER] {len(items)} gifts -> {len(out)} fresh gifts")
    return out

# --- One monitoring cycle ---
async def one_cycle(app):
    await bypass_cf()
    token = await pm.update_auth(API_ID, API_HASH, SESSION_STRING)
    all_gifts = []
    for offset in range(0, MAX_GIFTS, BATCH_SIZE):
        try:
            batch = pm.marketActivity(authData=token, limit=BATCH_SIZE, offset=offset)
            if not batch:
                break
            all_gifts.extend(batch)
        except Exception as e:
            logging.error(f"[SEARCH ERROR] at offset {offset}: {e}")
            break
    logging.info(f"[SEARCH] Total pulled gifts: {len(all_gifts)}")
    filtered = filter_fresh_gifts(all_gifts, MIN_DROP_PERCENT, seen_ids, FRESH_SEC)
    for g in filtered:
        msg = (
            f"🎁 <b>{g.get('name','Unknown')}</b>\n"
            f"💰 Price: {g.get('price')} TON\n"
            f"🏷 Floor: {g.get('floor_price')} TON\n"
            f"💸 Drop: {g.get('drop_percent')}%\n"
            f"🌑 BG: {g.get('backdrop')}\n"
            f"🔗 <a href='{g.get('photo_url','')}'>Open</a>"
        )
        try:
            await app.send_message(CHANNEL, msg, disable_web_page_preview=False)
            logging.info(f"[SEND] {g.get('name')} @ {g.get('price')} TON")
        except Exception as e:
            logging.error(f"[SEND ERROR] {e}")
        await asyncio.sleep(random.uniform(0.5,1.3))
    save_seen_ids()

# --- Monitoring loop ---
async def monitor_loop():
    use_bot = False
    while True:
        cli = make_client(use_bot=use_bot)
        try:
            async with cli as app:
                me = await app.get_me()
                logging.info(f"[TG] Connected as @{getattr(me,'username',me.id)}")
                await one_cycle(app)
                interval = random.randint(*CHECK_INTERVAL)
                logging.info(f"[WAIT] Next check in {interval} sec...")
                await asyncio.sleep(interval)
        except Unauthorized as e:
            logging.error(f"[AUTH] {e}. Switching to BOT_TOKEN if available.")
            if not BOT_TOKEN:
                raise
            use_bot = True
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"[ERROR] {e}, retrying in 30 sec...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
