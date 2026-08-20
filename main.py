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
from telethon.tl.types import MessageEntityTextUrl

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
# 2. KUZATILADIGAN KANALLAR
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
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
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
# 6. REKLAMA / VAKANSIYA EMASLARNI FILTRLASH
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
# 8.5 ARIZA / BATAFSIL LINKINI TOPISH
# ============================================================
APPLY_LINK_KEYWORDS = [
    "batafsil", "ariza yuborish", "ariza topshirish", "to'liq ma'lumot",
    "murojaat", "yuborish uchun", "topshirish uchun", "havola", "link",
]


def extract_application_link(message):
    """Postdagi inline tugmalar orasidan 'batafsil/ariza' kabi so'zga mos URL tugmani topadi."""
    try:
        if message.buttons:
            # 1) Kalit so'zga mos tugmani qidirish
            for row in message.buttons:
                for btn in row:
                    url = getattr(btn, "url", None)
                    label = (getattr(btn, "text", "") or "").lower()
                    if url and any(k in label for k in APPLY_LINK_KEYWORDS):
                        return url
            # 2) Agar faqat bitta URL-tugma bo'lsa, o'shani olish
            url_buttons = [
                getattr(btn, "url", None)
                for row in message.buttons
                for btn in row
                if getattr(btn, "url", None)
            ]
            if len(url_buttons) == 1:
                return url_buttons[0]
    except Exception:
        pass
    return None


def _utf16_slice(text: str, offset: int, length: int) -> str:
    """Telegram entity offset/length UTF-16 birliklarida bo'lgani uchun
    matndan xavfsiz (emoji va boshqa maxsus belgilarni hisobga olib) kesib oladi."""
    raw = text.encode("utf-16-le")
    start = offset * 2
    end = start + length * 2
    return raw[start:end].decode("utf-16-le", errors="ignore")


def extract_hidden_text_link(message):
    """Matn ichida yashiringan hyperlink'larni topadi
    (masalan 'Batafsil' so'zi bosilganda ochiladigan, lekin oddiy matnda ko'rinmaydigan link)."""
    text = extract_message_text(message)
    entities = getattr(message, "entities", None)
    if not entities or not text:
        return None

    candidates = []
    for ent in entities:
        if isinstance(ent, MessageEntityTextUrl):
            label = _utf16_slice(text, ent.offset, ent.length).lower()
            candidates.append((label, ent.url))

    if not candidates:
        return None

    # 1) Kalit so'zga mos label'li linkni qidirish
    for label, url in candidates:
        if any(k in label for k in APPLY_LINK_KEYWORDS):
            return url

    # 2) Agar faqat bitta yashirin link bo'lsa, o'shani qaytarish
    if len(candidates) == 1:
        return candidates[0][1]

    # 3) Bir nechta yashirin link bo'lsa ham, birinchisini olish
    #    (manba kanalda odatda faqat ariza linki shu tarzda joylashtiriladi)
    return candidates[0][1]


def extract_link_from_text(text: str):
    """Tugma va yashirin hyperlink bo'lmasa, matn ichidan
    'batafsil/ariza' so'zi yonidagi oddiy ko'rinadigan linkni qidiradi."""
    if not text:
        return None
    for line in text.split("\n"):
        low = line.lower()
        if any(k in low for k in APPLY_LINK_KEYWORDS):
            m = URL_RE.search(line)
            if m:
                return m.group(0)
    # Agar kalit so'z topilmasa ham, matnda bitta link bo'lsa o'shani olish
    all_links = URL_RE.findall(text)
    if len(all_links) == 1:
        return all_links[0]
    return None


def extract_any_link(message, post_text):
    """Barcha usullarni ketma-ket sinab, topilgan birinchi linkni qaytaradi:
    1) Inline tugma  2) Yashirin matn ichidagi hyperlink  3) Oddiy ko'rinadigan link"""
    return (
        extract_application_link(message)
        or extract_hidden_text_link(message)
        or extract_link_from_text(post_text)
    )


# ============================================================
# 9. YAKUNIY POST SHABLONINI QURISH (oddiy qolip)
# ============================================================
def build_vacancy_post(raw_text: str) -> str:
    cleaned = clean_source_text(raw_text)
    region = detect_region(cleaned)

    header = "📢 YANGI DAVLAT VAKANSIYASI"
    region_line = f"\n📍 VILOYAT: {region}" if region else ""

    post = (
        f"{header}"
        f"{region_line}\n\n"
        f"{cleaned}\n\n"
        f"Rezyume tayyorlashda sizga yordam beramiz 👇\n"
        f"👉 {RESUME_LINK.replace('https://t.me/', '@')}\n"
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
# 10. YUBORISH (FloodWait bilan, tugma bilan, forward EMAS)
# ============================================================
async def send_vacancy_post(bot_client, target, caption, image_path, apply_link=None):
    buttons = []
    if apply_link:
        buttons.append(Button.url("📝 BATAFSIL / ARIZA YUBORISH", apply_link))
    buttons.append(Button.url("📄 REZYUME KERAKMI?", RESUME_LINK))
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
# 11. ASOSIY JARAYON
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
                apply_link = extract_any_link(message, post_text)

                ok = await send_vacancy_post(bot_client, TARGET_CHANNEL, final_caption, image_path, apply_link)
                if ok:
                    posted_count += 1
                    link_info = "link bilan" if apply_link else "LINKSIZ"
                    print(f"  -> Vakansiya joylandi (msg_id={message.id}, {link_info})")

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
