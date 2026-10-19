
import os
import re
import threading
from datetime import datetime, timedelta, timezone
from collections import defaultdict

import telebot
from telebot import types
from flask import Flask

# ==========================================
# MASIH GUARD PRO
# Developer: Masih Hackring
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOPER_NAME = "کدنویس مسیح هکرینگ | Masih Hackring"
DEVELOPER_CONTACT = "@Ma3ih01"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN در Environment تنظیم نشده است.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# اطلاعات موقت؛ پس از ری‌استارت پاک می‌شوند
warnings = defaultdict(int)
group_rules = {}
blocked_links = defaultdict(bool)

# تشخیص لینک در متن و کپشن
LINK_PATTERN = re.compile(
    r"""(?ix)
    (?:https?://|www\.)[^\s<>]+
    |(?:t\.me|telegram\.me)/[^\s<>]+
    |(?<![@\w.-])
      (?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+
      [a-z]{2,}
      (?:/[^\s<>]*)?
    """
)


def is_group(message):
    return message.chat.type in ("group", "supergroup")


def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except Exception as error:
        print(f"Admin check error: {error}")
        return False


def is_bot_admin(chat_id):
    try:
        member = bot.get_chat_member(chat_id, bot.get_me().id)
        return member.status in ("creator", "administrator")
    except Exception as error:
        print(f"Bot admin check error: {error}")
        return False


def welcome_text(user):
    name = user.first_name or "دوست عزیز"
    return (
        f"سلام {name} عزیز! 👋💜\n\n"
        "به جمع ما خوش اومدی.\n"
        "لطفاً قوانین گروه رو رعایت کن.\n\n"
        "🛡️ محافظ گروه: MASIH GUARD PRO"
    )


def can_moderate(message):
    return (
        is_group(message)
        and message.from_user is not None
        and is_admin(message.chat.id, message.from_user.id)
    )


# ------------------------------------------
# START
# ------------------------------------------

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
        "/warn — اخطار با ریپلای (مدیر)\n"
        "/mute — سکوت ۱۰ دقیقه‌ای با ریپلای (مدیر)\n"
        "/unmute — رفع سکوت با ریپلای (مدیر)\n"
        "/ban — مسدودسازی با ریپلای (مدیر)\n"
        "/unban شناسه — رفع مسدودی (مدیر)\n\n"
        "ربات برای مدیریت اعضا باید ادمین گروه باشد."
    )


@bot.message_handler(commands=["about"])
def about(message):
    bot.reply_to(
        message,
        "💎 MASIH GUARD PRO\n"
        "نسخه مدیریت گروه با Python\n\n"
        "👨‍💻 کدنویس: مسیح مختاری\n"
        "🌐 Masih Hackring\n"
        f"📩 ارتباط: {DEVELOPER_CONTACT}"
    )


# ------------------------------------------
# GROUP RULES
# ------------------------------------------

@bot.message_handler(commands=["rules"])
def rules(message):
    text = group_rules.get(
        message.chat.id,
        "📜 قوانین هنوز تنظیم نشده‌اند.\n"
        "مدیر گروه می‌تواند با /setrules متن قوانین را ثبت کند."
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=["setrules"])
def set_rules(message):
    if not is_group(message):
        bot.reply_to(message, "این دستور را داخل گروه اجرا کن.")
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه می‌تواند قوانین را تغییر دهد.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        bot.reply_to(message, "روش استفاده:\n/setrules متن قوانین")
        return

    group_rules[message.chat.id] = (
        "📜 قوانین گروه:\n\n" + parts[1].strip()
    )
    bot.reply_to(message, "✅ قوانین گروه ذخیره شد.")


# ------------------------------------------
# ANTI-LINK SETTINGS
# ------------------------------------------

@bot.message_handler(commands=["antilink"])
def anti_link_command(message):
    if not is_group(message):
        bot.reply_to(message, "این دستور را داخل گروه اجرا کن.")
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) != 2 or parts[1].lower().strip() not in ("on", "off"):
        bot.reply_to(
            message,
            "روش استفاده:\n/antilink on\n/antilink off"
        )
        return

    enabled = parts[1].lower().strip() == "on"
    blocked_links[message.chat.id] = enabled

    if enabled:
        bot.reply_to(message, "🛡️ ضدلینک فعال شد ✅")
    else:
        bot.reply_to(message, "🔓 ضدلینک غیرفعال شد.")


# ------------------------------------------
# WARN
# ------------------------------------------

@bot.message_handler(commands=["warn"])
def warn_user(message):
    if not is_group(message):
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "برای اخطار، روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user

    if not target or target.is_bot or is_admin(message.chat.id, target.id):
        bot.reply_to(message, "نمی‌توان به این کاربر اخطار داد.")
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
        if not is_bot_admin(message.chat.id):
            bot.send_message(
                message.chat.id,
                "برای محدودسازی، ربات باید ادمین باشد."
            )
            return

        try:
            until = datetime.now(timezone.utc) + timedelta(minutes=10)
            bot.restrict_chat_member(
                message.chat.id,
                target.id,
                permissions=types.ChatPermissions(
                    can_send_messages=False
                ),
                until_date=until
            )
            warnings[key] = 0
            bot.send_message(
                message.chat.id,
                f"🔇 {target.first_name} پس از ۳ اخطار، "
                "برای ۱۰ دقیقه محدود شد."
            )
        except Exception as error:
            print(f"Warn restriction error: {error}")
            bot.send_message(
                message.chat.id,
                "محدودسازی ناموفق بود؛ دسترسی ربات را بررسی کن."
            )


