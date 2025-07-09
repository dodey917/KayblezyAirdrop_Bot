import logging
import sqlite3
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler
)

# Get environment variables
BOT_TOKEN = os.environ.get('7705705814:AAG5R0uOm-ZJfFzi32i2xE1vnl-3QVc9ETs')
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

ADMIN_USER_ID = os.environ.get('5584801763')
if not ADMIN_USER_ID:
    raise RuntimeError("ADMIN_USER_ID environment variable not set")

# Conversation states
VERIFY_SOCIALS, GET_WALLET = range(2)

# Initialize database
conn = sqlite3.connect('airdrop.db', check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        wallet_address TEXT UNIQUE
    )
''')
conn.commit()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Bot Handlers =====
def start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user

    # Check if user exists
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (user.id,))
    if cursor.fetchone():
        update.message.reply_text("You've already participated in this airdrop!")
        return ConversationHandler.END

    # Create verification keyboard
    keyboard = [
        [InlineKeyboardButton("✅ Verify Channel", url='https://t.me/Yakstaschannel')],
        [InlineKeyboardButton("✅ Verify Group", url='https://t.me/yakstascapital')],
        [InlineKeyboardButton("✅ Verify Twitter", url='https://twitter.com/bigbangdist10')],
        [InlineKeyboardButton("🔁 I Have Completed All Tasks", callback_data='completed_tasks')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "🔥 *Welcome to Mr Kayblezzy2's Airdrop!* 🔥\n\n"
        "To participate, please complete these steps:\n"
        "1. Join our [Telegram Channel](https://t.me/Yakstaschannel)\n"
        "2. Join our [Telegram Group](https://t.me/yakstascapital)\n"
        "3. Follow our [Twitter Account](https://twitter.com/bigbangdist10)\n\n"
        "After completing all steps, click the button below:",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

    return VERIFY_SOCIALS

def handle_verification(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user = query.from_user

    if query.data == 'completed_tasks':
        # Send congratulations message
        context.bot.send_message(
            chat_id=user.id,
            text="🎉 *CONGRATULATIONS!*\n\n"
                 "You've passed Mr Kayblezzy2's airdrop call!\n"
                 "*100 SOL will be sent to your wallet* 💰\n\n"
                 "Please submit your Solana wallet address now:",
            parse_mode='Markdown'
        )
        
        # Prepare for wallet input
        context.bot.send_message(
            chat_id=user.id,
            text="👇 Enter your Solana wallet address:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Cancel")]], 
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
        return GET_WALLET
    return VERIFY_SOCIALS

def handle_wallet(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    wallet_address = update.message.text.strip()

    # Basic Solana address validation
    if len(wallet_address) < 32 or len(wallet_address) > 44:
        update.message.reply_text(
            "⚠️ *Invalid Solana address!*\n"
            "Please enter a valid wallet address:",
            parse_mode='Markdown'
        )
        return GET_WALLET

    # Save user data
    try:
        cursor.execute('''
            INSERT INTO users (telegram_id, username, wallet_address)
            VALUES (?, ?, ?)
        ''', (user.id, user.username, wallet_address))
        conn.commit()
        
        # Send success message
        update.message.reply_text(
            "🚀 *Congratulations!*\n\n"
            "10 SOL is on its way to your address!\n\n"
            "Transaction details will appear here soon...",
            parse_mode='Markdown'
        )
        
        # Notify admin
        context.bot.send_message(
            ADMIN_USER_ID,
            f"🔥 New Airdrop Participant:\n\n"
            f"User: @{user.username}\n"
            f"Wallet: `{wallet_address}`",
            parse_mode='Markdown'
        )
        
    except sqlite3.IntegrityError:
        update.message.reply_text(
            "❌ You've already participated in this airdrop!"
        )

    return ConversationHandler.END

def export_data(update: Update, context: CallbackContext) -> None:
    """Admin command to export user data"""
    if str(update.effective_user.id) != ADMIN_USER_ID:
        update.message.reply_text("❌ Unauthorized")
        return

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    if not users:
        update.message.reply_text("No participants yet")
        return

    csv_data = "ID,Telegram ID,Username,Wallet\n"
    for user in users:
        csv_data += f"{user[0]},{user[1]},{user[2] or ''},{user[3]}\n"
    
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=csv_data.encode(),
        filename='airdrop_participants.csv'
    )

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Registration canceled.")
    return ConversationHandler.END

# ===== Main Application =====
def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            VERIFY_SOCIALS: [CallbackQueryHandler(handle_verification)],
            GET_WALLET: [MessageHandler(Filters.text & ~Filters.command, handle_wallet)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('export', export_data))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
