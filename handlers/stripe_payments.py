
import stripe
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from utils import ESCROWS, PAYMENT_SESSIONS

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

class StripePayments:
    def __init__(self):
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
    
    async def create_payment_link(self, amount_usd, escrow_id, description):
        """Create a Stripe payment link"""
        try:
            # Create a payment link
            payment_link = stripe.PaymentLink.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': description,
                                'description': f'Escrow #{escrow_id}'
                            },
                            'unit_amount': int(amount_usd * 100),  # Stripe uses cents
                        },
                        'quantity': 1,
                    }
                ],
                metadata={
                    'escrow_id': escrow_id,
                    'payment_type': 'escrow'
                },
                after_completion={
                    'type': 'redirect',
                    'redirect': {
                        'url': 'https://t.me/your_bot_username'  # Replace with your bot username
                    }
                }
            )
            return payment_link
        except Exception as e:
            print(f"Stripe payment link creation error: {e}")
            return None
    
    async def create_checkout_session(self, amount_usd, escrow_id, description, success_url, cancel_url):
        """Create a Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': description,
                            'description': f'Escrow #{escrow_id}'
                        },
                        'unit_amount': int(amount_usd * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'escrow_id': escrow_id,
                    'payment_type': 'escrow'
                }
            )
            return session
        except Exception as e:
            print(f"Stripe checkout session creation error: {e}")
            return None
    
    def verify_webhook_signature(self, payload, signature):
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return True
        except Exception as e:
            print(f"Webhook signature verification failed: {e}")
            return False

# Initialize Stripe handler
stripe_payments = StripePayments()

async def initiate_stripe_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Stripe payment process"""
    query = update.callback_query
    await query.answer()
    
    escrow_id = query.data.replace("pay_stripe_", "")
    
    if escrow_id not in ESCROWS:
        await query.edit_message_text("❌ Escrow not found.")
        return
    
    escrow = ESCROWS[escrow_id]
    amount = float(escrow["amount"].replace("$", ""))
    description = f"Escrow payment for {escrow['item']}"
    
    # Create payment link
    payment_link = await stripe_payments.create_payment_link(
        amount_usd=amount,
        escrow_id=escrow_id,
        description=description
    )
    
    if not payment_link:
        await query.edit_message_text("❌ Failed to create payment link. Please try again.")
        return
    
    # Store payment session
    payment_id = payment_link.id
    PAYMENT_SESSIONS[payment_id] = {
        "escrow_id": escrow_id,
        "user_id": update.effective_user.id,
        "amount": amount,
        "currency": "usd",
        "status": "waiting",
        "payment_type": "stripe"
    }
    
    message = f"💳 *Stripe Payment*\n\n"
    message += f"🏷️ Escrow ID: #{escrow_id}\n"
    message += f"💰 Amount: ${amount}\n"
    message += f"📦 Item: {escrow['item']}\n\n"
    message += f"Click the link below to pay with your credit/debit card:\n"
    message += f"🔗 [Pay with Stripe]({payment_link.url})\n\n"
    message += f"⚠️ *Important:*\n"
    message += f"• Secure payment processing by Stripe\n"
    message += f"• Your card details are never stored\n"
    message += f"• Payment will be confirmed automatically\n"
    message += f"• You'll receive an email receipt"
    
    keyboard = [
        [InlineKeyboardButton("💳 Pay with Stripe", url=payment_link.url)],
        [InlineKeyboardButton("🔄 Check Payment Status", callback_data=f"check_stripe_{payment_id}")],
        [InlineKeyboardButton("🔙 Back to Escrow", callback_data=f"escrow_details_{escrow_id}")]
    ]
    
    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def check_stripe_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check Stripe payment status"""
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("check_stripe_", "")
    
    if payment_id not in PAYMENT_SESSIONS:
        await query.edit_message_text("❌ Payment session not found.")
        return
    
    try:
        # Get payment link details
        payment_link = stripe.PaymentLink.retrieve(payment_id)
        
        # Check if there are any successful payments for this link
        sessions = stripe.checkout.Session.list(
            payment_link=payment_id,
            limit=10
        )
        
        session = PAYMENT_SESSIONS[payment_id]
        escrow_id = session["escrow_id"]
        
        # Look for completed sessions
        completed_session = None
        for sess in sessions.data:
            if sess.payment_status == "paid":
                completed_session = sess
                break
        
        if completed_session:
            # Payment completed
            ESCROWS[escrow_id]["payment_status"] = "paid"
            ESCROWS[escrow_id]["payment_id"] = payment_id
            ESCROWS[escrow_id]["stripe_session_id"] = completed_session.id
            ESCROWS[escrow_id]["funded_at"] = time.time()
            
            await query.edit_message_text(
                f"✅ *Payment Confirmed!*\n\n"
                f"💰 Amount: ${session['amount']}\n"
                f"💳 Payment Method: Stripe\n"
                f"🆔 Session ID: `{completed_session.id}`\n\n"
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
                             f"The buyer has completed the Stripe payment."
                    )
                except Exception as e:
                    print(f"Error notifying seller: {e}")
        else:
            # Still waiting
            await query.edit_message_text(
                "⏳ Payment Status: Pending\n\n"
                "Please complete your payment and check again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Check Again", callback_data=f"check_stripe_{payment_id}")
                ]])
            )
            
    except Exception as e:
        print(f"Error checking Stripe payment: {e}")
        await query.edit_message_text("❌ Failed to check payment status.")

def register_handlers(app):
    app.add_handler(CallbackQueryHandler(initiate_stripe_payment, pattern="^pay_stripe_"))
    app.add_handler(CallbackQueryHandler(check_stripe_payment_status, pattern="^check_stripe_"))
