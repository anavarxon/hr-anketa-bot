import logging
from google import genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
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
BOT_TOKEN = "7634467401:AAGBpV1MoC0qzeo1_8OS0bXcc6NZ3_uQubI"  # Bot Token
ADMIN_ID = 1168952611  # Telegram ID
GEMINI_API_KEY = "AQ.Ab8RN6JZuwaFTXld3fv_JsG5UevwrjXf_0jd7u4X8wxARinDJg"  # Google AI Studio API Key

# Yangi Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Bosqichlar
(
    PHOTO, POSITION, FULL_NAME, BIRTH_DATE, PHONE, ADDRESS, 
    EDUCATION, EDU_DETAILS, WORK_EXP, LANGUAGES, COMPUTER, 
    DRIVER, FAMILY, SALARY, ADDITIONAL
) = range(15)


async def analyze_candidate_with_ai(user_data: dict) -> str:
    """Gemini AI orqali nomzodni tahlil qilish va baholash"""
    prompt = f"""
Siz tajribali HR xodimi va psixologsiz. Quyida ishga kirmoqchi bo'lgan nomzod to'ldirgan anketa ma'lumotlari berilgan.
Sizning vazifangiz nomzodning javoblarini chuqur tahlil qilib, HR menejer uchun xulosa va baho berish.

NOMZOD ANKETASI:
- Topshirayotgan lavozimi: {user_data.get('position')}
- F.I.Sh: {user_data.get('fullname')}
- Tug'ilgan yili/joyi: {user_data.get('birthdate')}
- Ma'lumoti va o'quv yurti: {user_data.get('education')} / {user_data.get('edu_details')}
- Ish tajribasi: {user_data.get('work_exp')}
- Tillar: {user_data.get('languages')}
- Kompyuter ko'nikmalari: {user_data.get('computer')}
- Haydovchilik/Avto: {user_data.get('driver')}
- Oilaviy ahvoli: {user_data.get('family')}
- Kutilayotgan maosh: {user_data.get('salary')}
- O'zi haqida qo'shimcha va sifatlari: {user_data.get('additional')}

QUYIDAGI MEZONLAR BO'YICHA TAHLIL QILING (O'zbek tilida, professional va aniq javob bering):

1. **Bilimi va Salohiyati (1-10 ball):** Ma'lumoti, tajribasi va ko'nikmalari u tanlagan lavozimga qanchalik mos?
2. **G'ayrati va Yonib ishlash xohishi (1-10 ball):** Javoblaridagi intilish, motivatsiya va ishtiyoq darajasi.
3. **Mantiq va Samimiylik (Rostg'oylik):** Javoblarida qarama-qarshiliklar yoki oshirib ko'rsatilgan joylar bormi? Mantiqan bir-biriga mos keladimi?
4. **Kuchli va Kuchsiz tomonlari:** Javoblarga asoslangan holda 2 ta kuchli va 2 ta zaif tomonini ko'rsating.
5. **YAKUNIY XULOSA VA TAVSIYA (1-10 ball):** 
   - Umumiy baho: X/10
   - HR uchun tavsiya: (Suhbatga chaqirish shart / Zaxirada ushlash / Rad etish)
"""
    try:
        # Model 'gemini-2.0-flash' ga o'zgardi (ushbu model 100% ishlaydi)
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini AI xatoligi: {e}")
        return "⚠️ Sun'iy intellekt tahlilida xatolik yuz berdi."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Ishga qabul qilish anketasiga xush kelibsiz.\n\n"
        "Iltimos, anketani to'ldirish uchun rasmingizni yuboring (yoki matn yuborib o'tkazib yuboring)."
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
    else:
        context.user_data['photo'] = None

    await update.message.reply_text("Qaysi bo'lim va lavozimga topshiryapsiz?\n(Masalan: *Sotuv bo'limi - Menejer*)", parse_mode="Markdown")
    return POSITION


async def get_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['position'] = update.message.text
    await update.message.reply_text("To'liq F.I.Sh. (Familiya, Ism, Otangizning ismi):")
    return FULL_NAME


async def get_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fullname'] = update.message.text
    await update.message.reply_text("Tug'ilgan sanangiz va joyingiz (Masalan: 15.05.1998, Toshkent sh.):")
    return BIRTH_DATE


