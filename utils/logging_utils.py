"""
Logging utilities
"""

import logging
from flask import current_app

def get_logger(name=None):
    """Get a logger instance"""
    if name:
        return logging.getLogger(f'economy.{name}')
    else:
        return current_app.logger if current_app else logging.getLogger('economy')

# Create common loggers
app_logger = get_logger('app')
bot_logger = get_logger('bot')
cog_logger = get_logger('cogs') 