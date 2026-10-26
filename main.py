import os
import time
import sqlite3
import logging
import threading
from typing import Optional

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from cryptography.fernet import Fernet, InvalidToken

# -------------------- تنظیمات --------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("masih_factory")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ENCRYPTION_KEY = os.getenv("BOT_TOKEN_ENCRYPTION_KEY", "").strip()
DB_PATH = os.getenv("DATABASE_PATH", "masih_factory.sqlite3")

if not BOT_TOKEN:
    raise RuntimeError("متغیر TELEGRAM_BOT_TOKEN تنظیم نشده است.")
if not ENCRYPTION_KEY:
    raise RuntimeError(
        "متغیر BOT_TOKEN_ENCRYPTION_KEY تنظیم نشده است. "
        "یک کلید Fernet بسازید و در متغیرهای محیطی قرار دهید."
    )

try:
    cipher = Fernet(ENCRYPTION_KEY.encode("utf-8"))
except (ValueError, TypeError) as exc:
    raise RuntimeError("مقدار BOT_TOKEN_ENCRYPTION_KEY معتبر نیست.") from exc

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True)
db_lock = threading.Lock()
state_lock = threading.Lock()
user_states = {}
running_child_bots = {}
child_lock = threading.Lock()


def connect_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_lock:
        with connect_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    bot_id INTEGER NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    encrypted_token BLOB NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_bots_owner ON user_bots(owner_id)"
            )


def main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🚀 ساخت ربات جدید", callback_data="create_bot"))
    markup.add(
        InlineKeyboardButton("📦 ربات‌های من", callback_data="my_bots"),
        InlineKeyboardButton("📚 راهنما", callback_data="help"),
    )
    markup.add(InlineKeyboardButton("🔒 امنیت توکن", callback_data="security"))
    return markup


