# utils.py

# This dictionary stores all ongoing escrows.
# You can replace this with a database later.
ESCROWS = {}

# User statistics tracking
USER_STATS = {
    # Example structure:
    # "username": {
    #     "trades_completed": 0,
    #     "trades_cancelled": 0,
    #     "total_volume": 0,
    #     "reputation": 5.0
    # }
}

# Payment sessions tracking
PAYMENT_SESSIONS = {
    # Example structure:
    # "payment_id": {
    #     "escrow_id": "seller_username",
    #     "user_id": 123456789,
    #     "amount": 100.0,
    #     "currency": "btc",
    #     "status": "waiting"
    # }
}