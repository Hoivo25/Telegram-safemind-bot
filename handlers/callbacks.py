
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

def register_handlers(app):
    app.add_handler(CallbackQueryHandler(callback_router))

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    print(f"🔁 Callback data received: {data}")

    if data == "create_escrow":
        await query.edit_message_text("🔐 Please send the amount and item details to create the escrow.")
        context.user_data["awaiting_escrow_details"] = True
        context.user_data["awaiting_join"] = False

    elif data == "join_escrow":
        await query.edit_message_text("🤝 Please send the seller's @username to join the escrow.")
        context.user_data["awaiting_join"] = True
        context.user_data["awaiting_escrow_details"] = False

    elif data == "rules":
        await query.edit_message_text("📜 Rules will be shown here.")

    elif data == "history":
        await query.edit_message_text("📊 Trade history will be shown here.")

    else:
        await query.edit_message_text("❌ Unknown option selected.")