# ------------------------------------------
# MUTE / UNMUTE
# ------------------------------------------

@bot.message_handler(commands=["mute"])
def mute_user(message):
    if not is_group(message):
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "برای سکوت، روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user

    if not target or target.is_bot or is_admin(message.chat.id, target.id):
        bot.reply_to(message, "این کاربر قابل محدودسازی نیست.")
        return

    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا ربات را ادمین گروه کن.")
        return

    try:
        until = datetime.now(timezone.utc) + timedelta(minutes=10)
        bot.restrict_chat_member(
            message.chat.id,
            target.id,
            permissions=types.ChatPermissions(
                can_send_messages=False
            ),
            until_date=until
        )
        bot.reply_to(
            message,
            f"🔇 {target.first_name} برای ۱۰ دقیقه سکوت شد."
        )
    except Exception as error:
        print(f"Mute error: {error}")
        bot.reply_to(message, "سکوت ناموفق بود؛ دسترسی ربات را بررسی کن.")


@bot.message_handler(commands=["unmute"])
def unmute_user(message):
    if not is_group(message):
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user

    if not target:
        bot.reply_to(message, "کاربر پیدا نشد.")
        return

    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا ربات را ادمین گروه کن.")
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
        bot.reply_to(
            message,
            f"🔊 درخواست رفع سکوت {target.first_name} انجام شد."
        )
    except Exception as error:
        print(f"Unmute error: {error}")
        bot.reply_to(message, "رفع سکوت ناموفق بود؛ دسترسی ربات را بررسی کن.")


# ------------------------------------------
# BAN / UNBAN
# ------------------------------------------

@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not is_group(message):
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "برای مسدودسازی، روی پیام کاربر ریپلای کن.")
        return

    target = message.reply_to_message.from_user

    if not target or target.is_bot or is_admin(message.chat.id, target.id):
        bot.reply_to(message, "نمی‌توان این کاربر را مسدود کرد.")
        return

    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا ربات را ادمین گروه کن.")
        return

    try:
        bot.ban_chat_member(message.chat.id, target.id)
        bot.reply_to(message, f"🚫 {target.first_name} از گروه مسدود شد.")
    except Exception as error:
        print(f"Ban error: {error}")
        bot.reply_to(message, "مسدودسازی ناموفق بود؛ دسترسی ربات را بررسی کن.")


@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_group(message):
        return

    if not can_moderate(message):
        bot.reply_to(message, "⛔ فقط مدیر گروه مجاز است.")
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) != 2 or not parts[1].lstrip("-").isdigit():
        bot.reply_to(message, "استفاده:\n/unban شناسه_عددی_کاربر")
        return

    if not is_bot_admin(message.chat.id):
        bot.reply_to(message, "ابتدا ربات را ادمین گروه کن.")
        return

    try:
        bot.unban_chat_member(message.chat.id, int(parts[1]))
        bot.reply_to(message, "✅ درخواست رفع مسدودی انجام شد.")
    except Exception as error:
        print(f"Unban error: {error}")
        bot.reply_to(message, "رفع مسدودی ناموفق بود.")


# ------------------------------------------
# WELCOME NEW MEMBERS
# ------------------------------------------

@bot.message_handler(content_types=["new_chat_members"])
def new_members(message):
    for user in message.new_chat_members:
        if not user.is_bot:
            bot.send_message(
                message.chat.id,
                welcome_text(user)
            )


# ------------------------------------------
# REAL ANTI-LINK FILTER
# Must be after command handlers.
# ------------------------------------------

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "animation",
        "sticker",
        "audio",
        "voice",
        "video_note"
    ]
)
def moderation(message):
    if not is_group(message):
        return

    if not blocked_links.get(message.chat.id, False):
        return

    if not message.from_user:
        return

    # مدیران از فیلتر ضدلینک مستثنا هستند
    if is_admin(message.chat.id, message.from_user.id):
        return

    text = message.text or message.caption or ""

    if not text or not LINK_PATTERN.search(text):
        return

    try:
        bot.delete_message(
            message.chat.id,
            message.message_id
        )
        print(f"Anti-link: deleted message in {message.chat.id}")
    except Exception as error:
        print(f"Anti-link deletion failed: {error}")


# ------------------------------------------
# RENDER HEALTH CHECKS
# ------------------------------------------

@app.get("/")
def health():
    return "MASIH GUARD PRO is running!", 200


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "bot": "MASIH GUARD PRO"
    }, 200


# ------------------------------------------
# START BOT AND WEB SERVER
# ------------------------------------------

def run_bot():
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=25
    )


if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
