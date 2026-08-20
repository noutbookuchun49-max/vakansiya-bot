import os
import re
import sys
import json
import asyncio
import traceback
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.custom import Button

# ============================================================
# 1. ENVIRONMENT VARIABLES
# ============================================================
API_ID_RAW = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
SESSION_STRING = os.environ.get("TELEGRAM_SESSION", "").strip()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL")
CHANNEL_TAG = os.environ.get("CHANNEL_TAG", "@davlat_vakansiyalar")

missing_env = []
if not API_ID_RAW: missing_env.append("TELEGRAM_API_ID")
if not API_HASH: missing_env.append("TELEGRAM_API_HASH")
if not SESSION_STRING: missing_env.append("TELEGRAM_SESSION")
if not BOT_TOKEN: missing_env.append("BOT_TOKEN")
if not TARGET_CHANNEL: missing_env.append("TARGET_CHANNEL")

if missing_env:
    print(f"CRITICAL XATO: Quyidagi Secrets topilmadi: {', '.join(missing_env)}")
    sys.exit(1)

API_ID = int(API_ID_RAW)

# ============================================================
# 2. KUZATILADIGAN KANALLAR  (militsiya_live OLIB TASHLANDI)
# ============================================================
CHANNELS = [
    "iivuz",
    "vakansyuz",
    "mahalladosh_tv",
    "militsiya_102",
    "vacancy_argos",
]

STATE_FILE = "posted_ids.json"
MAX_CAPTION_LEN = 1024   # Telegram rasm captioni uchun limit
MAX_TEXT_LEN = 4096      # Telegram matn xabari uchun limit

RESUME_LINK = "https://t.me/rezumekerakmi"


# ============================================================
# 3. HOLATNI SAQLASH (takrorlanishning oldini olish)
# ============================================================
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ============================================================
# 4. RASMNI TOPISH
# ============================================================
def find_image_by_prefix(prefix):
    for filename in os.listdir("."):
        if filename.lower().startswith(prefix.lower()) and filename.lower().endswith(('.jpeg', '.jpg', '.png')):
            return filename
    return None


def get_matching_image(text, channel_name):
    # vacancy_argos uchun DOIMIY rasm (7-prefiks)
    if channel_name == "vacancy_argos":
        return find_image_by_prefix("7")

    text_lower = text.lower() if text else ""
    if any(w in text_lower for w in ["iib", "militsiya", "patrul", "qo'riqlash", "soqchi", "oxrana", "ichki ishlar", "akademiya", "102"]):
        return find_image_by_prefix("Police_officer")
    elif any(w in text_lower for w in ["bank", "kassa", "kassir", "moliya", "buxgalter"]):
        return find_image_by_prefix("Bank_employee")
    elif any(w in text_lower for w in ["oshpaz", "povar", "oshxona", "restoran"]):
        return find_image_by_prefix("Chef_plating")
    elif any(w in text_lower for w in ["farrosh", "tozalik", "uborka"]):
        return find_image_by_prefix("Cleaner_cleaning")
    elif any(w in text_lower for w in ["qurilish", "prorab", "ustoxona"]):
        return find_image_by_prefix("Construction_worker")
    elif any(w in text_lower for w in ["shifokor", "vrach", "hamshira", "tibbiyot"]):
        return find_image_by_prefix("Doctor_smiling")
    elif any(w in text_lower for w in ["yurist", "advokat", "huquq"]):
        return find_image_by_prefix("Lawyer_standing")
    elif any(w in text_lower for w in ["sotuvchi", "magazin", "do'kon"]):
        return find_image_by_prefix("Shop_seller")
    elif any(w in text_lower for w in ["dasturchi", "python", "it", "web"]):
        return find_image_by_prefix("Software_developer")
    elif any(w in text_lower for w in ["o'qituvchi", "ustoz", "pedagog"]):
        return find_image_by_prefix("Teacher_explaining")
    elif any(w in text_lower for w in ["haydovchi", "shofyor", "dostavka"]):
        return find_image_by_prefix("Truck_driver")
    elif any(w in text_lower for w in ["operator", "call-center"]):
        return find_image_by_prefix("Operator_working")
    return find_image_by_prefix("7")


# ============================================================
# 5. XABAR MATNINI OLISH
# ============================================================
def extract_message_text(message) -> str:
    text = getattr(message, 'message', None) or getattr(message, 'text', None) or getattr(message, 'caption', None) or ""
    return str(text).strip()


