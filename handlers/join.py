
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters
from utils import ESCROWS

async def handle_join_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_join"):
        return

    try:
        seller_username = update.message.text.strip().lstrip('@')
        buyer_username = update.effective_user.username
        buyer_id = update.effective_user.id

        if not buyer_username:
            await update.message.reply_text("❌ You need to set a username in Telegram to use this bot.")
            context.user_data["awaiting_join"] = False
            return

        if seller_username not in ESCROWS:
            await update.message.reply_text("❌ No active escrow found for that seller.")
            context.user_data["awaiting_join"] = False
            return

        escrow = ESCROWS[seller_username]
        
        if escrow["status"] != "pending":
            await update.message.reply_text("❌ This escrow is no longer available to join.")
            context.user_data["awaiting_join"] = False
            return

        if escrow.get("buyer"):
            await update.message.reply_text("❌ This escrow already has a buyer.")
            context.user_data["awaiting_join"] = False
            return

        # Update escrow with buyer info
        ESCROWS[seller_username]["buyer"] = buyer_username
        ESCROWS[seller_username]["buyer_id"] = buyer_id
        ESCROWS[seller_username]["status"] = "active"

        # Notify buyer
        success_message = f"✅ *Successfully Joined Escrow!*\n\n"
        success_message += f"👤 Seller: @{seller_username}\n"
        success_message += f"👤 Buyer: @{buyer_username}\n"
        success_message += f"💰 Amount: {escrow['amount']}\n"
        success_message += f"📦 Item: {escrow['item']}\n"
        success_message += f"📊 Status: Active\n\n"
        success_message += f"The trade is now active! Proceed with payment when ready."

        keyboard = [
            [InlineKeyboardButton("💰 Pay with Crypto", callback_data=f"pay_crypto_{seller_username}")],
            [InlineKeyboardButton("📊 View Trade Details", callback_data=f"escrow_details_{seller_username}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ]

        await update.message.reply_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Notify seller
        try:
            seller_chat_id = escrow.get("seller_id")
            if seller_chat_id:
                await context.bot.send_message(
                    chat_id=seller_chat_id,
                    text=(
                        f"✅ *Buyer Joined Your Escrow!*\n\n"
                        f"👤 Buyer: @{buyer_username}\n"
                        f"💰 Amount: {escrow['amount']}\n"
                        f"📦 Item: {escrow['item']}\n"
                        f"🟢 Trade is now *active*.\n\n"
                        f"Wait for the buyer to complete payment."
                    ),
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Error notifying seller: {e}")

        context.user_data["awaiting_join"] = False

    except Exception as e:
        print(f"Error joining escrow: {e}")
        await update.message.reply_text("❌ Error joining escrow. Please try again.")
        context.user_data["awaiting_join"] = False

def register_handlers(app):
    # Text handling is done through router.py
    pass
