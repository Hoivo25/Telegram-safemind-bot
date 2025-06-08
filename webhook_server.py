
from flask import Flask, request, jsonify
import json
import threading
from handlers.payments import nowpayments
from utils import PAYMENT_SESSIONS, ESCROWS

app = Flask(__name__)

@app.route('/webhook/nowpayments', methods=['POST'])
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
        if not nowpayments.verify_ipn_signature(payload, signature):
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
    """Run webhook server in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    run_webhook_server()