# ============================================================
# 6. REKLAMA / VAKANSIYA EMASLARNI FILTRLASH  (ASOSIY MUAMMO)
# ============================================================
VACANCY_KEYWORDS = [
    "vakansiya", "ish o'rni", "ish o'rniga", "talab etiladi", "talab qilinadi",
    "ishga qabul", "qabul qilinadi", "ishga taklif", "xodim kerak", "xodim talab", "ishga oladi",
    "ishga olinadi", "maosh", "lavozim", "kerak:", "kerak.", "kerak!",
    "vakant", "ishga chaqiriladi", "ish beriladi", "штат", "требуется",
    "вакансия", "зарплата",
]

AD_KEYWORDS = [
    "sotiladi", "sotib oling", "sotib olish", "chegirma", "aksiya",
    "eng past narx", "arzon narxda", "reklama", "buyurtma bering",
    "yetkazib berish xizmati", "promo kod", "промокод", "скидка",
    "распродажа", "купить", "заказать", "доставка бесплатно",
    "obuna bo'ling", "kanalga qo'shiling", "kanalimizga a'zo",
]


def is_vacancy(text: str) -> bool:
    if not text or len(text.strip()) < 15:
        return False
    t = text.lower()
    has_vacancy_word = any(k in t for k in VACANCY_KEYWORDS)
    has_ad_word = any(k in t for k in AD_KEYWORDS)
    if has_ad_word and not has_vacancy_word:
        return False
    return has_vacancy_word


# ============================================================
# 7. BOSHQA KANAL BELGILARINI TOZALASH (@mention, obuna chaqiruvi)
# ============================================================
MENTION_RE = re.compile(r"@[A-Za-z0-9_]{4,}")
URL_RE = re.compile(r"https?://\S+")
NOISE_LINE_PATTERNS = [
    "obuna bo'ling", "kanalimiz", "kanalga qo'shiling", "manba:",
    "forwarded", "подпишись", "подписывайтесь", "наш канал",
]


def clean_source_text(text: str) -> str:
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        low = line.lower()
        if any(p in low for p in NOISE_LINE_PATTERNS):
            continue
        line = MENTION_RE.sub("", line)
        line = URL_RE.sub("", line)
        cleaned_lines.append(line.strip())
    return "\n".join(l for l in cleaned_lines if l)


# ============================================================
# 8. VILOYATLARNI ANIQLASH
# ============================================================
REGIONS = [
    "Toshkent shahri", "Toshkent viloyati", "Andijon", "Farg'ona", "Fargona",
    "Namangan", "Samarqand", "Buxoro", "Xorazm", "Navoiy", "Qashqadaryo",
    "Surxondaryo", "Sirdaryo", "Jizzax", "Qoraqalpog'iston",
]


def detect_region(text: str):
    for r in REGIONS:
        if r.lower() in text.lower():
            return r.upper()
    return None


# ============================================================
# 9. MAYDONLARNI MATNDAN AJRATIB OLISH
# ============================================================
FIELD_PATTERNS = {
    "org": [r"tashkilot[:\-]\s*(.+)", r"kompaniya[:\-]\s*(.+)", r"muassasa[:\-]\s*(.+)", r"korxona[:\-]\s*(.+)"],
    "position": [r"lavozim[:\-]\s*(.+)", r"vakansiya[:\-]\s*(.+)", r"kasb[:\-]\s*(.+)", r"ish o'rni[:\-]\s*(.+)"],
    "salary": [r"maosh[:\-]\s*(.+)", r"ish haqi[:\-]\s*(.+)", r"oylik[:\-]\s*(.+)"],
    "address": [r"manzil[:\-]\s*(.+)", r"joylashuv[:\-]\s*(.+)", r"address[:\-]\s*(.+)"],
    "education": [r"ma'?lumot[:\-]\s*(.+)", r"ta'?lim[:\-]\s*(.+)"],
    "experience": [r"tajriba[:\-]\s*(.+)", r"ish tajribasi[:\-]\s*(.+)"],
    "age": [r"yosh[:\-]\s*(.+)"],
    "extra_req": [r"qo'shimcha talab[:\-]\s*(.+)", r"talablar[:\-]\s*(.+)"],
    "deadline": [r"muddat[:\-]\s*(.+)", r"ariza.*muddat[:\-]\s*(.+)"],
}

PHONE_RE = re.compile(r"(\+?998\s?-?\d{2}\s?-?\d{3}\s?-?\d{2}\s?-?\d{2})")


def extract_field(text, keys, default="Berilmagan"):
    for pattern in FIELD_PATTERNS[keys]:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            val = val.split("\n")[0].strip(" .,-")
            val = MENTION_RE.sub("", val).strip()
            if val:
                return val[:200]
    return default


def extract_contact(text, default="Berilmagan"):
    m = PHONE_RE.search(text)
    if m:
        return m.group(1).strip()
    return default


