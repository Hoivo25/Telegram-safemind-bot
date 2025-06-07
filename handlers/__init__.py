from .callbacks import register_handlers as callback_handlers
from .start import register_handlers as start_handlers
from .initiate_trade import register_functions as create_functions
from .join import register_functions as join_functions
from .router import text_router  # ✅ Fix typo here

def register_all_handlers(app):
    callback_handlers(app)
    start_handlers(app)
    app.add_handler(text_router)