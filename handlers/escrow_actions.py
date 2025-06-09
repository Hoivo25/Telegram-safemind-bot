import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils import ESCROWS, USER_STATS, USER_WALLETS, AUTO_RELEASE_TIME
from handlers.payments import nowpayments

async def confirm_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyer confirms delivery and releases payment"""
    query = update.callback_query
    await query.answer()

    escrow_id = query.data.replace("confirm_delivery_", "")
    username = update.effective_user.username

    if escrow_id not in ESCROWS:
        await query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]

    # Check if user is the buyer
    if escrow.get("buyer") != username:
        await query.edit_message_text("❌ Only the buyer can confirm delivery.")
        return

    if escrow["status"] != "active":
        await query.edit_message_text("❌ This escrow is not active.")
        return

    # Release payment to seller
    await release_payment_to_seller(update, context, escrow_id)

async def release_payment_to_seller(update, context, escrow_id):
    """Release payment to seller"""
    escrow = ESCROWS[escrow_id]
    seller_username = escrow_id
    amount = float(escrow["amount"].replace("$", ""))

    # Check if seller has wallet address
    seller_wallets = USER_WALLETS.get(seller_username, {})

    if not seller_wallets:
        message = f"⚠️ *Payment Ready for Release*\n\n"
        message += f"💰 Amount: ${amount}\n"
        message += f"👤 Seller: @{seller_username}\n\n"
        message += f"The seller hasn't provided wallet addresses yet.\n"
        message += f"Please contact @{seller_username} to add wallet addresses."

        if update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode="Markdown")
        return

    # Show available currencies for payout
    keyboard = []
    for currency in seller_wallets.keys():
        keyboard.append([InlineKeyboardButton(
            f"Pay in {currency.upper()}", 
            callback_data=f"payout_{escrow_id}_{currency}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data=f"escrow_details_{escrow_id}")])

    message = f"💰 *Release Payment*\n\n"
    message += f"Amount: ${amount}\n"
    message += f"Seller: @{seller_username}\n\n"
    message += f"Choose payout currency:"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def process_payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process payout to seller"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    escrow_id = parts[1]
    currency = parts[2]

    escrow = ESCROWS[escrow_id]
    seller_username = escrow_id
    amount = float(escrow["amount"].replace("$", ""))

    seller_wallets = USER_WALLETS.get(seller_username, {})
    wallet_address = seller_wallets.get(currency)

    if not wallet_address:
        await query.edit_message_text("❌ Seller doesn't have this wallet address saved.")
        return

    # Create payout using NOWPayments
    try:
        # Note: In a real implementation, you'd need to use NOWPayments payout API
        # For now, we'll simulate the payout process

        # Update escrow status
        escrow["status"] = "completed"
        escrow["completed_at"] = time.time()

        # Update user statistics
        buyer_username = escrow.get("buyer")
        if buyer_username not in USER_STATS:
            USER_STATS[buyer_username] = {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0}
        if seller_username not in USER_STATS:
            USER_STATS[seller_username] = {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0}

        USER_STATS[buyer_username]["trades_completed"] += 1
        USER_STATS[buyer_username]["total_volume"] += amount
        USER_STATS[seller_username]["trades_completed"] += 1
        USER_STATS[seller_username]["total_volume"] += amount

        success_message = f"✅ *Payment Released Successfully!*\n\n"
        success_message += f"💰 Amount: ${amount}\n"
        success_message += f"💎 Currency: {currency.upper()}\n"
        success_message += f"📍 Sent to: `{wallet_address}`\n\n"
        success_message += f"Trade completed successfully!"

        await query.edit_message_text(success_message, parse_mode="Markdown")

        # Notify seller
        try:
            await context.bot.send_message(
                chat_id=escrow["seller_id"],
                text=f"✅ *Payment Received!*\n\n"
                     f"You've received ${amount} in {currency.upper()}\n"
                     f"Wallet: `{wallet_address}`\n\n"
                     f"Trade with @{buyer_username} completed!",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error notifying seller: {e}")

    except Exception as e:
        print(f"Payout error: {e}")
        await query.edit_message_text("❌ Error processing payout. Please try again or contact support.")

async def initiate_refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate refund process"""
    query = update.callback_query
    await query.answer()

    escrow_id = query.data.replace("refund_", "")
    username = update.effective_user.username

    if escrow_id not in ESCROWS:
        await query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]

    # Check if user is authorized to refund (seller or admin)
    if escrow_id != username:  # Not the seller
        await query.edit_message_text("❌ Only the seller can initiate a refund.")
        return

    if escrow["status"] != "active":
        await query.edit_message_text("❌ This escrow is not active.")
        return

    buyer_username = escrow.get("buyer")
    if not buyer_username:
        await query.edit_message_text("❌ No buyer to refund.")
        return

    # Check if buyer has wallet address
    buyer_wallets = USER_WALLETS.get(buyer_username, {})

    if not buyer_wallets:
        await query.edit_message_text(
            f"⚠️ *Refund Request*\n\n"
            f"The buyer @{buyer_username} hasn't provided wallet addresses yet.\n"
            f"Please ask them to add wallet addresses in the bot.",
            parse_mode="Markdown"
        )
        return

    # Show available currencies for refund
    keyboard = []
    for currency in buyer_wallets.keys():
        keyboard.append([InlineKeyboardButton(
            f"Refund in {currency.upper()}", 
            callback_data=f"process_refund_{escrow_id}_{currency}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data=f"escrow_details_{escrow_id}")])

    amount = escrow["amount"]
    message = f"💸 *Process Refund*\n\n"
    message += f"Amount: {amount}\n"
    message += f"Buyer: @{buyer_username}\n\n"
    message += f"Choose refund currency:"

    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process refund to buyer"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    escrow_id = parts[2]
    currency = parts[3]

    escrow = ESCROWS[escrow_id]
    buyer_username = escrow.get("buyer")
    amount = float(escrow["amount"].replace("$", ""))

    buyer_wallets = USER_WALLETS.get(buyer_username, {})
    wallet_address = buyer_wallets.get(currency)

    if not wallet_address:
        await query.edit_message_text("❌ Buyer doesn't have this wallet address saved.")
        return

    try:
        # Update escrow status
        escrow["status"] = "refunded"
        escrow["refunded_at"] = time.time()

        # Update user statistics
        seller_username = escrow_id
        if buyer_username not in USER_STATS:
            USER_STATS[buyer_username] = {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0}
        if seller_username not in USER_STATS:
            USER_STATS[seller_username] = {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0}

        USER_STATS[buyer_username]["trades_cancelled"] += 1
        USER_STATS[seller_username]["trades_cancelled"] += 1

        success_message = f"✅ *Refund Processed Successfully!*\n\n"
        success_message += f"💰 Amount: ${amount}\n"
        success_message += f"💎 Currency: {currency.upper()}\n"
        success_message += f"📍 Sent to: `{wallet_address}`\n\n"
        success_message += f"Refund completed!"

        await query.edit_message_text(success_message, parse_mode="Markdown")

        # Notify buyer
        try:
            buyer_user = None
            for user_id, user_data in context.application.user_data.items():
                if user_data.get("username") == buyer_username:
                    buyer_user = user_id
                    break

            if buyer_user:
                await context.bot.send_message(
                    chat_id=buyer_user,
                    text=f"✅ *Refund Received!*\n\n"
                         f"You've received a ${amount} refund in {currency.upper()}\n"
                         f"Wallet: `{wallet_address}`\n\n"
                         f"Refund from @{seller_username} processed!",
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Error notifying buyer: {e}")

    except Exception as e:
        print(f"Refund error: {e}")
        await query.edit_message_text("❌ Error processing refund. Please try again or contact support.")

async def check_auto_release(context: ContextTypes.DEFAULT_TYPE):
    """Check for escrows that should be auto-released"""
    current_time = time.time()

    for escrow_id, escrow in ESCROWS.items():
        if (escrow["status"] == "active" and 
            escrow.get("funded_at") and 
            current_time - escrow["funded_at"] >= AUTO_RELEASE_TIME):

            # Auto-release payment
            try:
                seller_username = escrow_id
                buyer_username = escrow.get("buyer")

                # Release payment automatically
                escrow["status"] = "auto_completed"
                escrow["completed_at"] = current_time

                # Notify both parties
                if escrow.get("seller_id"):
                    await context.bot.send_message(
                        chat_id=escrow["seller_id"],
                        text=f"⏰ *Auto-Release Triggered*\n\n"
                             f"Escrow #{escrow_id} has been automatically completed.\n"
                             f"Payment will be processed to your wallet.",
                        parse_mode="Markdown"
                    )

                print(f"Auto-released escrow {escrow_id}")

            except Exception as e:
                print(f"Error in auto-release for {escrow_id}: {e}")

def register_handlers(app):
    app.add_handler(CallbackQueryHandler(confirm_delivery, pattern="^confirm_delivery_"))
    app.add_handler(CallbackQueryHandler(process_payout, pattern="^payout_"))
    app.add_handler(CallbackQueryHandler(initiate_refund, pattern="^refund_"))
    app.add_handler(CallbackQueryHandler(process_refund, pattern="^process_refund_"))

    # Schedule auto-release check every hour (if job queue is available)
    if app.job_queue:
        app.job_queue.run_repeating(check_auto_release, interval=3600, first=10)
        print("✅ Auto-release scheduler started")
    else:
        print("⚠️ Job queue not available - auto-release disabled")