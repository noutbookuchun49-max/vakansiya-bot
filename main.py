import os
import sys
import asyncio
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

# Environment variables va ularning mavjudligini tekshirish
API_ID_RAW = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION", "").strip()

missing_env = []
if not API_ID_RAW: missing_env.append("TELEGRAM_API_ID")
if not API_HASH: missing_env.append("TELEGRAM_API_HASH")
if not TARGET_CHANNEL: missing_env.append("TARGET_CHANNEL")
if not SESSION_STRING: missing_env.append("TELEGRAM_SESSION")

if missing_env:
    print(f"CRITICAL XATO: Quyidagi Secrets topilmadi: {', '.join(missing_env)}")
    sys.exit(1)

API_ID = int(API_ID_RAW)

# Kuzatiladigan kanallar (ID raqamlari orqali)
CHANNELS = [
    -1001121935460, # @iivuz
    -1002887232365, # @vakansyuz
    -1002362638976, # @mahalladosh_tv
    -1001565245426, # @militsiya_102
    -1001796150117, # @militsiya_live
    -1001316196272  # @vacancy_argos
]

def find_image_by_prefix(prefix):
    for filename in os.listdir("."):
        if filename.lower().startswith(prefix.lower()) and filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            return filename
    return None

def get_matching_image(text):
    text_lower = text.lower() if text else ""
    if any(word in text_lower for word in ["iib", "militsiya", "patrul", "qo'riqlash", "soqchi", "oxrana", "ichki ishlar", "akademiya", "102"]):
        return find_image_by_prefix("Police_officer")
    elif any(word in text_lower for word in ["bank", "kassa", "kassir", "moliya", "buxgalter"]):
        return find_image_by_prefix("Bank_employee")
    elif any(word in text_lower for word in ["oshpaz", "povar", "oshxona", "restoran"]):
        return find_image_by_prefix("Chef_plating")
    elif any(word in text_lower for word in ["farrosh", "tozalik", "uborka"]):
        return find_image_by_prefix("Cleaner_cleaning")
    elif any(word in text_lower for word in ["qurilish", "prorab", "ustoxona"]):
        return find_image_by_prefix("Construction_worker")
    elif any(word in text_lower for word in ["shifokor", "vrach", "hamshira", "tibbiyot"]):
        return find_image_by_prefix("Doctor_smiling")
    elif any(word in text_lower for word in ["yurist", "advokat", "huquq"]):
        return find_image_by_prefix("Lawyer_standing")
    elif any(word in text_lower for word in ["sotuvchi", "magazin", "do'kon"]):
        return find_image_by_prefix("Shop_seller")
    elif any(word in text_lower for word in ["dasturchi", "python", "it", "web"]):
        return find_image_by_prefix("Software_developer")
    elif any(word in text_lower for word in ["o'qituvchi", "ustoz", "pedagog"]):
        return find_image_by_prefix("Teacher_explaining")
    elif any(word in text_lower for word in ["haydovchi", "shofyor", "dostavka"]):
        return find_image_by_prefix("Truck_driver")
    elif any(word in text_lower for word in ["operator", "call-center"]):
        return find_image_by_prefix("Operator_working")
    return find_image_by_prefix("7")

# Message matnini xavfsiz olish funksiyasi
def extract_message_text(message) -> str:
    text = getattr(message, 'message', None) or getattr(message, 'text', None) or getattr(message, 'caption', None) or ""
    return str(text).strip()

async def main():
    print("Telegram client ishga tushmoqda...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        await client.start()
        print("Telegram klient muvaffaqiyatli ulandi.")
    except Exception as e:
        print(f"CRITICAL XATO: Telegram klientga ulanib bo'lmadi! Details: {type(e).__name__}: {e}")
        return

    start_date = datetime(2026, 8, 18, tzinfo=timezone.utc)

    for ch in CHANNELS:
        print(f"\n--- Kanal tekshirilmoqda: {ch} ---")
        
        try:
            entity = await client.get_entity(ch)
            count = 0
            
            async for message in client.iter_messages(entity, limit=15):
                if message.date >= start_date:
                    post_text = extract_message_text(message)
                    
                    if post_text:
                        github_image = get_matching_image(post_text)
                        
                        if github_image and os.path.exists(github_image):
                            await client.send_file(TARGET_CHANNEL, file=github_image, caption=post_text)
                        else:
                            await client.send_message(TARGET_CHANNEL, post_text)
                            
                        count += 1
                        print(f"-> {ch} kanalidan post joylandi. Rasm: {github_image}")
                        await asyncio.sleep(2)
                        
            print(f"Xulosa: {ch} kanalidan {count} ta post olindi.")

        except Exception as e:
            print(f"XATO [{ch}]: {type(e).__name__} - {e}")

    await client.disconnect()
    print("\nJarayon yakunlandi va client uzildi.")

if __name__ == "__main__":
    asyncio.run(main())
