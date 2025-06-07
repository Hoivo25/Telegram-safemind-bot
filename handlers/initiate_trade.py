from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from utils import ESCROWS

# Step 1: Show instructions when user clicks "Create Escrow"
async def create_escrow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    instructions = (
        "📝 *Create Escrow*\n\n"
        "Please send the escrow details in the following format:\n"
        "`amount | item name | @buyer_username`\n\n"
        "Example:\n"
        "`100 | iPhone 12 | @john_doe`\n\n"
        "Once submitted, the buyer can join the trade."
    )

    await query.edit_message_text(
        text=instructions,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")
        ]])
    )

    context.user_data["awaiting_escrow_details"] = True


# Step 2: Handle the user's input message after pressing create escrow
async def handle_escrow_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_escrow_details"):
        return  # Ignore if not in the flow

    text = update.message.text
    try:
        amount, item, buyer = map(str.strip, text.split("|"))
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please use:\n\n`100 | Item name | @buyer_username`",
            parse_mode="Markdown"
        )
        return

    seller_username = update.effective_user.username
    seller_id = update.effective_user.id

    if not seller_username:
        await update.message.reply_text("❌ You must have a Telegram username to create an escrow.")
        return

    ESCROWS[seller_username] = {
        "seller_id": seller_id,
        "amount": f"${amount}",
        "item": item,
        "buyer": None,
        "status": "pending"
    }

    context.user_data["awaiting_escrow_details"] = False

    await update.message.reply_text("✅ Escrow created and waiting for buyer to join.")


# Register these handlers
def register_handlers(app):
    app.add_handler(CallbackQueryHandler(create_escrow_handler, pattern="^create_escrow$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_escrow_details))