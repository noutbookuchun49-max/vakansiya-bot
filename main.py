import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")

SOURCE_CHANNELS = [
    '@iivuz',
    '@vakansyuz',
    '@mahalladosh_tv',
    '@militsiya_102',
    '@militsiya_live',
    '@vacancy_argos'
]

DB_FILE = 'posted_ids.json'

def get_matching_image(text):
    """Matnga qarab repositoriyadagi mos rasm faylini topadi"""
    txt = text.lower()
    all_files = os.listdir('.')
    prefix = 'Office_worker_sitting_at'
    
    if any(k in txt for k in ['iib', 'iiv', 'militsiya', 'politsiya', 'patrul', 'tadbirlar', 'qo\'riqlash']):
        prefix = 'Police_officer_standing_near'
    elif any(k in txt for k in ['o\'qituvchi', 'pedagog', 'maktab', 'dars', 'ta\'lim', 'tarbiyachi', 'repetitor']):
        prefix = 'Teacher_explaining_lesson_at'
    elif any(k in txt for k in ['shifokor', 'vrach', 'hamshira', 'tibbiyot', 'med', 'doktor', 'klinika', 'dorixona']):
        prefix = 'Doctor_smiling_in_hospital_hallway'
    elif any(k in txt for k in ['dasturchi', 'developer', 'python', 'php', 'frontend', 'backend', 'it ', 'kompyuter', 'smm', 'dizayner']):
        prefix = 'Software_developer_coding_on'
    elif any(k in txt for k in ['bank', 'moliya', 'buxgalter', 'gaznachilik', 'kassa', 'kassir', 'kredit']):
        prefix = 'Bank_employee_assisting_client'
    elif any(k in txt for k in ['zavod', 'sekh', 'fabrika', 'ishlab chiqarish', 'stanok', 'sex', 'texnik']):
        prefix = 'Worker_operating_manufacturing'
    elif any(k in txt for k in ['yurist', 'advokat', 'sudya', 'huquq', 'notarius', 'yuriskonsult']):
        prefix = 'Lawyer_standing_in_law_office'
    elif any(k in txt for k in ['sotuvchi', 'savdo', 'do\'kon', 'market', 'administrator', 'konsultant']):
        prefix = 'Shop_seller_arranging_grocery'
    elif any(k in txt for k in ['haydovchi', 'voditel', 'dostavka', 'yetkazib', 'taksi', 'moshina']):
        prefix = 'Truck_driver_smiling_on_highway'
    elif any(k in txt for k in ['oshpaz', 'povar', 'fastfood', 'oshxona', 'restoran', 'kafe', 'pitsa', 'ofitsiant']):
        prefix = 'Chef_plating_dish_in_kitchen'
    elif any(k in txt for k in ['qurilish', 'prorab', 'g\'isht', 'stroyka', 'payvandchi', 'svarchik', 'usta']):
        prefix = 'Construction_worker_working_on'
    elif any(k in txt for k in ['tozalash', 'uborka', 'klining', 'farrosh']):
        prefix = 'Cleaner_cleaning_commercial'
    elif any(k in txt for k in ['operator', 'call-center', 'muloqot', 'qo\'ng\'iroq']):
        prefix = 'Operator_working_on_computer'
    elif any(k in txt for k in ['ombor', 'sklad', 'gruzchik', 'yuklovchi']):
        prefix = 'Worker_checking_inventory'

    for f in all_files:
        if f.startswith(prefix):
            return f
            
    if os.path.exists('7.jpg'):
        return '7.jpg'
    return None

def load_posted_ids():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            print(f"Baza faylini o'qishda xato: {e}")
            return set()
    return set()

def save_posted_ids(posted_ids):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(posted_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Baza fayliga saqlashda xato: {e}")

async def main():
    posted_ids = load_posted_ids()
    bot = Bot(token=BOT_TOKEN)
    
    # Userbot sifatida ulanish uchun StringSession ishlatiladi
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await user_client.start()
    
    for channel in SOURCE_CHANNELS:
        try:
            print(f"Kanal tekshirilmoqda: {channel}")
            # Userbot kanaldagi postlar tarixini o'qiydi
            messages = await user_client.get_messages(channel, limit=30)
            
            for msg in reversed(messages):
                post_identifier = f"{channel}_{msg.id}"
                post_text = msg.text or msg.caption
                
                if post_identifier not in posted_ids and post_text:
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
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📄 Rezume kerakmi?", url="https://t.me/rezyume_tayyorlasht_bot")]
                    ])
                    
                    image_file = get_matching_image(post_text)
                    
                    if image_file and os.path.exists(image_file):
                        with open(image_file, 'rb') as photo_file:
                            await bot.send_photo(
                                chat_id=TARGET_CHANNEL,
                                photo=photo_file,
                                caption=full_caption,
                                reply_markup=keyboard
                            )
                    else:
                        await bot.send_message(
                            chat_id=TARGET_CHANNEL,
                            text=full_caption,
                            reply_markup=keyboard
                        )
                    
                    print(f"Yangi post joylandi ({image_file} bilan): {post_identifier}")
                    posted_ids.add(post_identifier)
                    save_posted_ids(posted_ids)
                    
                    await asyncio.sleep(3)
                    
        except Exception as e:
            print(f"{channel} kanalini o'qishda xatolik yuz berdi: {e}")

    await user_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