async def get_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['birthdate'] = update.message.text
    reply_keyboard = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
    await update.message.reply_text(
        "Siz bilan bog'lanish uchun telefon raqamingizni yuboring:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.contact.phone_number if update.message.contact else update.message.text
    await update.message.reply_text("Doimiy yashash manzilingiz (Viloyat, tuman, ko'cha/uy):", reply_markup=ReplyKeyboardRemove())
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    keyboard = [["Oliy", "O'rta maxsus", "O'rta"]]
    await update.message.reply_text("Ma'lumotingiz darajasi:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return EDUCATION


async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['education'] = update.message.text
    await update.message.reply_text("Qaysi o'quv yurtini va qaysi yili tugatgansiz? (Fakultet/Yo'nalish):", reply_markup=ReplyKeyboardRemove())
    return EDU_DETAILS


async def get_edudetails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['edu_details'] = update.message.text
    await update.message.reply_text("Oldingi ish joylaringiz haqida ma'lumot bering:\n(Tashkilot nomi, lavozim, ishlagan yilingiz va bo'shash sababi)")
    return WORK_EXP


async def get_workexp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['work_exp'] = update.message.text
    await update.message.reply_text("Qaysi xorijiy tillarni bilasiz va darajangiz qanday?\n(Masalan: O'zbek - a'lo, Rus - yaxshi, Ingliz - o'rta)")
    return LANGUAGES


async def get_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['languages'] = update.message.text
    await update.message.reply_text("Qaysi kompyuter dasturlarini bilasiz?\n(Masalan: MS Office, Word, Excel, 1C, AutoCAD, Photoshop va h.k.)")
    return COMPUTER


async def get_computer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['computer'] = update.message.text
    keyboard = [["Bormi (A, B, C...)", "Yo'q"]]
    await update.message.reply_text("Haydovchilik guvohnomangiz yoki shaxsiy avtomobilingiz bormi?", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return DRIVER


async def get_driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['driver'] = update.message.text
    keyboard = [["Oilali", "Oila qurmagan"]]
    await update.message.reply_text("Oilaviy ahvolingiz:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return FAMILY


async def get_family(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['family'] = update.message.text
    await update.message.reply_text("Qancha miqdordagi maoshga ishlamoqchisiz? (Kutilayotgan maosh):", reply_markup=ReplyKeyboardRemove())
    return SALARY


async def get_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['salary'] = update.message.text
    await update.message.reply_text("O'zingiz haqingizda qo'shimcha ma'lumotlar:\n(Ijobiy va salbiy taraflaringiz, yonib ishlashingizni isbotlovchi misollar va h.k.)")
    return ADDITIONAL


async def get_additional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['additional'] = update.message.text

    await update.message.reply_text(
        "Rahmat! Anketangiz qabul qilindi. Sun'iy intellekt ma'lumotlaringizni tahlil qilmoqda, tez orada siz bilan bog'lanamiz.",
        reply_markup=ReplyKeyboardRemove()
    )

    summary_text = (
        "📥 *YANGI ISHGA QABUL ANKETASI*\n\n"
        f"🎯 *Lavozim:* {context.user_data.get('position')}\n"
        f"👤 *F.I.Sh:* {context.user_data.get('fullname')}\n"
        f"🎂 *Tug'ilgan yili/joyi:* {context.user_data.get('birthdate')}\n"
        f"📞 *Tel:* {context.user_data.get('phone')}\n"
        f"🏠 *Manzil:* {context.user_data.get('address')}\n\n"
        f"🎓 *Ma'lumoti:* {context.user_data.get('education')}\n"
        f"🏫 *O'quv yurti:* {context.user_data.get('edu_details')}\n"
        f"💼 *Ish tajribasi:* {context.user_data.get('work_exp')}\n\n"
        f"🌐 *Tillar:* {context.user_data.get('languages')}\n"
        f"💻 *Kompyuter:* {context.user_data.get('computer')}\n"
        f"🚗 *Haydovchilik/Avto:* {context.user_data.get('driver')}\n"
        f"👨‍👩‍👧 *Oilaviy ahvoli:* {context.user_data.get('family')}\n\n"
        f"💰 *Kutilayotgan maosh:* {context.user_data.get('salary')}\n"
        f"📝 *Qo'shimcha:* {context.user_data.get('additional')}\n"
    )

    # AI tahlili
    ai_analysis = await analyze_candidate_with_ai(context.user_data)

    ai_report_text = (
        "🤖 *GEMINI AI HR TAHLILI VA BAHOSI*\n"
        "------------------------------------\n"
        f"{ai_analysis}"
    )

    try:
        photo = context.user_data.get('photo')
        if photo:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=summary_text, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=summary_text, parse_mode="Markdown")

        await context.bot.send_message(chat_id=ADMIN_ID, text=ai_report_text, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Anketa bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, get_photo), CommandHandler("skip", get_photo), MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo)],
            POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_position)],
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fullname)],
            BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)],
            PHONE: [MessageHandler(filters.CONTACT, get_phone), MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            EDU_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_edudetails)],
            WORK_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_workexp)],
            LANGUAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_languages)],
            COMPUTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_computer)],
            DRIVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_driver)],
            FAMILY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_family)],
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_salary)],
            ADDITIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_additional)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Bot va Gemini AI ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
