import asyncio
import random
import time
import os
import sys
from pyrogram import Client
from playwright.async_api import async_playwright
import portalsmp as pm

# --- Загрузка и проверка переменных окружения ---
def get_env_var(name, default=None, cast=str):
    val = os.environ.get(name, default)
    if val is None:
        sys.exit(f"[ERROR] Переменная окружения {name} не задана!")
    return cast(val) if cast else val

SESSION_STRING = os.environ.get("SESSION_STRING", "").replace("\n", "").strip()
if not SESSION_STRING:
    sys.exit("[ERROR] SESSION_STRING пустой или некорректный — проверь переменные Railway!")

API_ID = get_env_var("API_ID", cast=int)
API_HASH = get_env_var("API_HASH")
CHANNEL = get_env_var("CHANNEL")

MIN_DROP_PERCENT = get_env_var("MIN_DROP_PERCENT", 10, int)
BATCH_SIZE = get_env_var("BATCH_SIZE", 200, int)
MAX_GIFTS = get_env_var("MAX_GIFTS", 5000, int)
CHECK_INTERVAL = (
    get_env_var("CHECK_MIN", 60, int),
    get_env_var("CHECK_MAX", 120, int)
)
FRESH_SEC = get_env_var("FRESH_SEC", 60, int)

seen_ids = set()

# --- Игнорируем проверки хоста Playwright на Railway ---
os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "1"

# --- Playwright обход Cloudflare ---
async def bypass_cf():
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
        await browser.close()
        print("[CF] Bypass done")

# --- Фильтр свежих листингов ---
def filter_fresh_gifts(items: list, min_drop: float, seen: set, fresh_sec=60):
    out = []
    now = time.time()
    for g in items:
        gid = g.get("id") or g.get("token_id")
        if not gid or gid in seen:
            continue
        listed_at = g.get("listed_at")
        if not listed_at:
            continue
        listed_ts = None
        try:
            if isinstance(listed_at, (int, float)):
                listed_ts = float(listed_at)
            elif isinstance(listed_at, str):
                try:
                    listed_ts = time.mktime(time.strptime(listed_at.split(".")[0], "%Y-%m-%dT%H:%M:%S"))
                except:
                    listed_ts = float(listed_at)
        except:
            continue
        if not listed_ts or now - listed_ts > fresh_sec:
            continue
        try:
            price = float(str(g.get("price", 0)).replace("~", "").strip())
            floor = float(str(g.get("floor_price", 0)).replace("~", "").strip())
        except:
            continue
        drop_percent = 100 * (1 - price / floor) if floor > 0 else 0
        if drop_percent >= min_drop:
            g['drop_percent'] = round(drop_percent, 1)
            out.append(g)
            seen.add(gid)
    print(f"[FILTER] {len(items)} gifts -> {len(out)} fresh gifts")
    return out

# --- Основной цикл мониторинга ---
async def monitor_loop():
    async with Client(
        name="my_account",
        session_string=SESSION_STRING,
        api_id=API_ID,
        api_hash=API_HASH
    ) as app:
        me = await app.get_me()
        print(f"[START] Авторизован как: {me.first_name} (id: {me.id})")

        while True:
            try:
                await bypass_cf()
                token = await pm.update_auth(API_ID, API_HASH)

                all_gifts = []
                for offset in range(0, MAX_GIFTS, BATCH_SIZE):
                    batch = pm.search(sort="price_asc", limit=BATCH_SIZE, offset=offset, authData=token)
                    if not batch:
                        break
                    all_gifts.extend(batch)
                print(f"[SEARCH] Total pulled gifts: {len(all_gifts)}")

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
                    await app.send_message(CHANNEL, msg, disable_web_page_preview=False)
                    print(f"[SEND] {g.get('name')} @ {g.get('price')} TON")
                    await asyncio.sleep(random.uniform(0.5, 1.3))

                interval = random.randint(*CHECK_INTERVAL)
                print(f"[WAIT] Next check in {interval} seconds...")
                await asyncio.sleep(interval)

            except Exception as e:
                print(f"[ERROR] {e}, retrying in 30 sec...")
                await asyncio.sleep(30)

# --- Запуск ---
if __name__ == "__main__":
    asyncio.run(monitor_loop())
