
import os
import threading
from collections import defaultdict

import telebot
from telebot import types
from flask import Flask

# ==========================================
# MASIH GUARD PRO
# Developer: مسیح مختاری | Masih Hackring
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_NAME = "کدنویس مسیح مختاری | Masih Hackring"
DEVELOPER_CONTACT = "@YOUR_TELEGRAM_USERNAME"  # آیدی واقعی خودت را جایگزین کن

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN در Environment تنظیم نشده است.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# اطلاعات موقت؛ با ری‌استارت پاک می‌شوند
warnings = defaultdict(int)
group_rules = {}
blocked_links = defaultdict(bool)


def is_group(message):
    return message.chat.type in ("group", "supergroup")


def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


def is_bot_admin(chat_id):
    try:
        member = bot.get_chat_member(chat_id, bot.get_me().id)
        return member.status in ("creator", "administrator")
    except Exception:
        return False


def welcome_text(user):
    name = user.first_name or "دوست عزیز"
    return (
        f"سلام {name} عزیز! 👋💜\n\n"
        "به جمع ما خوش اومدی.\n"
        "لطفاً قوانین گروه رو رعایت کن.\n\n"
        "🛡️ محافظ گروه: MASIH GUARD PRO"
    )


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "⚡ MASIH GUARD PRO ⚡\n\n"
        "ربات مدیریت و امنیت گروه تلگرام\n\n"
        "🛡️ مدیریت اعضا و ضداسپم\n"
        "🔨 اخطار، سکوت و مسدودسازی\n"
        "📜 قوانین اختصاصی گروه\n"
        "👋 خوشامدگویی خودکار\n\n"
        f"👨‍💻 سازنده: {DEVELOPER_NAME}\n"
        f"📩 ارتباط: {DEVELOPER_CONTACT}\n\n"
        "برای مشاهده دستورات /help را بزن."
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.reply_to(
        message,
        "📚 راهنمای MASIH GUARD PRO\n\n"
        "/start — معرفی ربات\n"
        "/about — درباره سازنده\n"
        "/rules — مشاهده قوانین\n"
        "/setrules متن — تنظیم قوانین (مدیر)\n"
        "/antilink on — فعال‌سازی ضدلینک (مدیر)\n"
        "/antilink off — غیرفعال‌سازی ضدلینک (مدیر)\n"
        "/warn — اخطار به کاربر (روی پیامش ریپلای کن)\n"
        "/mute — سکوت کاربر (روی پیامش ریپلای کن)\n"
        "/unmute — رفع سکوت (روی پیامش ریپلای کن)\n"
        "/ban — مسدودسازی (روی پیامش ریپلای کن)\n"
        "/unban شناسه — رفع مسدودی با شناسه کاربر\n\n"
        "نکته: برای دستورات مدیریتی، ربات باید مدیر گروه باشد."
    )


@bot.message_handler(commands=["about"])
def about(message):
    bot.reply_to(
        message,
        "💎 MASIH GUARD PRO\n"
        "نسخه اولیه ربات مدیریت گروه\n\n"
        "👨‍💻 کدنویس: مسیح مختاری\n"
        "🌐 نام برنامه‌نویسی: Masih Hackring\n"
        f"📩 ارتباط: {DEVELOPER_CONTACT}\n\n"
        "ساخته‌شده با Python برای مدیریت امن‌تر گروه‌ها."
    )


