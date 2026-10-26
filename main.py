import os
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# خواندن توکن از متغیرهای محیطی رندر
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ توکن ربات (TELEGRAM_BOT_TOKEN) تنظیم نشده است!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name or "دوست عزیز"
    
    # دکمه‌های شیک شبیه بات‌سازها
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 ساخت ربات جدید", callback_data="create_bot"))
    markup.add(InlineKeyboardButton("⚙️ ربات‌های من", callback_data="my_bots"),
               InlineKeyboardButton("📚 راهنما", callback_data="help"))
    markup.add(InlineKeyboardButton("👨‍💻 پشتیبانی", url="https://t.me/Masih"))

    welcome_text = (
        f"سلام <b>{user_name}</b> عزیز! 👋\n\n"
        "🤖 به سیستم پیشرفته <b>بات‌ساز مسیح</b> خوش آمدید.\n\n"
        "از طریق این ربات می‌توانید به راحتی و بدون نیاز به دانش برنامه‌نویسی، ربات تلگرامی خودتان را بسازید و مدیریت کنید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "create_bot":
        bot.answer_callback_query(call.id, "بخش ساخت ربات جدید")
        bot.send_message(
            call.message.chat.id,
            "🛠 برای ساخت ربات جدید، لطفاً توکن ربات خود (گرفته شده از @BotFather) را ارسال کنید:"
        )
    elif call.data == "my_bots":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📦 شما هنوزی رباتی نساخته‌اید.")
    elif call.data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            "💡 <b>راهنمای استفاده:</b>\n\n"
            "۱. به ربات @BotFather بروید و یک ربات جدید بسازید.\n"
            "۲. توکن آن را به این بات‌ساز بدهید.\n"
            "۳. ربات شما آماده‌ست!"
        )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.reply_to(
        message, 
        "مسیح بات‌ساز آنلاینه! 🚀\nبرای شروع کار با دستور /start منو را باز کنید."
    )

if __name__ == "__main__":
    logger.info("🤖 بات‌ساز مسیح با موفقیت روشن شد و در حال دریافت پیام است...")
    bot.infinity_polling()
