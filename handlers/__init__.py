
from .callbacks import register_handlers as callback_handlers
from .start import register_handlers as start_handlers
from .initiate_trade import register_handlers as create_handlers
from .join import register_handlers as join_handlers
from .admin import register_handlers as admin_handlers
from .payments import register_handlers as payment_handlers
from .router import text_router

def register_all_handlers(app):
    callback_handlers(app)
    start_handlers(app)
    create_handlers(app)
    join_handlers(app)
    admin_handlers(app)
    payment_handlers(app)
    app.add_handler(text_router)
