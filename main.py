import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Environment variables
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")

# Base64 padding xatosini oldini olish
raw_session = os.environ.get("TELEGRAM_SESSION", "").strip()
missing_padding = len(raw_session) % 4
if missing_padding:
    raw_session += '=' * (4 - missing_padding)
SESSION_STRING = raw_session

# Kuzatish kerak bo'lgan kanallar
CHANNELS = [
    "@iivuz",
    "@vakansyuz",
    "@mahalladosh_tv",
    "@militsiya_102",
    "@militsiya_live",
    "@vacancy_argos"
]

async def main():
    # User Client — kanallardan postlarni O'QISH uchun
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    # Bot Client — o'zingizning kanalingizga YUBORISH uchun
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)
    
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    
    print("Clientlar muvaffaqiyatli ishga tushdi.")

    for channel in CHANNELS:
        print(f"Kanal tekshirilmoqda: {channel}")
        try:
            # POSTLARNI USER CLIENT O'QIYDI (xatolik bermaydi)
            async for message in user_client.iter_messages(channel, limit=3):
                if message.text:
                    # Target kanalga BOT yuboradi
                    await bot_client.send_message(TARGET_CHANNEL, message.text)
                    print(f"-> {channel} kanalidan post yuborildi!")
                    break 
        except Exception as e:
            print(f"{channel} kanalini o'qishda xatolik yuz berdi: {e}")

    await user_client.disconnect()
    await bot_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
