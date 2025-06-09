
import stripe
import json
from flask import Flask, request
from config import STRIPE_WEBHOOK_SECRET
from utils import ESCROWS, PAYMENT_SESSIONS

stripe_webhook_app = Flask(__name__)

@stripe_webhook_app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"Payment succeeded: {payment_intent['id']}")
    
    return "Success", 200

def handle_successful_payment(session):
    """Handle successful Stripe payment"""
    try:
        escrow_id = session['metadata'].get('escrow_id')
        if escrow_id and escrow_id in ESCROWS:
            # Update escrow status
            ESCROWS[escrow_id]["payment_status"] = "paid"
            ESCROWS[escrow_id]["stripe_session_id"] = session['id']
            ESCROWS[escrow_id]["funded_at"] = time.time()
            
            print(f"Escrow #{escrow_id} funded via Stripe: {session['id']}")
    except Exception as e:
        print(f"Error handling Stripe payment: {e}")

if __name__ == '__main__':
    stripe_webhook_app.run(debug=True, port=5001)
