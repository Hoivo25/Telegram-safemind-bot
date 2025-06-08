import asyncio
import nest_asyncio
import threading
from telegram.ext import Application
from telegram.request import HTTPXRequest
from config import BOT_TOKEN
from handlers import register_all_handlers
from webhook_server import run_webhook_server

# Allow nested async loops (required in Replit)
nest_asyncio.apply()

async def main():
    # Start webhook server in background thread
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
    webhook_thread.start()
    print("🌐 Webhook server started on port 5000")
    
    # Configure request with longer timeout
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )
    
    application = Application.builder().token(BOT_TOKEN).request(request).build()
    register_all_handlers(application)

    print("✅ Bot is running...")
    try:
        await application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ Bot error: {e}")

# Run the bot (Replit compatible)
asyncio.get_event_loop().run_until_complete(main())