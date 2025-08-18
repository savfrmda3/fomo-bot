# main.py
import os
import time
import random
import pickle
import logging
import asyncio
from pyrogram import Client
import portalsmp as pm
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- ENV ---
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()
BOT_TOKEN      = os.environ.get("BOT_TOKEN", "").strip()
API_ID         = int(os.environ["API_ID"])
API_HASH       = os.environ["API_HASH"]
CHANNEL        = os.environ["CHANNEL"]

MIN_DROP_PERCENT = int(os.environ.get("MIN_DROP_PERCENT", 10))
SEEN_FILE = "seen_ids.pickle"
seen_ids = set()
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "rb") as f:
        seen_ids = pickle.load(f)

def save_seen_ids():
    with open(SEEN_FILE, "wb") as f:
        pickle.dump(seen_ids, f)

def make_client():
    if SESSION_STRING and len(SESSION_STRING) > 100:
        return Client(name="user_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
    elif BOT_TOKEN:
        return Client(name="bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    else:
        raise RuntimeError("Нет SESSION_STRING или BOT_TOKEN")

async def bypass_cf():
    """Имитация поведения пользователя через Playwright для обхода Cloudflare"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20A5346a TelegramBot/8.0"
        ))
        page = await context.new_page()
        await page.goto("https://portals-market.com", wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(2, 5))
        for _ in range(random.randint(2, 5)):
            await page.mouse.wheel(0, random.randint(300, 700))
            await asyncio.sleep(random.uniform(0.3, 1.0))
        await browser.close()
        logging.info("[CF] Bypass done")

async def fetch_gifts():
    """Используем portalsmp для получения activity"""
    try:
        gifts = pm.marketActivity()
        logging.info(f"[PORTALSMP] Pulled {len(gifts)} gifts")
        return gifts
    except Exception as e:
        logging.error(f"[PORTALSMP ERROR] {e}")
        return []

def filter_gifts(items):
    out = []
    for g in items:
        gid = g.get("id")
        if not gid or gid in seen_ids:
            continue
        price = g.get("price") or 0
        floor = g.get("floor") or 0
        drop_percent = 100*(1-price/floor) if floor>0 else 0
        if drop_percent >= MIN_DROP_PERCENT:
            g["drop_percent"] = round(drop_percent,1)
            out.append(g)
            seen_ids.add(gid)
    logging.info(f"[FILTER] {len(items)} gifts -> {len(out)} fresh gifts")
    return out

async def one_cycle(app):
    await bypass_cf()
    gifts = await fetch_gifts()
    filtered = filter_gifts(gifts)
    for g in filtered:
        msg = (
            f"🎁 <b>{g.get('name')}</b>\n"
            f"💰 Price: {g.get('price')} TON\n"
            f"🏷 Floor: {g.get('floor')} TON\n"
            f"💸 Drop: {g.get('drop_percent')}%\n"
            f"🌑 BG: {g.get('backdrop')}\n"
            f"🔗 <a href='{g.get('link')}'>Open</a>"
        )
        try:
            await app.send_message(CHANNEL, msg, disable_web_page_preview=False)
            await asyncio.sleep(random.uniform(0.5,1.3))
        except Exception as e:
            logging.error(f"[SEND ERROR] {e}")
    save_seen_ids()

async def monitor_loop():
    cli = make_client()
    async with cli as app:
        while True:
            try:
                me = await app.get_me()
                logging.info(f"[TG] Connected as @{getattr(me,'username',me.id)}")
                await one_cycle(app)
                interval = random.randint(60, 120)
                logging.info(f"[WAIT] Next check in {interval} sec...")
                await asyncio.sleep(interval)
            except Exception as e:
                logging.error(f"[LOOP ERROR] {e}")
                await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
