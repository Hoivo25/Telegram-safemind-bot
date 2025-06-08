
import nest_asyncio
import asyncio
import logging
import os
from telegram.ext import Application

from config import BOT_TOKEN, WEBHOOK_MODE, WEBHOOK_URL, PORT
from handlers import register_all_handlers

nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Start the bot"""
    try:
        # Initialize bot application
        application = Application.builder().token(BOT_TOKEN).build()
        register_all_handlers(application)
        
        if WEBHOOK_MODE and WEBHOOK_URL:
            # Webhook mode (for production)
            from quart import Quart, request
            
            webhook_app = Quart(__name__)
            
            @webhook_app.route("/webhook", methods=["POST"])
            async def telegram_webhook():
                """Handle incoming Telegram updates from webhook"""
                data = await request.get_data()
                await application.update_queue.put(data)
                return "OK"
            
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
        else:
            # Polling mode (for development)
            logger.info("🤖 Starting bot in polling mode...")
            await application.bot.delete_webhook(drop_pending_updates=True)
            await application.run_polling(allowed_updates=["message", "callback_query"])
            
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot stopped.")
