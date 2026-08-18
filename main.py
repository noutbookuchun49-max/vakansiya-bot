import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

# Secret'lardan olinadigan ma'lumotlar
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")

# Kuzatiladigan kanallar ro'yxati (@ belgisi bilan)
SOURCE_CHANNELS = [
    '@iivuz',
    '@vakansyuz',
    '@mahalladosh_tv',
    '@militsiya_102',
    '@militsiya_live',
    '@vacancy_argos'
]

DB_FILE = 'posted_ids.json'

def load_posted_ids():
    """Ilgari joylangan post ID'larini fayldan o'qish"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Baza faylini o'qishda xato: {e}")
            return set()
    return set()

def save_posted_ids(posted_ids):
    """Joylangan post ID'larini faylga saqlash"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(posted_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Baza fayliga saqlashda xato: {e}")

async def main():
    posted_ids = load_posted_ids()
    bot = Bot(token=BOT_TOKEN)
    
    # Telegram Userbot mijozini ishga tushirish
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        for channel in SOURCE_CHANNELS:
            try:
                print(f"Kanal tekshirilmoqda: {channel}")
                # Har bir kanaldan oxirgi 5 ta postni olish
                messages = await client.get_messages(channel, limit=5)
                
                for msg in reversed(messages):
                    post_identifier = f"{channel}_{msg.id}"
                    
                    # Agar ushbu post ilgari joylanmagan bo'lsa va matni bo'lsa
                    if post_identifier not in posted_ids and msg.text:
                        
                        # Matnni tayyorlash
                        post_text = msg.text
                        
                        # Pastki qismdagi tugma va reklama matni
                        caption_footer = (
                            "\n\n— — — — — — — — — — — — — — — —\n"
                            "Ko'pchilik ish izlayotganlar **\"Oddiy ma'lumotnoma bo'lsa bo'ldiku\"** "
                            "deb o'ylashadi. Lekin davlat tashkilotlari birinchi navbatda "
                            "rezumeyingizga qarab baho beradi!\n\n"
                            "💡 Sifatli rezumeda nimalar bo'lishi kerak:\n"
                            "1️⃣ Rasmiy va sifatli fotosurat\n"
                            "2️⃣ Ma'lumotingiz va mutaxassisligingiz\n"
                            "3️⃣ Ish tajribangiz va ko'nikmalaringiz\n\n"
                            "⚠️ Sifatsiz va xato yozilgan rezume ishga kirish imkoniyatini keskin kamaytiradi!\n\n"
                            "👉 Professional rezume tayyorlatish uchun tugmani bosing:"
                        )
                        
                        full_caption = post_text + caption_footer
                        
                        # Inline tugma yaratish
                        keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton("📄 Rezume kerakmi?", url="https://t.me/rezyume_tayyorlasht_bot")]
                        ])
                        
                        # Postni kanalga yuborish
                        if msg.photo:
                            photo_path = await msg.download_media()
                            with open(photo_path, 'rb') as photo_file:
                                await bot.send_photo(
                                    chat_id=TARGET_CHANNEL,
                                    photo=photo_file,
                                    caption=full_caption,
                                    parse_mode='Markdown',
                                    reply_markup=keyboard
                                )
                            if os.path.exists(photo_path):
                                os.remove(photo_path)
                        else:
                            await bot.send_message(
                                chat_id=TARGET_CHANNEL,
                                text=full_caption,
                                parse_mode='Markdown',
                                reply_markup=keyboard
                            )
                        
                        print(f"Yangi post joylandi: {post_identifier}")
                        posted_ids.add(post_identifier)
                        save_posted_ids(posted_ids)
                        
                        # Kanalga birdaniga spam bo'lmasligi uchun 5 soniya kutish
                        await asyncio.sleep(5)
                        
            except Exception as e:
                print(f"{channel} kanalini o'qishda xatolik yuz berdi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
