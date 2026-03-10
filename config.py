# import os
# from datetime import timedelta

# class Config:
#     """Base configuration class with common settings"""
    
#     # Secret key for session management and CSRF protection
#     SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
#     # Database configuration - using SQLite for simplicity
#     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///workshop.db'
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
    
#     # Session configuration
#     PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
#     # Mail configuration (for future use in Phase 5)
#     MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
#     MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
#     MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
#     MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
#     MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
#     MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')


# class DevelopmentConfig(Config):
#     """Development configuration"""
    
#     DEBUG = True
#     # Show SQL queries in console during development
#     SQLALCHEMY_ECHO = True


# class ProductionConfig(Config):
#     """Production configuration"""
    
#     DEBUG = False
#     # Use a different secret key in production
#     SECRET_KEY = os.environ.get('SECRET_KEY')


# # Configuration dictionary
# config = {
#     'development': DevelopmentConfig,
#     'production': ProductionConfig,
#     'default': DevelopmentConfig
# }
import os
from datetime import timedelta
from pathlib import Path

class Config:
    """Base configuration class with common settings"""
    
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Get the base directory (project root)
    BASE_DIR = Path(__file__).parent
    
    # Database configuration - using SQLite for simplicity
    # Use absolute path to ensure consistency across all scripts
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "instance" / "workshop.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Mail configuration (for future use in Phase 5)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')


class DevelopmentConfig(Config):
    """Development configuration"""
    
    DEBUG = True
    # Show SQL queries in console during development
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    
    DEBUG = False
    # Use a different secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}