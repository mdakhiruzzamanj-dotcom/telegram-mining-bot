import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = "7837389709:AAEue6M60TRpL7F1adZwsFhkrPx6awll6K4"
    
    # Database URL (Render provides DATABASE_URL)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///mining_bot.db')
    # Convert SQLite URL to PostgreSQL for Render
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Admin ID for manual payments
    ADMIN_ID = int(os.getenv('ADMIN_ID', 123456789))
    
    # Mining settings
    MINING_RATES = {
        'basic': 0.5,
        'premium': 2.0,
        'pro': 5.0
    }
    
    # Ads settings
    AD_DURATION = 5
    MINING_DURATION = 30
    
    # Payment settings
    PAYMENT_CURRENCIES = ['BTTC', 'BONK', 'PEPE']
    PAYMENT_RATES = {
        'BTTC': 1000,
        'BONK': 50000,
        'PEPE': 200000
    }
    
    # Monetag Settings
    MONETAG_ZONE_ID = '9945520'
    MONETAG_SDK_URL = '//libtl.com/sdk.js'
