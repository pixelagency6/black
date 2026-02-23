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
PORT = int(os.environ.get("PORT", "8443"))
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Conversation States
Q1, Q2, Q3, Q4, Q5 = range(5)

# --- QUESTIONS with Emojis ---
QUESTIONS = [
    "🎯 **Question 1/5:** What is your primary goal with digital marketing? (e.g., Brand Awareness 📢, Sales 💰, Leads 📝)",
    "💸 **Question 2/5:** What is your approximate monthly budget for ads? (e.g., $500, $5k, $10k+)",
    "📱 **Question 3/5:** Which social media platform is your target audience most active on? (Instagram, TikTok, LinkedIn, etc.)",
    "🌐 **Question 4/5:** Do you currently have a website or landing page? (Yes/No – tell us a bit about it!)",
    "⏳ **Question 5/5:** How many years of experience do you have in your industry? (e.g., 2 years, just starting 🆕, veteran 🏆)"
]

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation with a warm welcome and checks weekly limit."""
    user = update.effective_user
    user_data = context.user_data

    # Check for Weekly Limit
    last_completed = user_data.get("last_completed_date")

    if last_completed:
        time_since_last = datetime.now() - last_completed
        days_remaining = 7 - time_since_last.days
        if time_since_last < timedelta(days=7):
            await update.message.reply_text(
                f"⏳ **Hold on,** {user.first_name}! You've already completed the challenge this week.\n"
                f"Come back in **{days_remaining} day{'s' if days_remaining != 1 else ''}** for a fresh set of questions. 🌟"
            )
            return ConversationHandler.END

    welcome_msg = (
        f"👋 **Hello {user.first_name}!** Welcome to the **Digital Marketing Challenge**!\n\n"
        "I'm your marketing assistant 🤖, and I'll ask you **5 fun questions** to understand your needs better.\n"
        "Answer each one, and at the end, I'll summarize your profile.\n\n"
        "Ready? Let's dive in! 🚀\n\n"
        f"{QUESTIONS[0]}"
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    return Q1

async def answer_q1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores first answer and moves to Q2 with encouragement."""
    context.user_data['q1_answer'] = update.message.text
    await update.message.reply_text(
        f"✅ Got it! Great start. Now, next question:\n\n{QUESTIONS[1]}",
        parse_mode='Markdown'
    )
    return Q2

async def answer_q2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q2_answer'] = update.message.text
    await update.message.reply_text(
        f"💰 Thanks for sharing! Budget is key. Moving on...\n\n{QUESTIONS[2]}",
        parse_mode='Markdown'
    )
    return Q3

async def answer_q3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q3_answer'] = update.message.text
    await update.message.reply_text(
        f"📱 Awesome! Knowing your audience's platform is half the battle.\n\n{QUESTIONS[3]}",
        parse_mode='Markdown'
    )
    return Q4

async def answer_q4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q4_answer'] = update.message.text
    await update.message.reply_text(
        f"🌐 Perfect! Almost there – just one more question.\n\n{QUESTIONS[4]}",
        parse_mode='Markdown'
    )
    return Q5

async def answer_q5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores final answer, saves completion time, and presents a vibrant summary."""
    context.user_data['q5_answer'] = update.message.text
    context.user_data['last_completed_date'] = datetime.now()

    answers = context.user_data
    summary = (
        f"🎉 **Challenge Completed!** 🎉\n\n"
        f"Here's your marketing profile snapshot:\n\n"
        f"🎯 **Goal:** {answers.get('q1_answer')}\n"
        f"💸 **Budget:** {answers.get('q2_answer')}\n"
        f"📱 **Platform:** {answers.get('q3_answer')}\n"
        f"🌐 **Website:** {answers.get('q4_answer')}\n"
        f"⏳ **Experience:** {answers.get('q5_answer')}\n\n"
        f"✨ *You're all set for this week!* ✨\n"
        f"Come back in 7 days for a new challenge. Until then, keep crushing your marketing goals! 💪🚀"
    )

    await update.message.reply_text(summary, parse_mode='Markdown')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation politely."""
    await update.message.reply_text(
        "❌ **Operation cancelled.** No worries – you can start over anytime with /start. 😊"
    )
    return ConversationHandler.END

def main() -> None:
    if not TOKEN:
        logger.error("Error: TELEGRAM_TOKEN environment variable is missing.")
        return

    persistence = PicklePersistence(filepath="bot_data.pickle")
    application = Application.builder().token(TOKEN).persistence(persistence).build()

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

    if WEBHOOK_URL:
        logger.info(f"Starting Webhook on Port {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{TOKEN}"
        )
    else:
        logger.info("Starting Polling (Local Mode)...")
        application.run_polling()

if __name__ == "__main__":
    main()
