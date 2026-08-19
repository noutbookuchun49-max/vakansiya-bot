import os
import sys
import asyncio
import traceback
from datetime import datetime, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# 1. Environment variables tekshiruvi
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

# Kuzatiladigan kanallar (Username yoki ID bo'lishi mumkin)
CHANNELS = [
    "iivuz",
    "vakansyuz",
    "mahalladosh_tv",
    "militsiya_102",
    "militsiya_live",
    "vacancy_argos"
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

def extract_message_text(message) -> str:
    text = getattr(message, 'message', None) or getattr(message, 'text', None) or getattr(message, 'caption', None) or ""
    return str(text).strip()

async def resolve_entity(client, identifier):
    """ Entity'ni topish uchun bir necha usul bilan urinish """
    # 1. Asl ko'rinishida urinish
    try:
        return await client.get_entity(identifier)
    except Exception:
        pass

    # 2. Agar @ yo'q bo'lsa, @ qo'shib urinish
    if isinstance(identifier, str) and not identifier.startswith("@"):
        try:
            return await client.get_entity(f"@{identifier}")
        except Exception:
            pass

    # 3. Dialoglar orasidan qidirish (keshni yangilaydi)
    async for dialog in client.iter_dialogs(limit=100):
        if str(dialog.id) == str(identifier) or dialog.name == identifier or getattr(dialog.entity, 'username', None) == str(identifier).replace("@", ""):
            return dialog.entity

    raise ValueError(f"Entity topilmadi: {identifier!r}")

async def send_with_retry(client, target, file=None, caption=None, text=None, message_to_forward=None):
    """ FloodWaitError holatida avtomatik kutib qayta yuborish """
    while True:
        try:
            if message_to_forward:
                await client.forward_messages(target, message_to_forward)
            elif file:
                await client.send_file(target, file=file, caption=caption)
            elif text:
                await client.send_message(target, text)
            break
        except FloodWaitError as e:
            print(f" FloodWait kutilmoqda: {e.seconds} soniya...")
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            print(f" Yuborishda xatolik: {e}")
            break

async def main():
    print("Telegram client ishga tushmoqda...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"Telegram klient ulandi: {me.first_name} (id={me.id}, @{me.username})")
    except Exception as e:
        print(f"CRITICAL XATO: Ulanishda xatolik: {e}")
        return

    start_date = datetime(2026, 8, 18, tzinfo=timezone.utc)

    for ch in CHANNELS:
        print(f"\n--- Kanal tekshirilmoqda: {ch!r} ---")
        try:
            entity = await resolve_entity(client, ch)
            count = 0
            
            async for message in client.iter_messages(entity, limit=15):
                if message.date >= start_date:
                    post_text = extract_message_text(message)
                    
                    if post_text:
                        github_image = get_matching_image(post_text)
                        if github_image and os.path.exists(github_image):
                            await send_with_retry(client, TARGET_CHANNEL, file=github_image, caption=post_text)
                        else:
                            await send_with_retry(client, TARGET_CHANNEL, text=post_text)
                        count += 1
                        print(f"-> {ch} kanalidan post joylandi. Rasm: {github_image}")
                    elif message.media:
                        # Matnsiz media bo'lsa forward qilish
                        await send_with_retry(client, TARGET_CHANNEL, message_to_forward=message)
                        count += 1
                        print(f"-> {ch} kanalidan media forward qilindi.")

                    await asyncio.sleep(2)
                        
            print(f"Xulosa: {ch} kanalidan {count} ta post olindi.")

        except Exception as e:
            print(f"XATO [{ch!r}]: {type(e).__name__} - {e}")
            traceback.print_exc()

    await client.disconnect()
    print("\nJarayon yakunlandi va client uzildi.")

if __name__ == "__main__":
    asyncio.run(main())
