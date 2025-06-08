
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Create Escrow", callback_data="create_escrow"),
         InlineKeyboardButton("🤝 Join Escrow", callback_data="join_escrow")],
        [InlineKeyboardButton("🔍 View All Escrows", callback_data="view_escrows"),
         InlineKeyboardButton("📊 My Trades", callback_data="my_trades")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile"),
         InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = "🔐 *Welcome to Escrow Bot!*\n\nSecure trading made simple. Choose an option below:"

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

def register_handlers(app):
    app.add_handler(CommandHandler("start", show_main_menu))
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="back_to_menu"))
