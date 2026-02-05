import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    PicklePersistence
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Render provides the PORT environment variable. If it exists, we are on Render.
PORT = int(os.environ.get("PORT", "8443"))
# Your Render App URL (e.g., https://my-bot.onrender.com). Required for Webhooks.
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") 

# Conversation States
Q1, Q2, Q3, Q4, Q5 = range(5)

# --- QUESTIONS ---
QUESTIONS = [
    "Question 1/5: What is your primary goal with digital marketing? (e.g., Brand Awareness, Sales, Leads)",
    "Question 2/5: What is your approximate monthly budget for ads?",
    "Question 3/5: Which social media platform is your target audience most active on?",
    "Question 4/5: Do you currently have a website or landing page?",
    "Question 5/5: How many years of experience do you have in your industry?"
]

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation if the weekly limit hasn't been reached."""
    user = update.effective_user
    user_data = context.user_data

    # Check for Weekly Limit
    last_completed = user_data.get("last_completed_date")
    
    if last_completed:
        # Calculate time difference
        time_since_last = datetime.now() - last_completed
        days_remaining = 7 - time_since_last.days
        
        if time_since_last < timedelta(days=7):
            await update.message.reply_text(
                f"⚠️ You have already completed the challenge this week.\n"
                f"Please come back in {days_remaining} days for a new challenge!"
            )
            return ConversationHandler.END

    await update.message.reply_text(
        f"👋 Hello {user.first_name}! Welcome to the Digital Marketing Challenge.\n\n"
        "I will ask you 5 questions to assess your needs. Let's get started!"
    )
    
    # Ask Question 1
    await update.message.reply_text(QUESTIONS[0])
    return Q1

async def answer_q1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q1_answer'] = update.message.text
    await update.message.reply_text(QUESTIONS[1])
    return Q2

async def answer_q2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q2_answer'] = update.message.text
    await update.message.reply_text(QUESTIONS[2])
    return Q3

async def answer_q3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q3_answer'] = update.message.text
    await update.message.reply_text(QUESTIONS[3])
    return Q4

async def answer_q4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q4_answer'] = update.message.text
    await update.message.reply_text(QUESTIONS[4])
    return Q5

async def answer_q5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q5_answer'] = update.message.text
    
    # Save completion time
    context.user_data['last_completed_date'] = datetime.now()

    # (Optional) Here you would process or email the answers
    answers = context.user_data
    summary = (
        f"✅ Challenge Completed!\n\n"
        f"1. Goal: {answers.get('q1_answer')}\n"
        f"2. Budget: {answers.get('q2_answer')}\n"
        f"3. Platform: {answers.get('q3_answer')}\n"
        f"4. Website: {answers.get('q4_answer')}\n"
        f"5. Experience: {answers.get('q5_answer')}\n"
    )

    await update.message.reply_text(summary)
    await update.message.reply_text(
        "🎉 Thank you! You've finished this week's questions.\n"
        "Come back next week for a new challenge."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Operation cancelled. Type /start to try again.")
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable is missing.")
        return

    # Persistence: Saves user data (answers & dates) to a file.
    # NOTE: On Render Free Tier, this file resets if the server restarts.
    # For permanent storage, you would need a database.
    persistence = PicklePersistence(filepath="bot_data.pickle")

    # Build the Application
    application = Application.builder().token(TOKEN).persistence(persistence).build()

    # Add Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_q1)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_q2)],
            Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_q3)],
            Q4: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_q4)],
            Q5: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_q5)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # --- DEPLOYMENT LOGIC ---
    if WEBHOOK_URL:
        # We are on Render (or a server with a public URL)
        print(f"Starting Webhook on Port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
    else:
        # We are running locally
        print("Starting Polling (Local Mode)...")
        application.run_polling()

if __name__ == "__main__":
    main()
