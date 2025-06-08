from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from utils import ESCROWS, USER_STATS
from config import SUPPORT_USERNAME, FLAT_FEE, PERCENTAGE_FEE

def register_handlers(app):
    app.add_handler(CallbackQueryHandler(callback_router))

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    print(f"🔁 Callback data received: {data}")

    if data == "create_escrow":
        instructions = (
            "📝 *Create Escrow*\n\n"
            "Please send the escrow details in the following format:\n"
            "`amount | item name | @buyer_username`\n\n"
            "Example:\n"
            "`100 | iPhone 12 | @john_doe`\n\n"
            "Once submitted, the buyer can join the trade."
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
        await query.edit_message_text(instructions, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data["awaiting_escrow_details"] = True
        context.user_data["awaiting_join"] = False

    elif data == "join_escrow":
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
        await query.edit_message_text("🤝 Please send the seller's @username to join the escrow.", reply_markup=InlineKeyboardMarkup(keyboard))
        context.user_data["awaiting_join"] = True
        context.user_data["awaiting_escrow_details"] = False

    elif data == "view_escrows":
        await show_active_escrows(update, context)

    elif data == "my_trades":
        await show_user_trades(update, context)

    elif data == "profile":
        await show_user_profile(update, context)

    elif data == "rules":
        await show_rules(update, context)
    
    elif data == "wallet_menu":
        await show_wallet_menu(update, context)

    elif data == "menu":
        from .start import show_main_menu
        await show_main_menu(update, context)

    elif data.startswith("escrow_details_"):
        escrow_id = data.replace("escrow_details_", "")
        await show_escrow_details(update, context, escrow_id)

    elif data.startswith("complete_"):
        escrow_id = data.replace("complete_", "")
        await complete_trade(update, context, escrow_id)

    elif data.startswith("cancel_"):
        escrow_id = data.replace("cancel_", "")
        await cancel_escrow(update, context, escrow_id)

    elif data.startswith("share_link_"):
        escrow_id = data.replace("share_link_", "")
        await share_join_link(update, context, escrow_id)

    elif data.startswith("confirm_join_"):
        escrow_id = data.replace("confirm_join_", "")
        await confirm_join_escrow(update, context, escrow_id)

    elif data.startswith("confirm_cancel_"):
        escrow_id = data.replace("confirm_cancel_", "")
        await confirm_cancel_escrow(update, context, escrow_id)

    elif data.startswith("dispute_"):
        escrow_id = data.replace("dispute_", "")
        await start_dispute(update, context, escrow_id)

    elif data.startswith("pay_crypto_"):
        escrow_id = data.replace("pay_crypto_", "")
        await initiate_payment(update, context, escrow_id)
    
    elif data.startswith("refund_"):
        escrow_id = data.replace("refund_", "")
        await refund_escrow(update, context, escrow_id)
    
    elif data == "set_seller_wallet":
        await set_seller_wallet(update, context)

    elif data == "set_buyer_refund_wallet":
        await set_buyer_refund_wallet(update, context)

    else:
        await query.edit_message_text("❌ Unknown option selected.")

async def show_escrow_details(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    """Show detailed view of an escrow"""
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    username = update.effective_user.username

    # Calculate fees
    amount = float(escrow["amount"].replace("$", ""))
    if amount < 100:
        fee = FLAT_FEE
        total = amount + fee
    else:
        fee = amount * PERCENTAGE_FEE
        total = amount + fee

    message = f"🔐 *Escrow Details*\n\n"
    message += f"🆔 ID: `{escrow_id}`\n"
    message += f"👤 Seller: @{escrow_id}\n"
    message += f"💰 Amount: {escrow['amount']}\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"👤 Buyer: {escrow.get('buyer', 'Waiting...')}\n"
    message += f"📊 Status: {escrow['status'].title()}\n"
    message += f"💳 Payment: {escrow.get('payment_status', 'unpaid').title()}\n\n"
    message += f"💵 Total with fees: ${total:.2f} (${fee:.2f} fee)\n\n"

    # Add auto-release info for active escrows
    if escrow["status"] == "active" and escrow.get("funded_at"):
        import time
        from utils import AUTO_RELEASE_TIME
        time_left = AUTO_RELEASE_TIME - (time.time() - escrow["funded_at"])
        if time_left > 0:
            hours_left = int(time_left // 3600)
            message += f"⏰ Auto-release in: {hours_left} hours\n\n"

    if escrow["status"] == "pending":
        message += "⏳ Waiting for buyer to join and make payment."
    elif escrow["status"] == "active":
        message += "✅ Escrow is active. Awaiting delivery confirmation."
    elif escrow["status"] == "completed":
        message += "✅ Trade completed successfully!"
    elif escrow["status"] == "auto_completed":
        message += "⏰ Trade auto-completed after 72 hours!"
    elif escrow["status"] == "refunded":
        message += "💸 Trade was refunded."
    elif escrow["status"] == "cancelled":
        message += "❌ Trade was cancelled."

    keyboard = []

    # Show different buttons based on user role and escrow status
    if escrow["status"] == "pending":
        if username == escrow_id:  # Seller
            keyboard.append([InlineKeyboardButton("❌ Cancel Escrow", callback_data=f"cancel_{escrow_id}")])
        elif username == escrow.get("buyer"):  # Buyer
            if escrow.get("payment_status") == "unpaid":
                keyboard.append([InlineKeyboardButton("💳 Make Payment", callback_data=f"pay_crypto_{escrow_id}")])

    elif escrow["status"] == "active":
        if username == escrow.get("buyer"):  # Buyer
            keyboard.append([InlineKeyboardButton("✅ Confirm Delivery", callback_data=f"confirm_delivery_{escrow_id}")])
        elif username == escrow_id:  # Seller
            keyboard.append([InlineKeyboardButton("💸 Issue Refund", callback_data=f"refund_{escrow_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="view_escrows")])

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def initiate_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    """Start payment process"""
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    amount = float(escrow["amount"].replace("$", ""))

    message = f"💰 *Payment Options*\n\n"
    message += f"Amount: ${amount}\n"
    message += f"Item: {escrow['item']}\n\n"
    message += f"Available payment methods:"

    keyboard = [
        [InlineKeyboardButton("₿ Bitcoin", callback_data=f"select_crypto_{escrow_id}_btc")],
        [InlineKeyboardButton("💎 Ethereum", callback_data=f"select_crypto_{escrow_id}_eth")],
        [InlineKeyboardButton("💰 USDT", callback_data=f"select_crypto_{escrow_id}_usdt")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"escrow_details_{escrow_id}")]
    ]

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_active_escrows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active escrows"""
    if not ESCROWS:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
        await update.callback_query.edit_message_text(
            "📭 No active escrows found.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    message = "🔐 *Active Escrows:*\n\n"
    keyboard = []

    for seller, escrow in ESCROWS.items():
        status_emoji = "🟡" if escrow["status"] == "pending" else "🟢" if escrow["status"] == "active" else "🔴"
        buyer_text = escrow.get("buyer", "Waiting for buyer")
        message += f"{status_emoji} *@{seller}*\n"
        message += f"💰 {escrow['amount']} - {escrow['item']}\n"
        message += f"👤 Buyer: {buyer_text}\n\n"

        keyboard.append([InlineKeyboardButton(f"View @{seller}", callback_data=f"escrow_details_{seller}")])

    keyboard = [
        [InlineKeyboardButton("➕ Create Escrow", callback_data="create_escrow"),
         InlineKeyboardButton("🤝 Join Escrow", callback_data="join_escrow")],
        [InlineKeyboardButton("🔍 View All Escrows", callback_data="view_escrows"),
         InlineKeyboardButton("📊 My Trades", callback_data="my_trades")],
        [InlineKeyboardButton("💳 Wallet Manager", callback_data="wallet_menu"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_user_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's trade history"""
    username = update.effective_user.username
    user_escrows = []

    for seller, escrow in ESCROWS.items():
        if seller == username or escrow.get("buyer") == username:
            role = "Seller" if seller == username else "Buyer"
            user_escrows.append((seller, escrow, role))

    if not user_escrows:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
        await update.callback_query.edit_message_text(
            "📭 You have no active trades.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    message = "📊 *Your Active Trades:*\n\n"
    keyboard = []

    for seller, escrow, role in user_escrows:
        status_emoji = "🟡" if escrow["status"] == "pending" else "🟢" if escrow["status"] == "active" else "🔴"
        message += f"{status_emoji} *{role}* - {escrow['amount']}\n"
        message += f"📦 {escrow['item']}\n"
        message += f"👤 Partner: @{escrow.get('buyer', 'None') if role == 'Seller' else seller}\n\n"

        # Add action buttons based on role and status
        if role == "Seller" and escrow["status"] == "pending":
            keyboard.append([
                InlineKeyboardButton(f"View Details", callback_data=f"escrow_details_{seller}"),
                InlineKeyboardButton(f"❌ Cancel", callback_data=f"cancel_{seller}")
            ])
        else:
            keyboard.append([InlineKeyboardButton(f"View Details", callback_data=f"escrow_details_{seller}")])

    keyboard = [
        [InlineKeyboardButton("➕ Create Escrow", callback_data="create_escrow"),
         InlineKeyboardButton("🤝 Join Escrow", callback_data="join_escrow")],
        [InlineKeyboardButton("🔍 View All Escrows", callback_data="view_escrows"),
         InlineKeyboardButton("📊 My Trades", callback_data="my_trades")],
        [InlineKeyboardButton("💳 Wallet Manager", callback_data="wallet_menu"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    username = update.effective_user.username
    user_id = update.effective_user.id

    if username not in USER_STATS:
        USER_STATS[username] = {
            "trades_completed": 0,
            "trades_cancelled": 0,
            "total_volume": 0,
            "reputation": 5.0
        }

    stats = USER_STATS[username]

    message = f"👤 *Profile: @{username}*\n\n"
    message += f"✅ Completed Trades: {stats['trades_completed']}\n"
    message += f"❌ Cancelled Trades: {stats['trades_cancelled']}\n"
    message += f"💰 Total Volume: ${stats['total_volume']}\n"
    message += f"⭐ Reputation: {stats['reputation']:.1f}/5.0\n"
    message += f"🆔 User ID: `{user_id}`"

    keyboard = [
        [InlineKeyboardButton("➕ Create Escrow", callback_data="create_escrow"),
         InlineKeyboardButton("🤝 Join Escrow", callback_data="join_escrow")],
        [InlineKeyboardButton("🔍 View All Escrows", callback_data="view_escrows"),
         InlineKeyboardButton("📊 My Trades", callback_data="my_trades")],
        [InlineKeyboardButton("💳 Wallet Manager", callback_data="wallet_menu"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show escrow rules"""
    rules_text = f"""📜 *Escrow Bot Rules & Guidelines*

🔐 *How Escrow Works:*
1. Seller creates an escrow with item details
2. Buyer joins the escrow to start the trade
3. Both parties agree on terms before proceeding
4. Seller sends item, buyer confirms receipt
5. Funds are released to seller upon completion

💰 *Fee Structure:*
• Transactions under $100: ${FLAT_FEE} flat fee
• Transactions over $100: {int(PERCENTAGE_FEE*100)}% of total amount

⚖️ *Dispute Resolution:*
• Both parties can initiate disputes
• Admin {SUPPORT_USERNAME} will mediate
• Provide evidence and clear communication
• Decision is final once made

🚫 *Prohibited Items:*
• Illegal goods or services
• Adult content
• Stolen or counterfeit items
• Anything violating Telegram ToS

⚠️ *Important Notes:*
• Always verify usernames before trading
• Keep all communication on Telegram
• Report suspicious activity immediately
• Bot is not responsible for off-platform trades

📞 *Support:* {SUPPORT_USERNAME}"""

    keyboard = [
        [InlineKeyboardButton("➕ Create Escrow", callback_data="create_escrow"),
         InlineKeyboardButton("🤝 Join Escrow", callback_data="join_escrow")],
        [InlineKeyboardButton("🔍 View All Escrows", callback_data="view_escrows"),
         InlineKeyboardButton("📊 My Trades", callback_data="my_trades")],
        [InlineKeyboardButton("💳 Wallet Manager", callback_data="wallet_menu"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]
    await update.callback_query.edit_message_text(
        rules_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def complete_trade(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    username = update.effective_user.username

    # Only participants can complete
    if username != escrow_id and username != escrow.get("buyer"):
        await update.callback_query.edit_message_text("❌ You are not part of this trade.")
        return

    # Update escrow status
    ESCROWS[escrow_id]["status"] = "completed"

    # Update user stats
    seller_stats = USER_STATS.get(escrow_id, {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0})
    buyer_stats = USER_STATS.get(escrow.get("buyer"), {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0})

    amount = int(escrow["amount"].replace("$", ""))
    seller_stats["trades_completed"] += 1
    seller_stats["total_volume"] += amount
    buyer_stats["trades_completed"] += 1

    USER_STATS[escrow_id] = seller_stats
    if escrow.get("buyer"):
        USER_STATS[escrow["buyer"]] = buyer_stats

    # Remove from active escrows
    del ESCROWS[escrow_id]

    message = f"✅ *Trade Completed Successfully!*\n\n"
    message += f"👤 Seller: @{escrow_id}\n"
    message += f"👤 Buyer: @{escrow.get('buyer', 'Unknown')}\n"
    message += f"💰 Amount: {escrow['amount']}\n"
    message += f"📦 Item: {escrow['item']}\n\n"
    message += f"Thank you for using our escrow service!"

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cancel_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    username = update.effective_user.username

    # Only seller can cancel pending escrows
    if username != escrow_id:
        await update.callback_query.edit_message_text("❌ Only the seller can cancel this escrow.")
        return

    escrow = ESCROWS[escrow_id]
    if escrow["status"] != "pending":
        await update.callback_query.edit_message_text("❌ Can only cancel pending escrows.")
        return

    # Show confirmation
    message = f"⚠️ *Confirm Cancellation*\n\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"💰 Amount: {escrow['amount']}\n\n"
    message += f"Are you sure you want to cancel this escrow?"

    keyboard = [
        [InlineKeyboardButton("✅ Yes, Cancel", callback_data=f"confirm_cancel_{escrow_id}")],
        [InlineKeyboardButton("❌ No, Keep It", callback_data=f"escrow_details_{escrow_id}")]
    ]

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_cancel_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    username = update.effective_user.username
    escrow = ESCROWS[escrow_id]

    # Update stats
    if username not in USER_STATS:
        USER_STATS[username] = {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0}
    USER_STATS[username]["trades_cancelled"] += 1

    # Remove escrow
    del ESCROWS[escrow_id]

    message = f"❌ *Escrow Cancelled Successfully*\n\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"💰 Amount: {escrow['amount']}\n\n"
    message += f"The escrow has been cancelled and removed from active trades."

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    username = update.effective_user.username

    # Only participants can start disputes
    if username != escrow_id and username != escrow.get("buyer"):
        await update.callback_query.edit_message_text("❌ You are not part of this trade.")
        return

    # Update status
    ESCROWS[escrow_id]["status"] = "disputed"

    message = f"⚠️ *Dispute Started*\n\n"
    message += f"👤 Initiated by: @{username}\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"💰 Amount: {escrow['amount']}\n\n"
    message += f"Admin {SUPPORT_USERNAME} has been notified and will review this case.\n\n"
    message += f"Please provide detailed information about the issue."

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def share_join_link(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    """Share the join link for an escrow"""
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    bot_username = context.bot.username
    join_link = f"https://t.me/{bot_username}?start=join_{escrow_id}"

    message = f"🔗 *Share This Join Link*\n\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"💰 Amount: {escrow['amount']}\n\n"
    message += f"🔗 *Quick Join Link:*\n`{join_link}`\n\n"
    message += f"Copy and share this link with your buyer. They can click it to join the escrow instantly!"

    keyboard = [
        [InlineKeyboardButton("📊 View Trade Details", callback_data=f"escrow_details_{escrow_id}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ]

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_join_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    """Confirm joining an escrow via deep link"""
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    buyer_username = update.effective_user.username
    buyer_id = update.effective_user.id

    if not buyer_username:
        await update.callback_query.edit_message_text("❌ You need to set a username in Telegram to use this bot.")
        return

    if escrow["status"] != "pending":
        await update.callback_query.edit_message_text("❌ This escrow is no longer available to join.")
        return

    if escrow.get("buyer"):
        await update.callback_query.edit_message_text("❌ This escrow already has a buyer.")
        return

    # Update escrow with buyer info
    ESCROWS[escrow_id]["buyer"] = buyer_username
    ESCROWS[escrow_id]["buyer_id"] = buyer_id
    ESCROWS[escrow_id]["status"] = "active"

    # Notify buyer
    success_message = f"✅ *Successfully Joined Escrow!*\n\n"
    success_message += f"👤 Seller: @{escrow_id}\n"
    success_message += f"👤 Buyer: @{buyer_username}\n"
    success_message += f"💰 Amount: {escrow['amount']}\n"
    success_message += f"📦 Item: {escrow['item']}\n"
    success_message += f"📊 Status: Active\n\n"
    success_message += f"The trade is now active! Proceed with payment when ready."

    keyboard = [
        [InlineKeyboardButton("💰 Pay with Crypto", callback_data=f"pay_crypto_{escrow_id}")],
        [InlineKeyboardButton("📊 View Trade Details", callback_data=f"escrow_details_{escrow_id}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ]

    await update.callback_query.edit_message_text(
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

async def refund_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE, escrow_id: str):
    """Refund the buyer"""
    if escrow_id not in ESCROWS:
        await update.callback_query.edit_message_text("❌ Escrow not found.")
        return

    escrow = ESCROWS[escrow_id]
    username = update.effective_user.username

    # Check if the user is the seller
    if username != escrow_id:
        await update.callback_query.edit_message_text("❌ You are not the seller.")
        return

    # Check if the escrow is active
    if escrow["status"] != "active":
        await update.callback_query.edit_message_text("❌ This escrow is not active.")
        return

    # Check if the buyer has a refund wallet
    if not escrow.get("buyer_refund_wallet"):
        await update.callback_query.edit_message_text("❌ Buyer has not set a refund wallet.")
        return

    # Refund the buyer
    # In a real-world scenario, you would use a payment gateway to refund the buyer
    # For this example, we will just update the escrow status
    ESCROWS[escrow_id]["status"] = "refunded"

    message = f"💸 *Refund Issued*\n\n"
    message += f"👤 Buyer: @{escrow.get('buyer', 'Unknown')}\n"
    message += f"💰 Amount: {escrow['amount']}\n"
    message += f"📦 Item: {escrow['item']}\n\n"
    message += f"The buyer has been refunded."

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show wallet management menu"""
    keyboard = [
        [InlineKeyboardButton("Set Seller Wallet", callback_data="set_seller_wallet")],
        [InlineKeyboardButton("Set Buyer Refund Wallet", callback_data="set_buyer_refund_wallet")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ]

    await update.callback_query.edit_message_text(
        "💳 *Wallet Manager*\n\nSet your wallet addresses for receiving payments and refunds.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_seller_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set seller wallet address"""
    await update.callback_query.edit_message_text("Please send your seller wallet address.")
    context.user_data["awaiting_seller_wallet"] = True

async def set_buyer_refund_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set buyer refund wallet address"""
    await update.callback_query.edit_message_text("Please send your buyer refund wallet address.")
    context.user_data["awaiting_buyer_refund_wallet"] = True