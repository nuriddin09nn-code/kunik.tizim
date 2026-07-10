import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import sqlite3
from datetime import datetime
import json
import os

# Telegram bot tokeni
TOKEN = "8965240923:AAHWEFjJRUyexEG0BKSkcuDnYcv8bL1E9QU"

# Sayt havolasi (WebApp uchun)
WEBSITE_URL = "https://nuriddin09nn-code.github.io/kunlik.tizim"

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ma'lumotlar bazasi
def init_db():
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            phone_number TEXT,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            registered_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            category TEXT,
            description TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

# Menyu tugmalari
def get_main_menu():
    keyboard = [
        [KeyboardButton("💰 Kirim"), KeyboardButton("💸 Chiqim")],
        [KeyboardButton("📊 Balans"), KeyboardButton("📈 Hisobot")],
        [KeyboardButton("📋 Tarix"), KeyboardButton("🌐 Open App", web_app=WebAppInfo(url=WEBSITE_URL))],
        [KeyboardButton("📞 Telefon raqamini yuborish", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Kategoriyalar
CATEGORIES = {
    'kirim': ['📝 Ish haqi', '💼 Biznes', '📈 Investitsiya', '🎁 Sovg\'a', '💰 Boshqa'],
    'chiqim': ['🍽 Oziq-ovqat', '🚗 Transport', '🏠 Uy-joy', '👕 Kiyim-kechak', 
               '🎮 Ko\'ngilochar', '🏥 Sog\'liq', '📚 Ta\'lim', '🔧 Boshqa']
}

# /start komandasi
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    
    # Foydalanuvchini bazaga qo'shish
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, first_name, last_name, username, registered_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.id, user.first_name, user.last_name, user.username, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Telefon raqamini so'rash
    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Telefon raqamini yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum {user.first_name}!\n\n"
        f"💳 Moliyaviy botga xush kelibsiz!\n\n"
        f"📱 Iltimos, telefon raqamingizni yuboring yoki pastdagi tugmani bosing.",
        reply_markup=contact_keyboard
    )

# Telefon raqamini qabul qilish
async def handle_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    user = update.effective_user
    
    if contact.user_id == user.id:
        # Telefon raqamini bazaga saqlash
        conn = sqlite3.connect('finance_bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET phone_number = ? WHERE user_id = ?
        ''', (contact.phone_number, user.id))
        conn.commit()
        conn.close()
        
        # Asosiy menyuni ko'rsatish
        await update.message.reply_text(
            f"✅ Telefon raqami qabul qilindi: {contact.phone_number}\n\n"
            f"🏠 Asosiy menyu:",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text("❌ Iltimos, o'zingizning telefon raqamingizni yuboring!")

# Matnlarni qayta ishlash
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "💰 Kirim":
        context.user_data['transaction_type'] = 'kirim'
        keyboard = [[InlineKeyboardButton(cat, callback_data=f'cat_kirim_{cat}')] for cat in CATEGORIES['kirim']]
        keyboard.append([InlineKeyboardButton("🔙 Ortga", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💰 Kirim kategoriyasini tanlang:",
            reply_markup=reply_markup
        )
    
    elif text == "💸 Chiqim":
        context.user_data['transaction_type'] = 'chiqim'
        keyboard = [[InlineKeyboardButton(cat, callback_data=f'cat_chiqim_{cat}')] for cat in CATEGORIES['chiqim']]
        keyboard.append([InlineKeyboardButton("🔙 Ortga", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "💸 Chiqim kategoriyasini tanlang:",
            reply_markup=reply_markup
        )
    
    elif text == "📊 Balans":
        await show_balance(update, context)
    
    elif text == "📈 Hisobot":
        await show_report(update, context)
    
    elif text == "📋 Tarix":
        await show_history(update, context)
    
    elif text == "🌐 Open App":
        # WebApp orqali saytni ochish
        await update.message.reply_text(
            f"🌐 Sayt ochilmoqda...\n\n"
            f"📱 Quyidagi tugmani bosing:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Saytni ochish", web_app=WebAppInfo(url=WEBSITE_URL))]
            ])
        )
    
    elif text.isdigit():
        # Summa kiritilganda
        if 'transaction_type' in context.user_data and 'category' in context.user_data:
            amount = float(text)
            trans_type = context.user_data['transaction_type']
            category = context.user_data['category']
            
            # Tranzaktsiyani saqlash
            conn = sqlite3.connect('finance_bot.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, category, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, trans_type, amount, category, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ {trans_type.capitalize()} qo'shildi!\n"
                f"📊 Summa: {amount:,.0f} so'm\n"
                f"📂 Kategoriya: {category}\n"
                f"🕐 Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                reply_markup=get_main_menu()
            )
            
            # Tozalash
            del context.user_data['transaction_type']
            del context.user_data['category']
        else:
            await update.message.reply_text(
                "❌ Iltimos, avval kategoriyani tanlang!",
                reply_markup=get_main_menu()
            )
    else:
        await update.message.reply_text(
            "❌ Tushunarsiz buyruq. Iltimos, menyudan foydalaning.",
            reply_markup=get_main_menu()
        )

# Kategoriya tanlash (callback)
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'back':
        await query.message.delete()
        await query.message.reply_text(
            "🏠 Asosiy menyu:",
            reply_markup=get_main_menu()
        )
        return
    
    if data.startswith('cat_'):
        parts = data.split('_')
        trans_type = parts[1]
        category = parts[2]
        
        context.user_data['transaction_type'] = trans_type
        context.user_data['category'] = category
        
        await query.message.delete()
        await query.message.reply_text(
            f"📝 {trans_type.capitalize()} kategoriyasi: {category}\n\n"
            f"💰 Summani kiriting (faqat raqam):",
            reply_markup=get_main_menu()
        )

# Balansni ko'rsatish
async def show_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    # Kirimlar
    cursor.execute('SELECT SUM(amount) FROM transactions WHERE user_id=? AND type="kirim"', (user_id,))
    income = cursor.fetchone()[0] or 0
    
    # Chiqimlar
    cursor.execute('SELECT SUM(amount) FROM transactions WHERE user_id=? AND type="chiqim"', (user_id,))
    expense = cursor.fetchone()[0] or 0
    
    # Balans
    balance = income - expense
    
    conn.close()
    
    await update.message.reply_text(
        f"📊 BALANS\n"
        f"{'='*20}\n"
        f"💰 Kirim: {income:,.0f} so'm\n"
        f"💸 Chiqim: {expense:,.0f} so'm\n"
        f"{'='*20}\n"
        f"💳 Balans: {balance:,.0f} so'm",
        reply_markup=get_main_menu()
    )

# Hisobot
async def show_report(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    # Har bir kategoriya bo'yicha
    report_text = "📈 HISOBOT\n"
    report_text += "="*20 + "\n\n"
    
    # Kirim kategoriyalari
    report_text += "💰 KIRIM:\n"
    for cat in CATEGORIES['kirim']:
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE user_id=? AND type="kirim" AND category=?', 
                      (user_id, cat))
        amount = cursor.fetchone()[0] or 0
        if amount > 0:
            report_text += f"  {cat}: {amount:,.0f} so'm\n"
    
    # Chiqim kategoriyalari
    report_text += "\n💸 CHIQIM:\n"
    for cat in CATEGORIES['chiqim']:
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE user_id=? AND type="chiqim" AND category=?', 
                      (user_id, cat))
        amount = cursor.fetchone()[0] or 0
        if amount > 0:
            report_text += f"  {cat}: {amount:,.0f} so'm\n"
    
    conn.close()
    
    await update.message.reply_text(report_text, reply_markup=get_main_menu())

# Tarix
async def show_history(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('finance_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, amount, category, date FROM transactions 
        WHERE user_id=? ORDER BY date DESC LIMIT 10
    ''', (user_id,))
    
    transactions = cursor.fetchall()
    conn.close()
    
    if not transactions:
        await update.message.reply_text(
            "📋 Hali hech qanday tranzaktsiya yo'q.",
            reply_markup=get_main_menu()
        )
        return
    
    history_text = "📋 SO'NGI 10 TRANZAKTSIYA\n"
    history_text += "="*25 + "\n\n"
    
    for trans in transactions:
        trans_type, amount, category, date = trans
        emoji = "💰" if trans_type == "kirim" else "💸"
        sign = "+" if trans_type == "kirim" else "-"
        date_obj = datetime.fromisoformat(date)
        history_text += f"{emoji} {trans_type.upper()}\n"
        history_text += f"  {sign}{amount:,.0f} so'm\n"
        history_text += f"  📂 {category}\n"
        history_text += f"  🕐 {date_obj.strftime('%d.%m %H:%M')}\n\n"
    
    await update.message.reply_text(history_text, reply_markup=get_main_menu())

# Xatoliklarni qayta ishlash
async def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception occurred:", exc_info=context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
            reply_markup=get_main_menu()
        )

def main():
    # Ma'lumotlar bazasini yaratish
    init_db()
    
    # Bot application
    application = Application.builder().token(TOKEN).build()
    
    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_error_handler(error_handler)
    
    # Botni ishga tushirish
    print("🤖 Bot ishga tushdi...")
    print(f"🌐 WebApp URL: {WEBSITE_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()