
import nest_asyncio
import asyncio
import logging
import os
from telegram.ext import Application

from config import BOT_TOKEN, WEBHOOK_MODE, WEBHOOK_URL, PORT
from handlers import register_all_handlers

# Apply nest_asyncio patch
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
            
            @webhook_app.route("/webhook/stripe", methods=["POST"])
            async def stripe_webhook():
                """Handle Stripe webhook events"""
                import stripe
                from config import STRIPE_WEBHOOK_SECRET
                from utils import ESCROWS
                import time
                
                payload = await request.get_data(as_text=True)
                sig_header = request.headers.get('Stripe-Signature')
                
                try:
                    event = stripe.Webhook.construct_event(
                        payload, sig_header, STRIPE_WEBHOOK_SECRET
                    )
                except:
                    return "Invalid signature", 400
                
                # Handle successful payment
                if event['type'] == 'checkout.session.completed':
                    session = event['data']['object']
                    escrow_id = session['metadata'].get('escrow_id')
                    if escrow_id and escrow_id in ESCROWS:
                        ESCROWS[escrow_id]["payment_status"] = "paid"
                        ESCROWS[escrow_id]["stripe_session_id"] = session['id']
                        ESCROWS[escrow_id]["funded_at"] = time.time()
                
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
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the main function
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot stopped.")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
