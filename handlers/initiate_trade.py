
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from utils import ESCROWS

async def handle_escrow_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_escrow_details"):
        return

    try:
        text = update.message.text.strip()
        parts = [part.strip() for part in text.split('|')]
        
        if len(parts) != 3:
            await update.message.reply_text("❌ Invalid format. Please use: `amount | item name | @buyer_username`", parse_mode="Markdown")
            return

        amount_str, item, buyer_username = parts
        
        # Validate amount
        try:
            amount = float(amount_str.replace('$', ''))
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
            return

        # Clean buyer username
        buyer_username = buyer_username.lstrip('@')
        
        # Get seller info
        seller_username = update.effective_user.username
        seller_id = update.effective_user.id
        
        if not seller_username:
            await update.message.reply_text("❌ You need to set a username in Telegram to use this bot.")
            return

        # Create escrow
        ESCROWS[seller_username] = {
            "amount": f"${amount}",
            "item": item,
            "buyer": None,
            "status": "pending",
            "seller_id": seller_id,
            "payment_status": "unpaid"
        }

        success_message = f"✅ *Escrow Created Successfully!*\n\n"
        success_message += f"👤 Seller: @{seller_username}\n"
        success_message += f"💰 Amount: ${amount}\n"
        success_message += f"📦 Item: {item}\n"
        success_message += f"👤 Expected Buyer: @{buyer_username}\n"
        success_message += f"📊 Status: Pending\n\n"
        success_message += f"Share your username (@{seller_username}) with the buyer so they can join!"

        keyboard = [
            [InlineKeyboardButton("📊 View My Trades", callback_data="my_trades")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ]

        await update.message.reply_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Reset state
        context.user_data["awaiting_escrow_details"] = False

    except Exception as e:
        print(f"Error creating escrow: {e}")
        await update.message.reply_text("❌ Error creating escrow. Please try again.")
        context.user_data["awaiting_escrow_details"] = False

def register_handlers(app):
    # Text handling is done through router.py
    pass
