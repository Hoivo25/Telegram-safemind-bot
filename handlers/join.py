from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from utils import ESCROWS

async def handle_join_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_join"):
        return

    seller_username = update.message.text.strip().lstrip('@')
    buyer_username = update.effective_user.username

    if seller_username not in ESCROWS:
        await update.message.reply_text("❌ No active escrow found for that seller.")
        context.user_data["awaiting_join"] = False
        return

    # Update buyer info
    ESCROWS[seller_username]["buyer"] = buyer_username
    ESCROWS[seller_username]["status"] = "active"

    # Notify buyer
    await update.message.reply_text(
        f"✅ You have joined the escrow!\n\n"
        f"👤 Seller: @{seller_username}\n"
        f"👤 Buyer: @{buyer_username}\n"
        f"💰 Amount: {ESCROWS[seller_username]['amount']}\n"
        f"📦 Item: {ESCROWS[seller_username]['item']}"
    )

    # Notify seller
    seller_chat_id = ESCROWS[seller_username].get("seller_id")
    if seller_chat_id:
        await context.bot.send_message(
            chat_id=seller_chat_id,
            text=(
                f"✅ Buyer @{buyer_username} has joined your escrow!\n\n"
                f"💰 Amount: {ESCROWS[seller_username]['amount']}\n"
                f"📦 Item: {ESCROWS[seller_username]['item']}\n"
                f"🟢 Deal is now *active*."
            ),
            parse_mode="Markdown"
        )

    context.user_data["awaiting_join"] = False

def register_handlers(app):
    pass  # Handler logic moved to router.py