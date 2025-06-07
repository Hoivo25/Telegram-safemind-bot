from telegram import Update
from telegram.ext import ContextTypes
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
        parse_mode="Markdown"
    )

    context.user_data["awaiting_escrow_details"] = True


# Step 2: Handle user input with escrow details
async def handle_escrow_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_escrow_details"):
        print("User sent message but bot is not awaiting escrow details")
        return

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
    if not seller_username:
        await update.message.reply_text("❌ You must have a Telegram username to create an escrow.")
        return

    # Save the deal
    ESCROWS[seller_username] = {
        "amount": f"${amount}",
        "item": item,
        "buyer": None
    }

    context.user_data["awaiting_escrow_details"] = False

    await update.message.reply_text("✅ Escrow created and waiting for buyer to join.")


# Register handlers (if still needed independently)
def register_handlers(app):
    # You can leave this empty or remove it entirely if you're using router.py
    pass