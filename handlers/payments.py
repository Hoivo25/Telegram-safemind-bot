
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_SECRET
from utils import ESCROWS, PAYMENT_SESSIONS
import json
import hashlib
import hmac

class NOWPayments:
    def __init__(self):
        self.api_key = NOWPAYMENTS_API_KEY
        self.base_url = "https://api.nowpayments.io/v1"
        self.ipn_secret = NOWPAYMENTS_IPN_SECRET
    
    async def get_available_currencies(self):
        """Get list of available cryptocurrencies"""
        async with aiohttp.ClientSession() as session:
            headers = {"x-api-key": self.api_key}
            async with session.get(f"{self.base_url}/currencies", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("currencies", [])
                return []
    
    async def create_payment(self, amount_usd, currency, order_id, description):
        """Create a payment invoice"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "price_amount": float(amount_usd),
                "price_currency": "usd",
                "pay_currency": currency,
                "order_id": order_id,
                "order_description": description,
                "ipn_callback_url": "https://your-repl-url.replit.dev/webhook/nowpayments",
                "success_url": "https://t.me/your_bot_username",
                "cancel_url": "https://t.me/your_bot_username"
            }
            
            async with session.post(f"{self.base_url}/payment", 
                                  headers=headers, 
                                  json=payload) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_data = await response.text()
                    print(f"Payment creation error: {error_data}")
                    return None
    
    async def get_payment_status(self, payment_id):
        """Check payment status"""
        async with aiohttp.ClientSession() as session:
            headers = {"x-api-key": self.api_key}
            async with session.get(f"{self.base_url}/payment/{payment_id}", 
                                 headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    def verify_ipn_signature(self, payload, signature):
        """Verify IPN callback signature"""
        expected_signature = hmac.new(
            self.ipn_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

# Initialize payment handler
nowpayments = NOWPayments()

async def initiate_crypto_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start crypto payment process"""
    query = update.callback_query
    await query.answer()
    
    escrow_id = query.data.replace("pay_crypto_", "")
    
    if escrow_id not in ESCROWS:
        await query.edit_message_text("❌ Escrow not found.")
        return
    
    escrow = ESCROWS[escrow_id]
    amount = float(escrow["amount"].replace("$", ""))
    
    # Get available currencies
    currencies = await nowpayments.get_available_currencies()
    popular_currencies = ["btc", "eth", "usdt", "usdc", "ltc", "ada", "dot"]
    
    # Filter to show only popular currencies that are available
    available_popular = [curr for curr in popular_currencies if curr in currencies]
    
    keyboard = []
    for i in range(0, len(available_popular), 2):
        row = []
        for j in range(2):
            if i + j < len(available_popular):
                curr = available_popular[i + j]
                row.append(InlineKeyboardButton(
                    f"{curr.upper()}", 
                    callback_data=f"select_crypto_{escrow_id}_{curr}"
                ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"escrow_details_{escrow_id}")])
    
    await query.edit_message_text(
        f"💰 *Payment for Escrow #{escrow_id}*\n\n"
        f"Amount: ${amount}\n"
        f"Item: {escrow['item']}\n\n"
        f"Choose your preferred cryptocurrency:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_crypto_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process selected cryptocurrency and create payment"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split("_")
    escrow_id = data_parts[2]
    currency = data_parts[3]
    
    if escrow_id not in ESCROWS:
        await query.edit_message_text("❌ Escrow not found.")
        return
    
    escrow = ESCROWS[escrow_id]
    amount = float(escrow["amount"].replace("$", ""))
    
    # Create payment with NOWPayments
    payment_data = await nowpayments.create_payment(
        amount_usd=amount,
        currency=currency,
        order_id=f"escrow_{escrow_id}_{update.effective_user.id}",
        description=f"Escrow payment for {escrow['item']}"
    )
    
    if not payment_data:
        await query.edit_message_text("❌ Failed to create payment. Please try again.")
        return
    
    # Store payment session
    payment_id = payment_data["payment_id"]
    PAYMENT_SESSIONS[payment_id] = {
        "escrow_id": escrow_id,
        "user_id": update.effective_user.id,
        "amount": amount,
        "currency": currency,
        "status": "waiting"
    }
    
    pay_address = payment_data["pay_address"]
    pay_amount = payment_data["pay_amount"]
    
    message = f"💰 *Crypto Payment Details*\n\n"
    message += f"🏷️ Order ID: `{payment_data['order_id']}`\n"
    message += f"💎 Currency: {currency.upper()}\n"
    message += f"💳 Amount to Pay: `{pay_amount}` {currency.upper()}\n"
    message += f"📍 Payment Address:\n`{pay_address}`\n\n"
    message += f"⏱️ Payment expires in: 60 minutes\n\n"
    message += f"⚠️ *Important:*\n"
    message += f"• Send EXACTLY `{pay_amount}` {currency.upper()}\n"
    message += f"• Use the address above only\n"
    message += f"• Payment will be confirmed automatically\n"
    message += f"• Do not send from an exchange"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Check Payment Status", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("🔙 Back to Escrow", callback_data=f"escrow_details_{escrow_id}")]
    ]
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check payment status"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("check_payment_", "")
    
    if payment_id not in PAYMENT_SESSIONS:
        await query.edit_message_text("❌ Payment session not found.")
        return
    
    payment_data = await nowpayments.get_payment_status(payment_id)
    
    if not payment_data:
        await query.edit_message_text("❌ Failed to check payment status.")
        return
    
    session = PAYMENT_SESSIONS[payment_id]
    status = payment_data["payment_status"]
    
    if status == "finished":
        # Payment completed
        escrow_id = session["escrow_id"]
        ESCROWS[escrow_id]["payment_status"] = "paid"
        ESCROWS[escrow_id]["payment_id"] = payment_id
        
        await query.edit_message_text(
            f"✅ *Payment Confirmed!*\n\n"
            f"💰 Amount: {session['amount']} USD\n"
            f"💎 Currency: {session['currency'].upper()}\n"
            f"🆔 Payment ID: `{payment_id}`\n\n"
            f"The escrow is now funded and active!",
            parse_mode="Markdown"
        )
        
        # Notify other party
        escrow = ESCROWS[escrow_id]
        if escrow.get("buyer") and escrow.get("seller_id"):
            try:
                await context.bot.send_message(
                    chat_id=escrow["seller_id"],
                    text=f"✅ Escrow #{escrow_id} has been funded!\n"
                         f"The buyer has completed the crypto payment."
                )
            except Exception as e:
                print(f"Error notifying seller: {e}")
                
    elif status == "expired" or status == "failed":
        await query.edit_message_text(
            f"❌ Payment {status.title()}\n\n"
            f"Please create a new payment to continue with the escrow.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Try Again", callback_data=f"pay_crypto_{session['escrow_id']}")
            ]])
        )
    else:
        # Still waiting
        await query.edit_message_text(
            f"⏳ Payment Status: {status.title()}\n\n"
            f"Please complete your payment and check again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Check Again", callback_data=f"check_payment_{payment_id}")
            ]])
        )

def register_handlers(app):
    app.add_handler(CallbackQueryHandler(initiate_crypto_payment, pattern="^pay_crypto_"))
    app.add_handler(CallbackQueryHandler(process_crypto_selection, pattern="^select_crypto_"))
    app.add_handler(CallbackQueryHandler(check_payment_status, pattern="^check_payment_"))
