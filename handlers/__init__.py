from .start import register_handlers as register_start_handlers
from .initiate_trade import register_handlers as register_trade_handlers
from .payments import register_handlers as register_payment_handlers
from .callbacks import register_handlers as register_callback_handlers

def register_all_handlers(app):
    """Register all bot handlers"""
    register_start_handlers(app)
    register_trade_handlers(app)
    register_payment_handlers(app)
    register_callback_handlers(app)