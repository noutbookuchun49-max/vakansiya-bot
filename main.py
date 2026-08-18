import os
import re
import json
import urllib.parse
import requests
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")

# Kuzatiladigan kanallar
SOURCE_CHANNELS = [
    'iivuz',
    'vakansyuz',
    'mahalladosh_tv',
    'militsiya_102',
    'militsiya_live',
    'vacancy_argos'
]

DB_FILE = 'posted_ids.json'

def load_posted_ids():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_posted_ids(posted_ids):
    with open(DB_FILE, 'w') as f:
        json.dump(list(posted_ids), f)

def clean_and_format_text(text):
    if not text:
        return ""
    
    # Boshqa kanallarning havolalari va userlarini tozalash
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r't\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    header = "🏛 **DAVLAT ISHLARI BO'YICHA VAKANSIYA**\n\n"
    footer = f"\n\n📌 **Bizning kanal:** {TARGET_CHANNEL}"
    
    return header + text.strip() + footer

def generate_ai_image_url(text):
    text_lower = text.lower()
    
    if "iib" in text_lower or "ichki ishlar" in text_lower or "militsiya" in text_lower:
        prompt = "Uzbekistan police officer in official uniform, high quality, realistic photo"
    elif "ayol" in text_lower or "xotin-qiz" in text_lower:
        prompt = "Uzbek woman office worker, professional business attire, realistic portrait"
    elif "tibbiyot" in text_lower or "shifokor" in text_lower:
        prompt = "Uzbek doctor in medical white coat, professional photo"
    elif "maktab" in text_lower or "ta'lim" in text_lower:
        prompt = "Uzbekistan school teacher in classroom, realistic photo"
    else:
        prompt = "Government job vacancy poster background, modern office Uzbekistan, realistic"
        
    encoded_prompt = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true"

def send_to_channel(text, image_url):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📄 Rezume kerakmi?", "url": "https://t.me/rezumekerakmi"}
            ]
        ]
    }
    
    payload = {
        'chat_id': TARGET_CHANNEL,
        'photo': image_url,
        'caption': text,
        'parse_mode': 'Markdown',
        'reply_markup': json.dumps(reply_markup)
    }
    
    requests.post(url, data=payload)

def send_daily_info_post(posted_ids):
    """Har kuni ertalab rezume haqida ma'lumot beruvchi avto-post"""
    today_key = f"daily_info_{datetime.now().strftime('%Y-%m-%d')}"
    if today_key in posted_ids:
        return

    info_text = (
        "📄 **REZUME NIMA VA U NIMA UCHUN KERAK?**\n\n"
        "Ko'pchilik ish izlayotganlar *\"Oddiy ma'lumotnoma bo'lsa bo'ldiku\"* deb o'ylashadi. "
        "Lekin davlat tashkilotlari birinchi navbatda **rezumeyingizga** qarab baho beradi!\n\n"
        "💡 **Sifatli rezumeda nimalar bo me bo'lishi kerak:**\n"
        "1️⃣ Rasmiy va sifatli fotosurat\n"
        "2️⃣ Ma'lumotingiz va mutaxassisligingiz\n"
        "3️⃣ Ish tajribangiz va ko'nikmalaringiz\n\n"
        "⚠️ Sifatsiz va xato yozilgan rezume ishga kirish imkoniyatini keskin kamaytiradi!\n\n"
        "👉 Professional rezume tayyorlatish uchun tugmani bosing:"
    )
    
    image_url = "https://image.pollinations.ai/prompt/professional%20cv%20resume%20document%20on%20office%20desk?width=800&height=600&nologo=true"
    send_to_channel(info_text, image_url)
    posted_ids.add(today_key)

async def main():
    posted_ids = load_posted_ids()
    
    # Kunlik informatsion postni tekshirish
    send_daily_info_post(posted_ids)
    
    async with TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH) as client:
        for channel in SOURCE_CHANNELS:
            try:
                async for message in client.iter_messages(channel, limit=20):
                    msg_key = f"{channel}_{message.id}"
                    
                    if msg_key in posted_ids:
                        continue
                    
                    if message.text:
                        formatted_text = clean_and_format_text(message.text)
                        ai_image_url = generate_ai_image_url(formatted_text)
                        
                        send_to_channel(formatted_text, ai_image_url)
                        posted_ids.add(msg_key)
                        await asyncio.sleep(3)
            except Exception as e:
                print(f"Xatolik {channel} kanalida: {e}")
                
    save_posted_ids(posted_ids)

if __name__ == '__main__':
    asyncio.run(main())
