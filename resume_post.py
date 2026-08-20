import os
import sys
from telethon import TelegramClient
from telethon.tl.custom import Button

API_ID_RAW = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")

missing = [n for n, v in [
    ("TELEGRAM_API_ID", API_ID_RAW), ("TELEGRAM_API_HASH", API_HASH),
    ("BOT_TOKEN", BOT_TOKEN), ("TARGET_CHANNEL", TARGET_CHANNEL)
] if not v]
if missing:
    print(f"CRITICAL XATO: Secrets topilmadi: {', '.join(missing)}")
    sys.exit(1)

API_ID = int(API_ID_RAW)
RESUME_LINK = "https://t.me/rezumekerakmi"
MAX_CAPTION_LEN = 1024
MAX_TEXT_LEN = 4096


def find_image_by_prefix(prefix):
    for filename in os.listdir("."):
        if filename.lower().startswith(prefix.lower()) and filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            return filename
    return None


def trim_caption(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit - 3].rstrip() + "..."


RESUME_TEXT = """📄 REZYUME NIMA VA NIMA UCHUN KERAK?
🤔 Ishga topshirayotganda sizdan rezyume so'rashdimi? Unda rezyume nima ekanini bilishingiz kerak!
📌 Rezyume (CV) — bu siz haqingizdagi qisqa ma'lumotnoma. Unda ish beruvchi sizning ma'lumotingiz, ish tajribangiz, kasbingiz, ko'nikmalaringiz va boshqa muhim ma'lumotlaringiz bilan tanishadi.
🎯 Nima uchun rezyume kerak?
🔹 Ish beruvchi siz haqingizda dastlabki ma'lumotni oladi
🔹 Sizning tajriba va ko'nikmalaringizni ko'rsatadi
🔹 Qaysi lavozimga mos kelishingizni baholashga yordam beradi
🔹 Suhbatga chaqirilish imkoniyatingizni oshiradi
❌ Rezyume bo'lmasa nima bo'ladi?
Ba'zi tashkilot va kompaniyalar vakansiyaga ariza topshirishda rezyumeni majburiy talab qiladi. Rezyume bo'lmasa, arizangiz qabul qilinmasligi yoki siz boshqa nomzodlardan ortda qolishingiz mumkin.
⚠️ Oddiy yozilgan yoki xatolarga to'la rezyume ham imkoniyatingizga ta'sir qilishi mumkin.
✨ Yaxshi tayyorlangan rezyume — ish topish yo'lidagi birinchi qadam!
📄 REZYUME KERAKMI?
Rezyume tayyorlashni bilmayapsizmi yoki professional rezyume kerakmi?
🤝 Biz sizga yordam beramiz!
👉 @rezumekerakmi
📢 Davlat vakansiyalarini kuzatib boring:
👉 @davlat_vakansiyalar
#Rezyume #CV #Ish #Vakansiya #DavlatIshi #IshQidirish"""


async def main():
    client = TelegramClient('bot_session', API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)

    image_path = find_image_by_prefix("8")
    buttons = [Button.url("📄 REZYUME KERAKMI?", RESUME_LINK)]

    if image_path and os.path.exists(image_path):
        caption = trim_caption(RESUME_TEXT, MAX_CAPTION_LEN)
        await client.send_file(TARGET_CHANNEL, file=image_path, caption=caption, buttons=buttons)
    else:
        text = trim_caption(RESUME_TEXT, MAX_TEXT_LEN)
        await client.send_message(TARGET_CHANNEL, text, buttons=buttons)

    print("Rezyume posti yuborildi.")
    await client.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
