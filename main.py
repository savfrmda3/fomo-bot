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

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- ENV ---
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
BOT_TOKEN      = os.environ.get("BOT_TOKEN", "").strip()
API_ID         = int(os.environ["API_ID"])
API_HASH       = os.environ["API_HASH"]
CHANNEL        = os.environ["CHANNEL"]

MIN_DROP_PERCENT = int(os.environ.get("MIN_DROP_PERCENT", 10))
FRESH_SEC        = int(os.environ.get("FRESH_SEC", 60))
CHECK_INTERVAL   = (int(os.environ.get("CHECK_MIN", 60)), int(os.environ.get("CHECK_MAX", 120)))

os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "1"

# --- SEEN PERSISTENCE ---
SEEN_FILE = "seen_ids.pickle"
seen_ids = set()
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "rb") as f:
        seen_ids = pickle.load(f)

def save_seen_ids():
    with open(SEEN_FILE, "wb") as f:
        pickle.dump(seen_ids, f)
        logging.info(f"[SEEN] Saved {len(seen_ids)} seen IDs")

# --- CLIENT ---
def make_client(use_bot=False):
    if not use_bot and SESSION_STRING and len(SESSION_STRING) > 100 and SESSION_STRING.startswith(("BA","CA","DA")):
        logging.info("[CLIENT] Using USERBOT session")
        return Client(name="user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
    elif BOT_TOKEN:
        logging.info("[CLIENT] Using BOT_TOKEN")
        return Client(name="bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    else:
        raise RuntimeError("Нет SESSION_STRING или BOT_TOKEN")

# --- XHR PARSER ---
async def get_activity_gifts_xhr(auth_token, max_wait=10):
    gifts = []
    try:
        async with async_playwright() as p:
            logging.info("[PLAYWRIGHT] Launching browser")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20A5346a TelegramBot/8.0"
            ))
            page = await context.new_page()
            await page.set_extra_http_headers({"Authorization": f"Bearer {auth_token}"})

            async def handle_response(response):
                try:
                    if "activity" in response.url and response.request.resource_type == "xhr":
                        data = await response.json()
                        for g in data.get("items", []):
                            gifts.append({
                                "id": g.get("id"),
                                "token_id": g.get("token_id"),
                                "name": g.get("name"),
                                "price": g.get("price"),
                                "floor_price": g.get("floor_price"),
                                "backdrop": g.get("backdrop_color"),
                                "photo_url": g.get("image_url"),
                                "listed_at": g.get("listed_at")
                            })
                        logging.info(f"[PLAYWRIGHT XHR] Got {len(data.get('items',[]))} items from response")
                except Exception as e:
                    logging.warning(f"[PLAYWRIGHT XHR] Response parse error: {e}")

            page.on("response", handle_response)
            logging.info("[PLAYWRIGHT] Opening activity page")
            await page.goto("https://portals-market.com/activity", wait_until="domcontentloaded")
            
            last_height = await page.evaluate("() => document.body.scrollHeight")
            start_time = time.time()
            while time.time() - start_time < max_wait:
                await page.mouse.wheel(0, random.randint(400, 800))
                await asyncio.sleep(random.uniform(0.8, 1.2))
                new_height = await page.evaluate("() => document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            await asyncio.sleep(2)
            await browser.close()
            logging.info(f"[PLAYWRIGHT XHR] Collected {len(gifts)} gifts total")
    except Exception as e:
        logging.error(f"[PLAYWRIGHT XHR] Failed: {e}")
    return gifts

# --- FILTER ---
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
        drop_percent = 100*(1 - price/floor) if floor>0 else 0
        if drop_percent >= min_drop:
            g["drop_percent"] = round(drop_percent,1)
            out.append(g)
            seen.add(gid)
    logging.info(f"[FILTER] {len(items)} gifts -> {len(out)} fresh gifts")
    return out

# --- ONE CYCLE ---
async def one_cycle(app):
    logging.info("[CYCLE] Starting cycle")
    token = await pm.update_auth(API_ID, API_HASH, SESSION_STRING)
    logging.info("[CYCLE] Auth updated")
    gifts = await get_activity_gifts_xhr(token)
    if not gifts:
        logging.info("[CYCLE] No gifts collected from activity")
    filtered = filter_fresh_gifts(gifts, MIN_DROP_PERCENT, seen_ids, FRESH_SEC)
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
        await asyncio.sleep(random.uniform(0.5, 1.3))
    save_seen_ids()
    logging.info("[CYCLE] Finished cycle")

# --- MONITOR LOOP ---
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
            logging.error(f"[AUTH] {e}, switching to BOT_TOKEN if available.")
            if not BOT_TOKEN:
                raise
            use_bot = True
            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"[ERROR] {e}, retrying in 30 sec...")
            await asyncio.sleep(30)

# --- RUN ---
if __name__ == "__main__":
    asyncio.run(monitor_loop())
