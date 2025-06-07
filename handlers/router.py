
from telegram.ext import MessageHandler, filters
from .initiate_trade import handle_escrow_details
from .join import handle_join_input

text_router = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)

async def handle_text_message(update, context):
    if context.user_data.get("awaiting_escrow_details"):
        print("📝 Handling escrow creation input")
        await handle_escrow_details(update, context)

    elif context.user_data.get("awaiting_join"):
        print("🤝 Handling join escrow input")
        await handle_join_input(update, context)

    else:
        print("⚠️ User sent message but bot is not awaiting any input.")
        await update.message.reply_text("❌ Please start an action from the menu (e.g. Create or Join Escrow)")
