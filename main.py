"""
Masih Music Bot — starter main.py
این فایل نقطه شروع پروژه است؛ هنوز پخش واقعی در ویس‌چت به سرویس PyTgCalls و
تنظیمات معتبر تلگرام نیاز دارد. توکن را داخل کد قرار نده؛ از متغیر محیطی استفاده کن.
"""

import os
import logging
import telebot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("masih-music-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "متغیر TELEGRAM_BOT_TOKEN تنظیم نشده است. "
        "توکن ربات را در بخش Environment میزبان اضافه کن."
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🎧 <b>ربات صوتی مسیح</b>\n\n"
        "ربات اجرا شده و آمادهٔ مرحلهٔ بعدی تنظیم پخش ویس‌چت است.\n"
        "برای راهنما دستور /help را بفرست.",
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "📚 <b>راهنما</b>\n\n"
        "• /start — بررسی روشن بودن ربات\n"
        "• پخش واقعی موسیقی در ویس‌چت هنوز در این فایل پیاده‌سازی نشده است.\n"
        "برای اضافه‌کردن آن باید وابستگی‌های سازگار PyTgCalls و کلاینت تلگرام "
        "را متناسب با محیط میزبانی تنظیم کنیم.",
    )


@bot.message_handler(func=lambda message: bool(message.text))
def fallback(message):
    bot.reply_to(
        message,
        "پیامت دریافت شد. فعلاً از /start و /help استفاده کن؛ "
        "قابلیت پخش ویس‌چت در مرحلهٔ بعد اضافه می‌شود.",
    )


if __name__ == "__main__":
    logger.info("ربات صوتی مسیح در حال اجراست.")
    # برای هاست‌های معمولی، polling اتصال دریافت پیام‌ها را فعال نگه می‌دارد.
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
