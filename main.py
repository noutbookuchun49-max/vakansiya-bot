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

# Kuzatiladigan kanallar
CHANNELS = [
    "@iivuz",
    "@vakansyuz",
    "@mahalladosh_tv",
    "@militsiya_102",
    "@militsiya_live",
    "@vacancy_argos"
]

# GitHub papkasidan mos rasmni topish
def find_image_by_prefix(prefix):
    for filename in os.listdir("."):
        if filename.lower().startswith(prefix.lower()) and filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            return filename
    return None

# Post matniga qarab GitHub'dagi mos rasmni tanlash
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
    # UserClient orqali kanallarni o'qiymiz
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    # BotClient orqali target kanalga post joylaymiz
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)
    
    await user_client.start()
    await bot_client.start(bot_token=BOT_TOKEN)

    for channel in CHANNELS:
        try:
            # MUHIM: Xabarlar user_client orqali o'qiladi!
            async for message in user_client.iter_messages(channel, limit=10):
                post_text = message.text or message.caption or ""
                
                if post_text.strip():
                    image_file = get_matching_image(post_text)
                    
                    if image_file and os.path.exists(image_file):
                        await bot_client.send_file(TARGET_CHANNEL, file=image_file, caption=post_text)
                    else:
                        await bot_client.send_message(TARGET_CHANNEL, post_text)
                        
                    print(f"-> {channel} kanalidan post joylandi!")
                    await asyncio.sleep(2)
                    break 
        except Exception as e:
            print(f"{channel} xatosi: {e}")

    await user_client.disconnect()
    await bot_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
