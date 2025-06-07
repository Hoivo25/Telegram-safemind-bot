from telegram import Update
from telegram.ext import ContextTypes
from utils import ESCROWS

async def handle_join_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_join"):
        print("User sent message but bot is NOT awaiting join input")
        return

    print("✅ Received seller username input")

    seller_username = update.message.text.strip().lstrip('@')
    buyer_username = update.effective_user.username

    if not buyer_username:
        await update.message.reply_text("❌ You must set a Telegram username to join the escrow.")
        return

    if seller_username not in ESCROWS:
        await update.message.reply_text("❌ No active escrow found for that seller.")
        context.user_data["awaiting_join"] = False
        return

    ESCROWS[seller_username]["buyer"] = buyer_username

    await update.message.reply_text(
        f"✅ You have joined the escrow!\n\n"
        f"👤 Seller: @{seller_username}\n"
        f"👤 Buyer: @{buyer_username}\n"
        f"💰 Amount: {ESCROWS[seller_username]['amount']}\n"
        f"📦 Item: {ESCROWS[seller_username]['item']}"
    )

    context.user_data["awaiting_join"] = False


def register_handlers(app):
    # Optional: leave empty or remove if routing via router.py
    pass