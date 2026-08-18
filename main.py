import os
import asyncio
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

# Environment variables
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION")

# Kuzatiladigan kanallar
CHANNELS = [
    "@iivuz",
    "@vakansyuz",
    "@mahalladosh_tv",
    "@militsiya_102",
    "@militsiya_live",
    "@vacancy_argos"
]

# GitHub papkasidan kengaytmasi (.jpg/.jpeg) va nomidan qat'i nazar mos rasmni topish
def find_image_by_prefix(prefix):
    for filename in os.listdir("."):
        if filename.lower().startswith(prefix.lower()) and filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            return filename
    return None

# Matn mazmuniga qarab mos rasmni aniqlash
def get_matching_image(text):
    text_lower = text.lower() if text else ""
    
    if any(word in text_lower for word in ["iib", "militsiya", "patrul", "qo'riqlash", "soqchi", "oxrana", "ichki ishlar", "akademiya", "akademiyasiga", "102"]):
        return find_image_by_prefix("Police_officer")
    elif any(word in text_lower for word in ["bank", "kassa", "kassir", "moliya", "buxgalter", "kredit"]):
        return find_image_by_prefix("Bank_employee")
    elif any(word in text_lower for word in ["oshpaz", "povar", "oshxona", "restoran", "kafe"]):
        return find_image_by_prefix("Chef_plating")
    elif any(word in text_lower for word in ["farrosh", "tozalik", "uborka", "uborshitsa"]):
        return find_image_by_prefix("Cleaner_cleaning")
    elif any(word in text_lower for word in ["qurilish", "prorab", "ustoxona", "montaj"]):
        return find_image_by_prefix("Construction_worker")
    elif any(word in text_lower for word in ["shifokor", "vrach", "hamshira", "tibbiyot", "bolnitsa", "klinika", "dorixona"]):
        return find_image_by_prefix("Doctor_smiling")
    elif any(word in text_lower for word in ["yurist", "advokat", "huquq", "sud"]):
        return find_image_by_prefix("Lawyer_standing")
    elif any(word in text_lower for word in ["sotuvchi", "magazin", "do'kon", "supermarket", "prodavets"]):
        return find_image_by_prefix("Shop_seller")
    elif any(word in text_lower for word in ["dasturchi", "python", "it", "flutter", "web", "dasturlash"]):
        return find_image_by_prefix("Software_developer")
    elif any(word in text_lower for word in ["o'qituvchi", "ustoz", "pedagog", "maktab", "dars"]):
        return find_image_by_prefix("Teacher_explaining")
    elif any(word in text_lower for word in ["haydovchi", "shofyor", "voditel", "dostavka", "yuk"]):
        return find_image_by_prefix("Truck_driver")
    elif any(word in text_lower for word in ["operator", "call-center", "dispetcher"]):
        return find_image_by_prefix("Operator_working")
        
    # Agarda biror maxsus sohaga tushmasa — zaxiradagi 7.jpg rasmini oladi
    return find_image_by_prefix("7")

async def main():
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)
    
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)
    
    print("Muvaffaqiyatli ulandi! 18-avgust postlari izlanmoqda...")

    # Toshkent vaqti bo'yicha 18-avgust sanasini belgilaymiz (UTC+5)
    target_date = datetime(2026, 8, 18).date()

    for channel in CHANNELS:
        try:
            async for message in user_client.iter_messages(channel, limit=30):
                # Post yaratilgan vaqtni mahalliy (Toshkent) vaqtga o'tkazish
                msg_date = message.date.astimezone(timezone(timedelta(hours=5))).date()
                
                # Faqat 18-avgustda tushgan postlarni olamiz
                if msg_date == target_date:
                    post_text = message.text or message.caption or ""
                    
                    if post_text.strip():  # Bo'sh bo'lmagan matnlarni oladi
                        image_file = get_matching_image(post_text)
                        
                        if image_file and os.path.exists(image_file):
                            await bot_client.send_file(TARGET_CHANNEL, file=image_file, caption=post_text)
                            print(f"-> {channel} kanalidan 18-avgust posti {image_file} rasmi bilan yuborildi!")
                        else:
                            await bot_client.send_message(TARGET_CHANNEL, post_text)
                            print(f"-> {channel} kanalidan 18-avgust matni yuborildi.")
                        
                        await asyncio.sleep(2)  # Telegram spam blokirovkasiga tushmaslik uchun
        except Exception as e:
            print(f"{channel} kanalida xatolik: {e}")

    await user_client.disconnect()
    await bot_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
