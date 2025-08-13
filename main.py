from pyrogram import Client
import os
import asyncio

# Вставь сюда свою строку сессии и API данные
SESSION_STRING = os.environ.get("SESSION_STRING", "твой_session_string")
API_ID = int(os.environ.get("API_ID", 123456))
API_HASH = os.environ.get("API_HASH", "your_api_hash")

async def test_session():
    try:
        async with Client(
            name="check_session",
            session_string=SESSION_STRING,
            api_id=API_ID,
            api_hash=API_HASH
        ) as app:
            me = await app.get_me()
            print(f"[OK] Session is valid! Logged in as: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"[ERROR] Session failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_session())
