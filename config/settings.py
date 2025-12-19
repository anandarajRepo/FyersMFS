# config/settings.py

"""
Basic settings and enumerations for MMFS strategy
"""

from enum import Enum
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SignalType(Enum):
    """Trade signal types"""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class TradingMode(Enum):
    """Trading mode"""
    PAPER = "PAPER"
    LIVE = "LIVE"


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


# Fyers API Configuration
class FyersAPIConfig:
    """Fyers API Configuration"""
    APP_ID = os.getenv('FYERS_APP_ID', '')
    SECRET_KEY = os.getenv('FYERS_SECRET_KEY', '')
    REDIRECT_URL = os.getenv('FYERS_REDIRECT_URL', 'https://localhost')
    ACCESS_TOKEN = os.getenv('FYERS_ACCESS_TOKEN', '')

    # API endpoints
    BASE_URL = "https://api-t1.fyers.in/api/v3"
    DATA_URL = "https://api-t1.fyers.in/data"
    WEBSOCKET_URL = "wss://api-t1.fyers.in/socket/v3/dataSock"


# Trading Configuration
class TradingConfig:
    """General trading configuration"""
    MODE = TradingMode(os.getenv('TRADING_MODE', 'PAPER').upper())
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'

    # Market hours (IST)
    MARKET_OPEN_HOUR = 9
    MARKET_OPEN_MINUTE = 15
    MARKET_CLOSE_HOUR = 15
    MARKET_CLOSE_MINUTE = 30

    # Data configuration
    USE_WEBSOCKET = os.getenv('USE_WEBSOCKET', 'true').lower() == 'true'
    WEBSOCKET_TIMEOUT = int(os.getenv('WEBSOCKET_TIMEOUT', '30'))
    REST_API_FALLBACK = os.getenv('REST_API_FALLBACK', 'true').lower() == 'true'


# Risk Management Configuration
class RiskConfig:
    """Risk management settings"""
    MAX_DAILY_LOSS_PCT = float(os.getenv('MAX_DAILY_LOSS_PCT', '1.0'))
    EMERGENCY_STOP_LOSS_PCT = float(os.getenv('EMERGENCY_STOP_LOSS_PCT', '2.0'))


# Logging Configuration
class LogConfig:
    """Logging configuration"""
    LOG_DIR = 'logs'
    LOG_FILE_PREFIX = 'mmfs'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


# Database Configuration (Optional)
class DatabaseConfig:
    """Database configuration for trade history"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/mmfs_trades.db')


# Notification Configuration (Optional)
class NotificationConfig:
    """Notification settings"""
    ENABLE_SMS = os.getenv('ENABLE_SMS_ALERTS', 'false').lower() == 'true'
    TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_FROM = os.getenv('TWILIO_FROM_NUMBER', '')
    TWILIO_TO = os.getenv('TWILIO_TO_NUMBER', '')


def validate_configuration():
    """Validate required configuration"""
    errors = []

    if not FyersAPIConfig.APP_ID:
        errors.append("FYERS_APP_ID not set")

    if not FyersAPIConfig.SECRET_KEY:
        errors.append("FYERS_SECRET_KEY not set")

    if not FyersAPIConfig.ACCESS_TOKEN:
        errors.append("FYERS_ACCESS_TOKEN not set")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True


if __name__ == "__main__":
    print("Configuration Settings")
    print("=" * 60)
    print(f"Trading Mode: {TradingConfig.MODE.value}")
    print(f"Log Level: {TradingConfig.LOG_LEVEL}")
    print(f"Use WebSocket: {TradingConfig.USE_WEBSOCKET}")
    print(f"Max Daily Loss: {RiskConfig.MAX_DAILY_LOSS_PCT}%")
    print("=" * 60)

    try:
        validate_configuration()
        print(" Configuration is valid")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")