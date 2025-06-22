"""
Base database configuration and common utilities.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from contextlib import contextmanager
import logging

# Database instance
db = SQLAlchemy()
migrate = Migrate()

# Logger for database operations
db_logger = logging.getLogger('economy.database')

@contextmanager
def db_transaction():
    """Context manager for database transactions with automatic rollback on error."""
    try:
        db.session.begin()
        yield db.session
        db.session.commit()
        db_logger.debug("Database transaction committed successfully")
    except Exception as e:
        db.session.rollback()
        db_logger.error(f"Database transaction failed, rolling back: {e}")
        raise
    finally:
        db.session.close()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()
        db_logger.info("Database tables created successfully")

class TimestampMixin:
    """Mixin class to add created_at and updated_at timestamps to models."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False) 