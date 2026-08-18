import os
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

# Environment variables
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION", "").strip()

# Kuzatiladigan kanallar
CHANNELS = [
    "@iivuz",
    "@vakansyuz",
    "@mahalladosh_tv",
    "@militsiya_102",
    "@militsiya_live",
    "@vacancy_argos"
]

def find_image_by_prefix(prefix):
    for filename in os.listdir("."):
        if filename.lower().startswith(prefix.lower()) and filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            return filename
    return None

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
        
    return find_image_by_prefix("7")

async def main():
    if not SESSION_STRING:
        print("XATO: TELEGRAM_SESSION kodi topilmadi!")
        return

    # Faqat User Client ishlatiladi
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    start_date = datetime(2026, 8, 18, tzinfo=timezone.utc)

    for channel in CHANNELS:
        try:
            async for message in client.iter_messages(channel, limit=15):
                if message.date >= start_date:
                    post_text = message.text or message.caption or ""
                    
                    if post_text.strip():
                        github_image = get_matching_image(post_text)
                        
                        if github_image and os.path.exists(github_image):
                            await client.send_file(TARGET_CHANNEL, file=github_image, caption=post_text)
                        else:
                            await client.send_message(TARGET_CHANNEL, post_text)
                        
                        print(f"-> {channel} kanalidan post jo'natildi!")
                        await asyncio.sleep(2)
        except Exception as e:
            print(f"{channel} xatosi: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
