import os
import logging
import json
from aiohttp import web
from google import genai
from google.genai import types
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === SOZLAMALAR ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8707986524:AAEo-rIRHunBAhLksE0wSapVCsP_X7lpb1Q")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1168952611"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Yangi Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Faol va ishlaydigan Gemini 3.6 Flash modellar
VALIDATION_MODELS = ['gemini-3.6-flash', 'gemini-3.5-flash-lite']
ANALYSIS_MODELS = ['gemini-3.6-flash', 'gemini-3.5-flash-lite']


def call_gemini_with_fallback(contents, models):
    """Modellarni birma-bir sinab ko'radi."""
    last_error = None
    for model_name in models:
        try:
            return ai_client.models.generate_content(model=model_name, contents=contents)
        except Exception as e:
            last_error = e
            logging.warning(f"Model '{model_name}' ishlamadi ({e}). Keyingisiga o'tilmoqda...")
            continue
    raise last_error


# === RENDER PORTI UCHUN DUMMY SERVER (Render 'Live' deyishi uchun SHART) ===
async def start_dummy_server():
    async def handle_ping(request):
        return web.Response(text="HR Anketa Bot is running on Render!")

    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Render Veb-server {port}-portda ishga tushdi.")


# === TELEGRAM MENU TUGMASINI SOZLASH ===
async def post_init(application):
    commands = [
        BotCommand("start", "Anketani boshlash 🚀"),
        BotCommand("cancel", "Anketani bekor qilish ❌")
    ]
    await application.bot.set_my_commands(commands)
    await start_dummy_server()


# === BOSQICHLAR (36 ta savol) ===
(
    PHOTO, POSITION, FULL_NAME, BIRTH_DATE, NATIONALITY, BIRTH_PLACE, ADDRESS,
    HOUSING, PHONE, EDUCATION_LEVEL, EDU_DETAILS, WORK_EXP,
    TRIP_ABROAD, TRIP_ABROAD_DETAILS, MARITAL_STATUS, FAMILY_MEMBERS,
    BUSINESS_TRIP, MILITARY, CRIMINAL, CAR, DRIVER_LICENSE,
    LANGUAGES, COMPUTER, HOW_HEARD, GUARANTOR, REFERENCE,
    BACKGROUND_CHECK, PREV_SALARY, EXPECTED_SALARY, WORK_DURATION,
    OVERTIME, MEETINGS, TEAMWORK, PARENTS_CALL, HEALTH, ADDITIONAL
) = range(36)

QUESTIONS = {
    POSITION: "Qaysi bo'lim va lavozimga topshiryapsiz?",
    FULL_NAME: "Familiya, ism-sharifingiz",
    BIRTH_DATE: "Tug'ilgan sanangiz",
    NATIONALITY: "Millatingiz",
    BIRTH_PLACE: "Tug'ilgan joyingiz",
    ADDRESS: "Doimiy yashash joyingiz",
    PHONE: "Shaxsiy mobil telefon raqamingiz",
    EDU_DETAILS: "Qachon va qaysi o'quv yurtini tamomlagansiz",
    WORK_EXP: "O'qishdan keyin qaysi korxona/tashkilotlarda ishlagansiz",
    TRIP_ABROAD_DETAILS: "Chet elga qachon, qaerga va nima sababdan chiqqansiz",
    FAMILY_MEMBERS: "Oila a'zolaringiz haqida ma'lumot",
    MILITARY: "Harbiy xizmatda bo'lganmisiz",
    CRIMINAL: "Sudlanganmisiz",
    CAR: "Shaxsiy avtomobilingiz bormi",
    DRIVER_LICENSE: "Haydovchilik guvohnomasi",
    LANGUAGES: "Xorijiy tillarni bilish darajangiz",
    COMPUTER: "Kompyuter dasturlarida ishlash darajangiz",
    HOW_HEARD: "Korxona haqida qaerdan ma'lumot oldingiz",
    GUARANTOR: "Kafolat bera oladigan shaxs",
    REFERENCE: "Tavsiya xati bera oladigan shaxs",
    PREV_SALARY: "Oxirgi ish o'rningizdagi maosh",
    EXPECTED_SALARY: "Kutilayotgan maosh",
    WORK_DURATION: "Qancha muddat ishlamoqchisiz",
    TEAMWORK: "Kollektiv deganda nimani tushunasiz",
    HEALTH: "Sog'ligingizda muammo yo'qmi",
    ADDITIONAL: "O'zingiz haqingizda qo'shimcha ma'lumot",
}


# ==================== AI VALIDATSIYA ====================

async def validate_answer(question: str, answer: str) -> dict:
    prompt = f"""Siz ishga qabul anketasini tekshiruvchi yordamchisiz.
Savol: "{question}"
Foydalanuvchi javobi: "{answer}"

Ushbu javob savolga mantiqan mos keladimi?
Faqat JSON formatida javob bering:
{{"valid": true yoki false, "reason": "qisqa sabab, o'zbek tilida"}}"""

    try:
        response = call_gemini_with_fallback(prompt, VALIDATION_MODELS)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result if "valid" in result else {"valid": True, "reason": ""}
    except Exception as e:
        logging.error(f"Validatsiyada xatolik: {e}")
        return {"valid": True, "reason": ""}