# ============================================================
# 10. YAKUNIY POST SHABLONINI QURISH
# ============================================================
def build_vacancy_post(raw_text: str) -> str:
    cleaned = clean_source_text(raw_text)

    org = extract_field(cleaned, "org")
    position = extract_field(cleaned, "position")
    salary = extract_field(cleaned, "salary")
    address = extract_field(cleaned, "address")
    education = extract_field(cleaned, "education")
    experience = extract_field(cleaned, "experience")
    age = extract_field(cleaned, "age")
    extra_req = extract_field(cleaned, "extra_req")
    deadline = extract_field(cleaned, "deadline")
    contact = extract_contact(cleaned)

    region = detect_region(cleaned)
    header = "📢 YANGI VAKANSIYA"
    region_line = f"📍 {region}\n" if region else ""

    post = (
        f"{header}\n"
        f"{region_line}"
        f"🏢 Tashkilot: {org}\n"
        f"💼 Lavozim: {position}\n"
        f"💰 Maosh: {salary}\n"
        f"📌 Manzil: {address}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 TALABLAR\n"
        f"🎓 Ma'lumoti: {education}\n"
        f"💼 Ish tajribasi: {experience}\n"
        f"👤 Yosh: {age}\n"
        f"🗣 Qo'shimcha talablar: {extra_req}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 Ariza topshirish muddati: {deadline}\n"
        f"📞 Murojaat uchun: {contact}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔔 Yangi davlat vakansiyalarini o'tkazib yubormang!\n"
        f"📲 Kanalimizga obuna bo'ling:\n"
        f"👉 {CHANNEL_TAG}"
    )
    return post


def trim_caption(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit - 3].rstrip() + "..."


# ============================================================
# 11. YUBORISH (FloodWait bilan, tugma bilan, forward EMAS)
# ============================================================
async def send_vacancy_post(bot_client, target, caption, image_path):
    buttons = [Button.url("📄 REZYUME KERAKMI?", RESUME_LINK)]
    while True:
        try:
            if image_path and os.path.exists(image_path):
                await bot_client.send_file(
                    target,
                    file=image_path,
                    caption=trim_caption(caption, MAX_CAPTION_LEN),
                    buttons=buttons,
                )
            else:
                await bot_client.send_message(
                    target,
                    trim_caption(caption, MAX_TEXT_LEN),
                    buttons=buttons,
                )
            return True
        except FloodWaitError as e:
            print(f"  FloodWait kutilmoqda: {e.seconds} soniya...")
            await asyncio.sleep(e.seconds + 1)
        except Exception as e:
            print(f"  Yuborishda xatolik: {e}")
            return False


# ============================================================
# 12. ASOSIY JARAYON
# ============================================================
async def main():
    print("Telegram clientlar ishga tushmoqda...")
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)

    try:
        await user_client.start()
        me = await user_client.get_me()
        print(f"Kuzatuvchi akkaunt ulandi: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"CRITICAL XATO: user_client ulanmadi: {e}")
        return

    try:
        await bot_client.start(bot_token=BOT_TOKEN)
        bme = await bot_client.get_me()
        print(f"Bot ulandi: @{bme.username}")
    except Exception as e:
        print(f"CRITICAL XATO: bot_client ulanmadi: {e}")
        return

    state = load_state()

    for ch in CHANNELS:
        print(f"\n--- Kanal tekshirilmoqda: {ch!r} ---")
        last_id = state.get(ch, 0)
        newest_id_seen = last_id
        posted_count = 0
        skipped_ad = 0

        try:
            entity = await user_client.get_entity(ch)

            # eskisidan yangisiga qarab, TARTIB buzilmasin
            async for message in user_client.iter_messages(
                entity, min_id=last_id, reverse=True, limit=50
            ):
                newest_id_seen = max(newest_id_seen, message.id)
                post_text = extract_message_text(message)

                if not is_vacancy(post_text):
                    skipped_ad += 1
                    continue

                final_caption = build_vacancy_post(post_text)
                image_path = get_matching_image(post_text, ch)

                ok = await send_vacancy_post(bot_client, TARGET_CHANNEL, final_caption, image_path)
                if ok:
                    posted_count += 1
                    print(f"  -> Vakansiya joylandi (msg_id={message.id})")

                await asyncio.sleep(2)

            state[ch] = newest_id_seen
            save_state(state)
            print(f"Xulosa [{ch}]: {posted_count} ta vakansiya joylandi, {skipped_ad} ta reklama/mos kelmagan post o'tkazib yuborildi.")

        except Exception as e:
            print(f"XATO [{ch!r}]: {type(e).__name__} - {e}")
            traceback.print_exc()

    await user_client.disconnect()
    await bot_client.disconnect()
    print("\nJarayon yakunlandi.")


if __name__ == "__main__":
    asyncio.run(main())
