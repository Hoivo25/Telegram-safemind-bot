
try:
    from flask import Flask, request, jsonify
except ImportError:
    print("⚠️ Flask not installed. Webhook server disabled.")
    Flask = None

import json
import threading
import hashlib
import hmac
from config import NOWPAYMENTS_IPN_SECRET
from utils import PAYMENT_SESSIONS, ESCROWS

app = Flask(__name__)

def verify_ipn_signature(payload, signature):
    """Verify IPN callback signature"""
    expected_signature = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

@app.route('/webhook/nowpayments', methods=['POSTT'])
def nowpayments_webhook():
    """Handle NOWPayments IPN callbacks"""
    try:
        # Get signature from headers
        signature = request.headers.get('x-nowpayments-sig')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 400
        
        # Get payload
        payload = request.get_data(as_text=True)
        
        # Verify signature
        if not verify_ipn_signature(payload, signature):
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Parse data
        data = json.loads(payload)
        payment_id = data.get('payment_id')
        payment_status = data.get('payment_status')
        
        if payment_id in PAYMENT_SESSIONS:
            session = PAYMENT_SESSIONS[payment_id]
            escrow_id = session['escrow_id']
            
            if payment_status == 'finished':
                # Mark escrow as paid
                if escrow_id in ESCROWS:
                    ESCROWS[escrow_id]['payment_status'] = 'paid'
                    ESCROWS[escrow_id]['payment_id'] = payment_id
                    print(f"✅ Payment confirmed for escrow {escrow_id}")
            
            elif payment_status in ['failed', 'expired']:
                print(f"❌ Payment {payment_status} for escrow {escrow_id}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': 'Internal error'}), 500

def run_webhook_server():
    """Run Flask webhook server"""
    if Flask is None:
        print("⚠️ Flask not available. Install with: pip install flask")
        return
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"❌ Webhook server error: {e}")'}), 500

def verify_ipn_signature(payload, signature):
    """Verify NOWPayments IPN signature"""
    import hmac
    import hashlib
    
    expected_sig = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode(),
        payload.encode(),
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_sig)

def run_webhook_server():
    """Run webhook server in a separate thread"""
    if Flask is None:
        print("⚠️ Flask not available. Webhook server disabled.")
        return
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"⚠️ Webhook server error: {e}")

if __name__ == '__main__':
    run_webhook_server()