async def validate_photo(photo_bytes: bytes) -> dict:
    prompt = """Bu rasmda aniq bitta odamning yuzi ko'rinib turibdimi (portret yoki selfie)?
Faqat JSON formatida javob bering:
{"is_person": true yoki false, "reason": "qisqa sabab, o'zbek tilida"}"""

    try:
        contents = [
            types.Part.from_bytes(data=bytes(photo_bytes), mime_type='image/jpeg'),
            prompt,
        ]
        response = call_gemini_with_fallback(contents, VALIDATION_MODELS)
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result if "is_person" in result else {"is_person": True, "reason": ""}
    except Exception as e:
        logging.error(f"Rasm validatsiyasida xatolik: {e}")
        return {"is_person": True, "reason": ""}


async def analyze_candidate_with_ai(user_data: dict) -> str:
    prompt = f"""
Siz professional HR menejeri va psixologsiz. Quyida nomzodning to'liq anketasi berilgan.

NOMZOD MA'LUMOTLARI:
- Lavozim va Bo'lim: {user_data.get('position')}
- F.I.Sh: {user_data.get('fullname')}
- Tug'ilgan sanasi: {user_data.get('birthdate')}
- Millati: {user_data.get('nationality')}
- Tug'ilgan joyi: {user_data.get('birthplace')}
- Manzili (propiska): {user_data.get('address')}
- Yashash sharoiti: {user_data.get('housing')}
- Tel: {user_data.get('phone')}
- Ma'lumoti va o'quv yurti: {user_data.get('education_level')} / {user_data.get('edu_details')}
- Ish tajribasi: {user_data.get('work_exp')}
- Chet el safarlari: {user_data.get('trip_abroad')} ({user_data.get('trip_abroad_details', 'Yo\'q')})
- Oilaviy ahvoli: {user_data.get('marital_status')}
- Oila a'zolari: {user_data.get('family_members')}
- Komandirovka / Overtime / Majlislar: {user_data.get('business_trip')} / {user_data.get('overtime')} / {user_data.get('meetings')}
- Harbiy xizmat / Sudlanganlik: {user_data.get('military')} / {user_data.get('criminal')}
- Avto / Haydovchilik: {user_data.get('car')} / {user_data.get('driver_license')}
- Tillar va Kompyuter: {user_data.get('languages')} / {user_data.get('computer')}
- Korxona haqida qaerdan eshitgani: {user_data.get('how_heard')}
- Kafillik va Tavsiya: {user_data.get('guarantor')} / {user_data.get('reference')}
- Surishtirishga roziligi: {user_data.get('background_check')}
- Oldingi va Kutilayotgan maosh: {user_data.get('prev_salary')} / {user_data.get('expected_salary')}
- Ishlash muddati: {user_data.get('work_duration')}
- Kollektiv va Sog'liq: {user_data.get('teamwork')} / {user_data.get('health')}
- Ota-onani chaqirish: {user_data.get('parents_call')}
- Sifatlari: {user_data.get('additional')}

QUYIDAGI MEZONLAR BO'YICHA HR UCHUN TAHLIL BERING (O'zbek tilida):
1. **Bilimi va Salohiyati (1-10 ball)**
2. **G'ayrati va Motivatsiyasi (1-10 ball)**
3. **Mantiq va Samimiylik (Rostg'oylik)**
4. **Kuchli va Kuchsiz tomonlari**
5. **YAKUNIY XULOSA VA TAVSIYA (1-10 ball va tavsiya)**
"""
    try:
        response = call_gemini_with_fallback(prompt, ANALYSIS_MODELS)
        return response.text
    except Exception as e:
        logging.error(f"Gemini AI xatoligi: {e}")
        return "⚠️ Sun'iy intellekt tahlilida xatolik yuz berdi."


async def process_text_step(update: Update, context: ContextTypes.DEFAULT_TYPE, current_state: int, field_name: str, next_question: str, next_state: int, keyboard=None):
    answer = update.message.text
    question_text = QUESTIONS.get(current_state, "")

    if question_text:
        result = await validate_answer(question_text, answer)
        if not result.get("valid", True):
            await update.message.reply_text(f"⚠️ {result.get('reason', 'Javob savolga mos emas.')}\n\nIltimos, qaytadan kiriting:\n{question_text}")
            return current_state

    context.user_data[field_name] = answer
    reply_markup = keyboard if keyboard else ReplyKeyboardRemove()
    await update.message.reply_text(next_question, reply_markup=reply_markup)
    return next_state


async def safe_send_message(bot, chat_id, text, parse_mode="Markdown"):
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=chat_id, text=text)


# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Ishga qabul qilish anketasiga xush kelibsiz.\n\n"
        "Iltimos, anketaga biriktirish uchun o'zingizning rasmingizni yuboring (yoki matn yozib o'tkazib yuboring):"
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        checking_msg = await update.message.reply_text("⏳ Rasmingiz tekshirilmoqda...")
        result = await validate_photo(photo_bytes)

        try:
            await checking_msg.delete()
        except Exception:
            pass

        if not result.get("is_person", True):
            await update.message.reply_text(f"❌ {result.get('reason', 'Bu rasm mos emas.')}\n\nIltimos, yuzingiz
