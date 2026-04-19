import os
from dotenv import load_dotenv

# Load all secret variables from the .env file
load_dotenv()

class Config:
    # Flask secret key - required for secure sessions
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    
    # JWT secret key - required for generating secure login tokens
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key')
    
    # Database connection URL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///kapdacare.db')
    
    # Set to False to disable unnecessary overhead and warnings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Set the expiration time for the JWT access token (1 day)
    from datetime import timedelta
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)