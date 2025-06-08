import os
import nest_asyncio
from telegram.ext import Application
from handlers import register_all_handlers  # Your custom handler setup

nest_asyncio.apply()

# Get the bot token and Render URL from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("RENDER_EXTERNAL_URL")  # Automatically set by Render
PORT = int(os.environ.get('PORT', 5000))

# Ensure required environment variables exist
if not BOT_TOKEN or not APP_URL:
    raise Exception("Missing BOT_TOKEN or RENDER_EXTERNAL_URL environment variables")

# Initialize the Telegram bot application
application = Application.builder().token(BOT_TOKEN).build()

# Register all command and callback handlers
register_all_handlers(application)

# Start webhook server
application.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=f"{APP_URL}/webhook/{BOT_TOKEN}",
    allowed_updates=application.resolve_used_update_types()
)
