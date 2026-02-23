import os
import logging
import asyncio
from datetime import datetime, timezone

# python-telegram-bot imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    PicklePersistence
)
from telegram.error import Forbidden, BadRequest

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
# This single variable handles the text for both /start and the 6-hour broadcast
PROMO_TEXT = (
    "👋 Welcome to MegaX Asia Assistance Bot!\n\n"
    "🎁 EXCLUSIVE BONUS: Register now and claim your FREE BONUS instantly! 💰✨\n\n"
    "Try our bot right now and experience the power of MegaX! The most advanced system is ready for you! 🤖⚡️\n\n"
    "✅ Direct HQ Support\n"
    "✅ Top-Rated Secure Platform\n"
    "✅ Instant Withdrawal Guaranteed\n\n"
    "⚡️ MEGA888 | PUSSY888 | 918KISS ⚡️\n\n"
    "🎁 150% Welcome Bonus\n"
    "🎁 50% Recommend Bonus\n"
    "🎁 Daily Receipts Combo: RM 58.64\n"
    "🎁 Weekly Receipts Combo: RM 246.64\n"
    "🎁 Share & Earn 10"
)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes the user and registers them for the 6-hour broadcast."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 1. Store the user's chat_id in bot_data for broadcasting
    # Using a set to avoid duplicates
    if "user_list" not in context.bot_data:
        context.bot_data["user_list"] = set()
    
    context.bot_data["user_list"].add(chat_id)

    # 2. Send the Welcome/Redirect message using the new promo text
    keyboard = [[InlineKeyboardButton("🧧 CLAIM BONUS NOW", url=f"https://t.me/{TARGET_BOT[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Attempt to send the video/gif with the text as a caption
    try:
        with open("Gif Bot.mp4", "rb") as media_file:
            await update.message.reply_animation(
                animation=media_file,
                caption=PROMO_TEXT,
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        logger.warning("Media file 'Gif Bot.mp4' not found. Sending text only.")
        await update.message.reply_text(
            text=PROMO_TEXT,
            reply_markup=reply_markup
        )

async def broadcast_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global job that sends the reminder to all registered users every 6 hours."""
    user_list = context.bot_data.get("user_list", set())
    
    if not user_list:
        return

    logger.info(f"Starting broadcast to {len(user_list)} users.")
    
    keyboard = [[InlineKeyboardButton("🧧 CLAIM BONUS NOW", url=f"https://t.me/{TARGET_BOT[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for chat_id in list(user_list):
        try:
            # Sending the promo text in the 6-hour broadcast reminder
            await context.bot.send_message(
                chat_id=chat_id,
                text=PROMO_TEXT,
                reply_markup=reply_markup
            )
            # Small delay to respect Telegram's rate limits (30 messages per second)
            await asyncio.sleep(0.05) 
        except Forbidden:
            # User blocked the bot, remove them from the list
            user_list.remove(chat_id)
            logger.info(f"Removed user {chat_id} (Bot blocked)")
        except BadRequest as e:
            logger.error(f"Error sending to {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error for {chat_id}: {e}")

def main() -> None:
    """Sets up and runs the bot."""
    if not TOKEN:
        logger.error("No TELEGRAM_TOKEN found in environment variables.")
        return

    # Initialize Persistence (stores user_list across restarts)
    persistence = PicklePersistence(filepath="bot_persistence.pickle")

    # Build the Application
    application = (
        Application.builder()
        .token(TOKEN)
        .persistence(persistence)
        .build()
    )

    # Add /start handler
    application.add_handler(CommandHandler("start", start))

    # Schedule the Global Broadcast Job (Every 6 hours)
    # 21600 seconds = 6 hours
    job_queue = application.job_queue
    job_queue.run_repeating(broadcast_reminder, interval=21600, first=10)

    # Deployment Strategy
    if WEBHOOK_URL:
        # Webhook Mode (Production)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
    else:
        # Polling Mode (Local)
        application.run_polling()

if __name__ == "__main__":
    main()
