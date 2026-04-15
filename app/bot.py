import os
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters,
)
from telegram.constants import ParseMode

from app.vision import analyze_image
from app.rules import check
from app.formatter import build_message, build_history_message
from app.db import init_db, log_query, get_user_history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *NutriScan Bot*\n\n"
        "Send me a photo of any food's *nutrition facts label* and I'll break it down "
        "for you — including health warnings if anything looks concerning.\n\n"
        "Commands:\n"
        "/history — see your last 5 scans",
        parse_mode=ParseMode.MARKDOWN,
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_user_history(str(update.effective_user.id))
    await update.message.reply_text(build_history_message(rows), parse_mode=ParseMode.MARKDOWN)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text("🔍 Scanning your nutrition label, please wait...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()

        nutrients = await analyze_image(bytes(image_bytes))
        flags = check(nutrients)
        reply = build_message(nutrients, flags)

        log_query(
            user_id=str(user.id),
            username=user.username,
            image_file=photo.file_id,
            result=reply,
            had_warnings=len(flags) > 0,
        )
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    except ValueError as e:
        logger.warning("Vision parse error: %s", e)
        await update.message.reply_text(
            "❌ I couldn't read the label clearly.\n"
            "Please send a well-lit, close-up photo and try again."
        )
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        await update.message.reply_text("⚠️ Something went wrong. Please try again.")


def create_app():
    init_db()
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(60)
        .write_timeout(60)
        .media_write_timeout(60)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    return app