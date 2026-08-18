import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Environment variables
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION")

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
    # User Client — kanallarni o'qish uchun
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    # Bot Client — o'zingizning kanalingizga yuborish uchun
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)
    
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    
    print("Muvaffaqiyatli ulandi!")

    for channel in CHANNELS:
        print(f"Kanal tekshirilmoqda: {channel}")
        try:
            async for message in user_client.iter_messages(channel, limit=3):
                if message.text:
                    await bot_client.send_message(TARGET_CHANNEL, message.text)
                    print(f"-> {channel} kanalidan post yuborildi!")
                    break 
        except Exception as e:
            print(f"{channel} kanalida xatolik: {e}")

    await user_client.disconnect()
    await bot_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
