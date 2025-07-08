import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
TASKS, WALLET = range(2)

def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("✅ I've Completed Tasks", callback_data='completed')]
    ]
    update.message.reply_text(
        "👋 Welcome to Mr. Kayblezzy Airdrop!\n\n"
        "📋 Complete these tasks:\n\n"
        "1. Join Telegram Channel ➜ https://t.me/Yakstaschannel\n"
        "2. Join Telegram Group ➜ https://t.me/yakstascapital\n"
        "3. Follow Twitter ➜ https://twitter.com/bigbangdist10\n\n"
        "Click below when done:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TASKS

def completed(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "🎉 Well done! Hope you didn't cheat the system!\n\n"
        "💰 Now send your SOLANA wallet address:"
    )
    return WALLET

def wallet(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    wallet_address = update.message.text
    
    update.message.reply_text(
        f"🚀 Congratulations {user.first_name}!\n\n"
        "✅ You've passed Mr. Kayblezzy Airdrop's call\n"
        "💸 100 SOL is on its way to your wallet!\n\n"
        "(Note: This is a test bot - no actual SOL will be sent)"
    )
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def main() -> None:
    TOKEN = os.environ.get('BOT_TOKEN')
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TASKS: [CallbackQueryHandler(completed, pattern='^completed$')],
            WALLET: [MessageHandler(Filters.text & ~Filters.command, wallet)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
