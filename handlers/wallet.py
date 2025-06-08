
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils import USER_WALLETS

async def show_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet management menu"""
    query = update.callback_query
    await query.answer()
    
    username = update.effective_user.username
    if not username:
        await query.edit_message_text("❌ You need to set a username in Telegram to use this feature.")
        return
    
    # Initialize user wallet if not exists
    if username not in USER_WALLETS:
        USER_WALLETS[username] = {}
    
    wallets = USER_WALLETS[username]
    
    message = f"💳 *Wallet Management*\n\n"
    message += f"Your saved wallet addresses:\n\n"
    
    if not wallets:
        message += "No wallets saved yet.\n\n"
    else:
        for currency, address in wallets.items():
            message += f"💰 {currency.upper()}: `{address}`\n"
        message += "\n"
    
    message += "Add or update your wallet addresses for automatic payments:"
    
    keyboard = [
        [InlineKeyboardButton("₿ Add/Update BTC", callback_data="add_wallet_btc")],
        [InlineKeyboardButton("💎 Add/Update ETH", callback_data="add_wallet_eth")],
        [InlineKeyboardButton("💵 Add/Update USDT", callback_data="add_wallet_usdt")],
        [InlineKeyboardButton("💰 Add/Update USDC", callback_data="add_wallet_usdc")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ]
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def initiate_wallet_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate wallet address addition"""
    query = update.callback_query
    await query.answer()
    
    currency = query.data.replace("add_wallet_", "")
    context.user_data["awaiting_wallet"] = currency
    context.user_data["awaiting_escrow_details"] = False
    context.user_data["awaiting_join"] = False
    
    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="wallet_menu")]]
    
    await query.edit_message_text(
        f"💳 *Add {currency.upper()} Wallet*\n\n"
        f"Please send your {currency.upper()} wallet address.\n\n"
        f"⚠️ *Important:*\n"
        f"• Double-check the address before sending\n"
        f"• Make sure it's a valid {currency.upper()} address\n"
        f"• This will be used for automatic payments",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_wallet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet address input"""
    username = update.effective_user.username
    currency = context.user_data.get("awaiting_wallet")
    wallet_address = update.message.text.strip()
    
    if not username:
        await update.message.reply_text("❌ You need to set a username in Telegram.")
        return
    
    # Initialize user wallet if not exists
    if username not in USER_WALLETS:
        USER_WALLETS[username] = {}
    
    # Save wallet address
    USER_WALLETS[username][currency] = wallet_address
    
    await update.message.reply_text(
        f"✅ *{currency.upper()} Wallet Saved!*\n\n"
        f"Address: `{wallet_address}`\n\n"
        f"This address will be used for automatic payments.",
        parse_mode="Markdown"
    )
    
    # Reset state
    context.user_data["awaiting_wallet"] = None
    
    # Show wallet menu again
    keyboard = [[InlineKeyboardButton("💳 Back to Wallets", callback_data="wallet_menu")]]
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register_handlers(app):
    app.add_handler(CallbackQueryHandler(show_wallet_menu, pattern="^wallet_menu$"))
    app.add_handler(CallbackQueryHandler(initiate_wallet_addition, pattern="^add_wallet_"))
