from .start import register_handlers as register_start_handlers
from .initiate_trade import register_handlers as register_trade_handlers
from .payments import register_handlers as register_payment_handlers
from .callbacks import register_handlers as register_callback_handlers
from .wallet import register_handlers as register_wallet_handlers  
from .escrow_actions import register_handlers as register_escrow_action_handlers
from .router import text_router

def register_all_handlers(app):
    """Register all bot handlers"""
    register_start_handlers(app)
    register_trade_handlers(app)
    register_payment_handlers(app)
    register_callback_handlers(app)
    register_wallet_handlers(app)
    register_escrow_action_handlers(app)
    app.add_handler(text_router)