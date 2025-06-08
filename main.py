import nest_asyncio
import asyncio
import logging
import os
from telegram.ext import Application
from quart import Quart, request

from config import BOT_TOKEN, WEBHOOK_URL, PORT
from handlers import register_all_handlers

nest_asyncio.apply()

# Initialize bot application
application = Application.builder().token(BOT_TOKEN).build()
register_all_handlers(application)

# Webhook server using Quart
webhook_app = Quart(__name__)

@webhook_app.route("/webhook", methods=["POST"])
async def telegram_webhook():
    """Handle incoming Telegram updates from webhook"""
    data = await request.get_data()
    await application.update_queue.put(data)
    return "OK"

async def start():
    # Set webhook
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    # Run both Telegram and Quart app
    await asyncio.gather(
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
        ),
        webhook_app.run_task(host="0.0.0.0", port=PORT),
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(start())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
