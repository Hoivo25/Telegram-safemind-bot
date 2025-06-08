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

    elif data == "menu":
        from .start import show_main_menu
        await show_main_menu(update, context)

    elif data.startswith("complete_"):
        escrow_id = data.replace("complete_", "")
        await complete_trade(update, context, escrow_id)

    elif data.startswith("cancel_"):
        escrow_id = data.replace("cancel_", "")
        await cancel_escrow(update, context, escrow_id)

    elif data.startswith("dispute_"):
        escrow_id = data.replace("dispute_", "")
        await start_dispute(update, context, escrow_id)

    else:
        await query.edit_message_text("❌ Unknown option selected.")

async def show_active_escrows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ESCROWS:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
        await update.callback_query.edit_message_text(
            "📭 No active escrows found.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    message = "🔐 *Active Escrows:*\n\n"
    for seller, escrow in ESCROWS.items():
        status_emoji = "🟡" if escrow["status"] == "pending" else "🟢" if escrow["status"] == "active" else "🔴"
        buyer_text = escrow["buyer"] or "Waiting for buyer"
        message += f"{status_emoji} *@{seller}*\n"
        message += f"💰 Amount: {escrow['amount']}\n"
        message += f"📦 Item: {escrow['item']}\n"
        message += f"👤 Buyer: {buyer_text}\n"
        message += f"📊 Status: {escrow['status'].title()}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_user_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        message += f"👤 Partner: @{escrow['buyer'] if role == 'Seller' else seller}\n"
        message += f"📊 Status: {escrow['status'].title()}\n\n"

        # Add action buttons based on role and status
        if role == "Seller" and escrow["status"] == "pending":
            keyboard.append([InlineKeyboardButton(f"❌ Cancel Trade", callback_data=f"cancel_{seller}")])
        elif escrow["status"] == "active":
            buttons = []
            if username == escrow_id:  # Seller
                buttons.append([InlineKeyboardButton("✅ Mark as Completed", callback_data=f"complete_{escrow_id}")])
            elif username == escrow.get("buyer"):  # Buyer
                buttons.extend([
                    [InlineKeyboardButton("💰 Pay with Crypto", callback_data=f"pay_crypto_{escrow_id}")],
                    [InlineKeyboardButton("✅ Confirm Receipt", callback_data=f"complete_{escrow_id}")]
                ])

            # Both parties can cancel or dispute
            buttons.extend([
                [InlineKeyboardButton("❌ Cancel Trade", callback_data=f"cancel_{escrow_id}"),
                 InlineKeyboardButton("⚠️ Open Dispute", callback_data=f"dispute_{escrow_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data="view_escrows")]
            ])
            keyboard.extend(buttons)

    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")])
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
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
    buyer_stats = USER_STATS.get(escrow["buyer"], {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0})

    amount = int(escrow["amount"].replace("$", ""))
    seller_stats["trades_completed"] += 1
    seller_stats["total_volume"] += amount
    buyer_stats["trades_completed"] += 1

    USER_STATS[escrow_id] = seller_stats
    USER_STATS[escrow["buyer"]] = buyer_stats

    # Remove from active escrows
    del ESCROWS[escrow_id]

    message = f"✅ *Trade Completed Successfully!*\n\n"
    message += f"👤 Seller: @{escrow_id}\n"
    message += f"👤 Buyer: @{escrow['buyer']}\n"
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

    # Update stats
    if username not in USER_STATS:
        USER_STATS[username] = {"trades_completed": 0, "trades_cancelled": 0, "total_volume": 0, "reputation": 5.0}
    USER_STATS[username]["trades_cancelled"] += 1

    # Remove escrow
    del ESCROWS[escrow_id]

    message = f"❌ *Escrow Cancelled*\n\n"
    message += f"The escrow for {escrow['item']} ({escrow['amount']}) has been cancelled."

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