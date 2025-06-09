
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

    welcome_text = """🔐 *Welcome to Escrow Bot!*

🌟 *Your Trusted Trading Partner*
We believe in complete transparency and security for every trade.

🛡️ *What Makes Us Different:*
• All trades are secured through blockchain escrow
• Zero hidden fees - you see exactly what you pay
• Open-source security protocols
• 24/7 automated dispute resolution
• Real-time trade status tracking

💎 *Transparency Promise:*
• Fee Structure: Clearly displayed before each trade
• Trade History: Full audit trail for all transactions  
• Security: Multi-signature wallet protection
• Support: Direct access to human moderators

🚀 *Ready to trade safely?* Choose an option below:"""

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with potential deep link parameters"""
    args = context.args
    
    # Check if this is a join link
    if args and args[0].startswith("join_"):
        seller_username = args[0].replace("join_", "")
        await handle_join_link(update, context, seller_username)
        return
    
    # Regular start command
    await show_main_menu(update, context)

async def handle_join_link(update: Update, context: ContextTypes.DEFAULT_TYPE, seller_username: str):
    """Handle joining escrow via deep link"""
    from utils import ESCROWS
    
    buyer_username = update.effective_user.username
    buyer_id = update.effective_user.id

    if not buyer_username:
        await update.message.reply_text("❌ You need to set a username in Telegram to use this bot.")
        return

    if seller_username not in ESCROWS:
        await update.message.reply_text("❌ No active escrow found for that seller.")
        return

    escrow = ESCROWS[seller_username]
    
    if escrow["status"] != "pending":
        await update.message.reply_text("❌ This escrow is no longer available to join.")
        return

    if escrow.get("buyer"):
        await update.message.reply_text("❌ This escrow already has a buyer.")
        return

    # Show escrow details with join option
    message = f"🔗 *Quick Join Escrow*\n\n"
    message += f"👤 Seller: @{seller_username}\n"
    message += f"💰 Amount: {escrow['amount']}\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"📊 Status: {escrow['status'].title()}\n\n"
    message += f"Do you want to join this escrow?"

    keyboard = [
        [InlineKeyboardButton("✅ Join Escrow", callback_data=f"confirm_join_{seller_username}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu")]
    ]

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def register_handlers(app):
    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="back_to_menu"))