@bot.message_handler(commands=["rules"])
def rules(message):
    text = group_rules.get(
        message.chat.id,
        "📜 قوانین هنوز تنظیم نشده‌اند.\n"
        "مدیر گروه می‌تواند با /setrules قوانین را ثبت کند."
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["setrules"])
def set_rules(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه می‌تواند قوانین را تغییر دهد.")
        return

    text = message.text.partition(" ")[2].strip()
    if not text:
        bot.reply_to(message, "روش استفاده:\n/setrules متن قوانین")
        return

    group_rules[message.chat.id] = "📜 قوانین گروه:\n\n" + text
    bot.reply_to(message, "✅ قوانین گروه ذخیره شد.")


@bot.message_handler(commands=["antilink"])
def anti_link_command(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or parts[1].lower() not in ("on", "off"):
        bot.reply_to(message, "استفاده:\n/antilink on\n/antilink off")
        return

    blocked_links[message.chat.id] = parts[1].lower() == "on"
    status = "فعال شد ✅" if blocked_links[message.chat.id] else "غیرفعال شد."
    bot.reply_to(message, f"🛡️ ضدلینک {status}")


@bot.message_handler(commands=["warn"])
def warn_user(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای اخطار، روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user
    if target.is_bot or is_admin(message.chat.id, target.id):
        bot.reply_to(message, "نمی‌توان به ربات یا مدیر گروه اخطار داد.")
        return

    key = (message.chat.id, target.id)
    warnings[key] += 1
    count = warnings[key]

    bot.reply_to(
        message,
        f"⚠️ اخطار برای {target.first_name}\n"
        f"تعداد اخطارها: {count}/3"
    )

    if count >= 3:
        warnings[key] = 0
        if not is_bot_admin(message.chat.id):
            bot.send_message(message.chat.id, "برای محدودسازی، به ربات دسترسی مدیریت بده.")
            return
        try:
            bot.restrict_chat_member(
                message.chat.id,
                target.id,
                permissions=types.ChatPermissions(can_send_messages=False)
            )
            bot.send_message(
                message.chat.id,
                f"🔇 {target.first_name} پس از ۳ اخطار به‌طور موقت محدود شد."
            )
        except Exception:
            bot.send_message(message.chat.id, "محدودسازی انجام نشد؛ دسترسی ربات را بررسی کن.")


@bot.message_handler(commands=["mute"])
def mute_user(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای سکوت، روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user
    if target.is_bot or is_admin(message.chat.id, target.id):
        bot.reply_to(message, "این کاربر قابل محدودسازی با این دستور نیست.")
        return
    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا به ربات دسترسی مدیریت بده.")
        return

    from datetime import datetime, timedelta, timezone
    until = datetime.now(timezone.utc) + timedelta(minutes=10)

    try:
        bot.restrict_chat_member(
            message.chat.id,
            target.id,
            permissions=types.ChatPermissions(can_send_messages=False),
            until_date=until
        )
        bot.reply_to(message, f"🔇 {target.first_name} برای ۱۰ دقیقه سکوت شد.")
    except Exception as e:
        bot.reply_to(message, f"محدودسازی ناموفق بود: {e}")


@bot.message_handler(commands=["unmute"])
def unmute_user(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user
    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا به ربات دسترسی مدیریت بده.")
        return

    try:
        bot.restrict_chat_member(
            message.chat.id,
            target.id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        bot.reply_to(message, f"🔊 محدودیت {target.first_name} برداشته شد.")
    except Exception:
        bot.reply_to(message, "رفع محدودیت انجام نشد؛ دسترسی ربات را بررسی کن.")


@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "برای مسدودسازی، روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user
    if target.is_bot or is_admin(message.chat.id, target.id):
        bot.reply_to(message, "نمی‌توان این کاربر را مسدود کرد.")
        return
    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا به ربات دسترسی مدیریت بده.")
        return

    try:
        bot.ban_chat_member(message.chat.id, target.id)
        bot.reply_to(message, f"🚫 {target.first_name} از گروه مسدود شد.")
    except Exception:
        bot.reply_to(message, "مسدودسازی انجام نشد؛ دسترسی ربات را بررسی کن.")


@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_group(message):
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        bot.reply_to(message, "استفاده:\n/unban شناسه_عددی_کاربر")
        return
    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا به ربات دسترسی مدیریت بده.")
        return

    try:
        bot.unban_chat_member(message.chat.id, int(parts[1]))
        bot.reply_to(message, "✅ درخواست رفع مسدودی انجام شد.")
    except Exception:
        bot.reply_to(message, "رفع مسدودی ناموفق بود.")


@bot.message_handler(content_types=["new_chat_members"])
def new_members(message):
    for user in message.new_chat_members:
        if not user.is_bot:
            bot.send_message(message.chat.id, welcome_text(user))


@bot.message_handler(
    content_types=["text", "photo", "video", "document", "animation", "sticker"]
)
def moderation(message):
    if not is_group(message) or not blocked_links[message.chat.id]:
        return
    if is_admin(message.chat.id, message.from_user.id):
        return

    text = message.text or message.caption or ""
    lowered = text.lower()
    if "http://" in lowered or "https://" in lowered or "t.me/" in lowered:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass


@app.get("/")
def health():
    return "MASIH GUARD PRO is running!", 200


@app.get("/health")
def health_check():
    return {"status": "ok", "bot": "MASIH GUARD PRO"}, 200


def run_bot():
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=25)


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

