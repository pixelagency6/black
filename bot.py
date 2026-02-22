import os
import logging
from datetime import datetime, time, timezone

# python-telegram-bot imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PORT = int(os.environ.get("PORT", "8443"))
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") 
TARGET_BOT = "@megax_asia_bot"

# --- NOTIFICATION CONTENT ---
REMINDER_TEXT = (
    "🔥 **THE GAME IS HOT!** 🔥\n\n"
    "Amazing animations and massive jackpots are waiting for you right now. "
    "Don't miss out on your winning streak! 🎰✨\n\n"
    "🚀 **WIN NOW at @megax_asia_bot**"
)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes the user, provides the redirect link, and schedules reminders."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Welcome and Redirect Message
    keyboard = [[InlineKeyboardButton("🚀 Start Winning Now!", url=f"https://t.me/{TARGET_BOT[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Welcome to **MegaX Asia Assistance Bot**!\n\n"
        f"Please click the button below to start winning and earn jackpots at {TARGET_BOT}! 🎰💰",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    # Schedule the recurring reminder if not already scheduled for this user
    job_name = f"reminder_{chat_id}"
    current_jobs = context.job_queue.get_jobs_by_name(job_name)
    
    if not current_jobs:
        # Schedule every 6 hours (21600 seconds)
        context.job_queue.run_repeating(
            send_reminder, 
            interval=21600, 
            first=21600, 
            chat_id=chat_id, 
            name=job_name
        )
        logger.info(f"Scheduled 6hr reminders for user {chat_id}")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job function that sends the 'Game is Hot' reminder."""
    job = context.job
    keyboard = [[InlineKeyboardButton("🎰 PLAY NOW", url=f"https://t.me/{TARGET_BOT[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=job.chat_id,
            text=REMINDER_TEXT,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Could not send reminder to {job.chat_id}: {e}")

def main() -> None:
    """Sets up and runs the bot."""
    if not TOKEN:
        logger.error("No TELEGRAM_TOKEN found in environment variables.")
        return

    # Initialize Persistence
    persistence = PicklePersistence(filepath="bot_persistence.pickle")

    # Build the Application with JobQueue support
    application = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .build()
    )

    # Simple command handler
    application.add_handler(CommandHandler("start", start))

    # Deployment Strategy
    if WEBHOOK_URL:
        # Webhook Mode
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
    else:
        # Polling Mode
        application.run_polling()

if __name__ == "__main__":
    main()
