
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils import ESCROWS, USER_STATS
from config import SUPPORT_USERNAME

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin statistics"""
    username = update.effective_user.username
    
    # Simple admin check (you can improve this)
    if username != SUPPORT_USERNAME.replace("@", ""):
        await update.message.reply_text("❌ Admin access required.")
        return
    
    total_escrows = len(ESCROWS)
    total_users = len(USER_STATS)
    
    active_escrows = sum(1 for e in ESCROWS.values() if e["status"] == "active")
    pending_escrows = sum(1 for e in ESCROWS.values() if e["status"] == "pending")
    disputed_escrows = sum(1 for e in ESCROWS.values() if e["status"] == "disputed")
    
    total_completed = sum(stats["trades_completed"] for stats in USER_STATS.values())
    total_volume = sum(stats["total_volume"] for stats in USER_STATS.values())
    
    message = f"📊 *Admin Dashboard*\n\n"
    message += f"🔐 Total Active Escrows: {total_escrows}\n"
    message += f"   • Active: {active_escrows}\n"
    message += f"   • Pending: {pending_escrows}\n"
    message += f"   • Disputed: {disputed_escrows}\n\n"
    message += f"👥 Total Users: {total_users}\n"
    message += f"✅ Total Completed Trades: {total_completed}\n"
    message += f"💰 Total Volume: ${total_volume}\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def admin_resolve_dispute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resolve a dispute (admin only)"""
    username = update.effective_user.username
    
    if username != SUPPORT_USERNAME.replace("@", ""):
        await update.message.reply_text("❌ Admin access required.")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /resolve <seller_username> <winner>\n"
            "Example: /resolve john_doe seller"
        )
        return
    
    seller_username = context.args[0]
    winner = context.args[1].lower()
    
    if seller_username not in ESCROWS:
        await update.message.reply_text("❌ Escrow not found.")
        return
    
    escrow = ESCROWS[seller_username]
    if escrow["status"] != "disputed":
        await update.message.reply_text("❌ This escrow is not disputed.")
        return
    
    if winner not in ["seller", "buyer"]:
        await update.message.reply_text("❌ Winner must be 'seller' or 'buyer'.")
        return
    
    # Resolve dispute
    ESCROWS[seller_username]["status"] = "resolved"
    ESCROWS[seller_username]["winner"] = winner
    
    message = f"⚖️ *Dispute Resolved*\n\n"
    message += f"📦 Item: {escrow['item']}\n"
    message += f"💰 Amount: {escrow['amount']}\n"
    message += f"🏆 Winner: {winner.title()}\n"
    message += f"👤 Seller: @{seller_username}\n"
    message += f"👤 Buyer: @{escrow['buyer']}\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

def register_handlers(app):
    app.add_handler(CommandHandler("admin_stats", admin_stats))
    app.add_handler(CommandHandler("resolve", admin_resolve_dispute))