def safe_html(value: str) -> str:
    value = value or ""
    return (value.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def set_state(user_id: int, value: Optional[str]):
    with state_lock:
        if value is None:
            user_states.pop(user_id, None)
        else:
            user_states[user_id] = value


def get_state(user_id: int) -> Optional[str]:
    with state_lock:
        return user_states.get(user_id)


def get_user_bots(owner_id: int):
    with db_lock:
        with connect_db() as conn:
            return conn.execute(
                "SELECT bot_id, username, display_name, created_at "
                "FROM user_bots WHERE owner_id=? ORDER BY id DESC",
                (owner_id,),
            ).fetchall()


def save_user_bot(owner_id: int, bot_id: int, username: str,
                  display_name: str, token: str):
    encrypted = cipher.encrypt(token.encode("utf-8"))
    with db_lock:
        with connect_db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO user_bots
                   (owner_id, bot_id, username, display_name, encrypted_token)
                   VALUES (?, ?, ?, ?, ?)""",
                (owner_id, bot_id, username, display_name, encrypted),
            )


def decrypt_token(encrypted) -> str:
    try:
        return cipher.decrypt(bytes(encrypted)).decode("utf-8")
    except (InvalidToken, ValueError, TypeError) as exc:
        raise RuntimeError(
            "رمزگشایی توکن ناموفق بود؛ کلید BOT_TOKEN_ENCRYPTION_KEY را بررسی کنید."
        ) from exc


def start_child_bot(row):
    child_id = int(row["bot_id"])
    with child_lock:
        if child_id in running_child_bots and running_child_bots[child_id].is_alive():
            return

    try:
        token = decrypt_token(row["encrypted_token"])
        child = telebot.TeleBot(token, parse_mode="HTML", threaded=True)

        @child.message_handler(commands=["start"])
        def child_start(message):
            name = safe_html(message.from_user.first_name or "دوست عزیز")
            child.send_message(
                message.chat.id,
                f"سلام <b>{name}</b>! 👋\n"
                "این ربات با بات‌ساز مسیح ساخته شده است.\n"
                "برای راه‌اندازی قابلیت‌های اختصاصی، تنظیمات ربات را تکمیل کنید."
            )

        @child.message_handler(commands=["help"])
        def child_help(message):
            child.send_message(
                message.chat.id,
                "📚 راهنما\nاز دستور /start برای شروع استفاده کنید."
            )

        def run_polling():
            logger.info("Starting child bot @%s (id=%s)", row["username"], child_id)
            while True:
                try:
                    child.infinity_polling(
                        timeout=20, long_polling_timeout=20,
                        skip_pending=True, allowed_updates=["message"]
                    )
                    break
                except Exception:
                    logger.exception("Child bot @%s stopped unexpectedly", row["username"])
                    time.sleep(5)

        thread = threading.Thread(
            target=run_polling,
            name=f"child-bot-{child_id}",
            daemon=True,
        )
        with child_lock:
            running_child_bots[child_id] = thread
        thread.start()
    except Exception:
        logger.exception("Could not start child bot id=%s", child_id)


def restore_child_bots():
    with db_lock:
        with connect_db() as conn:
            rows = conn.execute(
                "SELECT bot_id, username, display_name, encrypted_token FROM user_bots"
            ).fetchall()
    for row in rows:
        start_child_bot(row)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    name = safe_html(message.from_user.first_name or "دوست عزیز")
    text = (
        f"سلام <b>{name}</b> عزیز! 👋\n\n"
        "🤖 به <b>بات‌ساز مسیح</b> خوش آمدی.\n\n"
        "می‌توانی توکن رباتی را که از @BotFather گرفته‌ای ثبت کنی. "
        "توکن‌ها در پایگاه داده به‌صورت رمزگذاری‌شده نگهداری می‌شوند.\n\n"
        "یکی از گزینه‌های زیر را انتخاب کن:"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        if call.data == "create_bot":
            set_state(call.from_user.id, "awaiting_token")
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "🛠 توکن رباتت را از @BotFather بگیر و همین‌جا ارسال کن.\n\n"
                "⚠️ توکن را در گروه یا برای افراد دیگر نفرست. فقط در گفت‌وگوی خصوصی با بات‌ساز ارسال کن.\n"
                "برای لغو، /cancel را بفرست."
            )
        elif call.data == "my_bots":
            bot.answer_callback_query(call.id)
            rows = get_user_bots(call.from_user.id)
            if not rows:
                bot.send_message(
                    call.message.chat.id,
                    "📦 هنوز رباتی ثبت نکرده‌ای.",
                    reply_markup=main_menu()
                )
                return
            lines = ["📦 <b>ربات‌های ثبت‌شده تو:</b>\n"]
            for item in rows[:50]:
                lines.append(
                    f"• @{safe_html(item['username'])} — "
                    f"{safe_html(item['display_name'])}\n"
                    f"  شناسه: <code>{item['bot_id']}</code>"
                )
            bot.send_message(call.message.chat.id, "\n".join(lines), reply_markup=main_menu())
        elif call.data == "help":
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "📚 <b>راهنمای استفاده</b>\n\n"
                "۱. در @BotFather یک ربات بساز.\n"
                "۲. روی «ساخت ربات جدید» بزن.\n"
                "۳. توکن را فقط در گفت‌وگوی خصوصی ارسال کن.\n"
                "۴. پس از اعتبارسنجی، ربات ثبت و اجرا می‌شود.\n\n"
                "ربات ساخته‌شده فعلاً پاسخ پایه به /start و /help دارد.",
                reply_markup=main_menu()
            )
        elif call.data == "security":
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "🔒 نکات امنیتی\n\n"
                "• توکن را در گروه نفرست.\n"
                "• توکن‌ها در پایگاه داده رمزگذاری می‌شوند.\n"
                "• متغیر BOT_TOKEN_ENCRYPTION_KEY را محرمانه نگه دار.\n"
                "• اگر توکنی افشا شد، آن را در @BotFather باطل و جایگزین کن.",
                reply_markup=main_menu()
            )
        else:
            bot.answer_callback_query(call.id, "این گزینه شناخته نشد.")
    except Exception:
        logger.exception("Callback handling failed")
        try:
            bot.answer_callback_query(call.id, "خطا رخ داد؛ دوباره تلاش کن.")
        except Exception:
            pass


@bot.message_handler(commands=["cancel"])
def cancel_action(message):
    set_state(message.from_user.id, None)
    bot.reply_to(message, "عملیات لغو شد.", reply_markup=main_menu())


@bot.message_handler(func=lambda message: True, content_types=["text"])
def handle_text(message):
    user_id = message.from_user.id
    state = get_state(user_id)

    if state != "awaiting_token":
        bot.reply_to(
            message,
            "بات‌ساز مسیح آماده است. برای نمایش منو دستور /start را بفرست.",
            reply_markup=main_menu()
        )
        return

    # توکن فقط در چت خصوصی پذیرفته شود تا در گروه منتشر نشود.
    if message.chat.type != "private":
        set_state(user_id, None)
        bot.reply_to(
            message,
            "برای امنیت، توکن را در گروه ارسال نکن. به گفت‌وگوی خصوصی بات‌ساز برو و /start را بزن."
        )
        return

    token = (message.text or "").strip()
    if len(token) < 20 or ":" not in token or any(ch.isspace() for ch in token):
        bot.reply_to(message, "❌ قالب توکن درست به نظر نمی‌رسد. دوباره تلاش کن یا /cancel بزن.")
        return

    # حذف پیام حاوی توکن، در صورت داشتن دسترسی؛ ممکن است تلگرام اجازه ندهد.
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        logger.warning("Could not delete the incoming token message.")

    set_state(user_id, None)
    status_msg = bot.send_message(message.chat.id, "⏳ در حال بررسی توکن با تلگرام...")

    try:
        candidate = telebot.TeleBot(token, parse_mode="HTML", threaded=False)
        info = candidate.get_me()
        if not info or not info.is_bot or not info.username:
            raise ValueError("توکن به یک ربات معتبر تعلق ندارد.")

        save_user_bot(
            owner_id=user_id,
            bot_id=info.id,
            username=info.username,
            display_name=info.first_name or info.username,
            token=token,
        )

        with db_lock:
            with connect_db() as conn:
                row = conn.execute(
                    "SELECT bot_id, username, display_name, encrypted_token "
                    "FROM user_bots WHERE bot_id=?",
                    (info.id,)
                ).fetchone()

        start_child_bot(row)
        bot.edit_message_text(
            f"✅ ربات <b>@{safe_html(info.username)}</b> با موفقیت ثبت شد و راه‌اندازی آن آغاز شد.\n\n"
            "برای دیدن فهرست، «ربات‌های من» را بزن.\n"
            "این نسخه فعلاً پاسخ پایه به /start و /help را در ربات جدید فعال می‌کند.",
            message.chat.id,
            status_msg.message_id,
            reply_markup=main_menu()
        )
    except Exception:
        logger.exception("Token validation or child bot startup failed")
        bot.edit_message_text(
            "❌ توکن تأیید نشد یا ذخیره‌سازی با خطا روبه‌رو شد.\n"
            "مطمئن شو توکن را از @BotFather درست کپی کرده‌ای. "
            "اگر مشکل ادامه داشت، لاگ هاست را بررسی کن.",
            message.chat.id,
            status_msg.message_id,
            reply_markup=main_menu()
        )


if __name__ == "__main__":
    init_db()
    logger.info("MASIH bot factory starting")
    restore_child_bots()
    bot.infinity_polling(
        timeout=20,
        long_polling_timeout=20,
        skip_pending=True,
        allowed_updates=["message", "callback_query"]
    )
