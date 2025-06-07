import asyncio
import nest_asyncio
from telegram.ext import Application
from config import BOT_TOKEN
from handlers import register_all_handlers

# Allow nested async loops (required in Replit)
nest_asyncio.apply()

async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    register_all_handlers(application)

    print("✅ Bot is running...")
    await application.run_polling()

# Replit needs this style
asyncio.get_event_loop().run_until_complete(main())