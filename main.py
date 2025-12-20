# main.py - Complete Example for MFS Strategy with Authentication

"""
5-Minute Market Force Scalping (MFS) Strategy
Complete main entry point with authentication integration
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables
load_dotenv()


# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'mfs_strategy.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )


setup_logging()
logger = logging.getLogger(__name__)

# Import authentication utilities
from utils.enhanced_auth_helper import (
    setup_auth_only,
    authenticate_fyers,
    test_authentication,
    update_pin_only,
    show_authentication_status
)


# Configuration Classes (if you don't have separate config files)
@dataclass
class FyersConfig:
    """Fyers API Configuration"""
    client_id: str
    secret_key: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    base_url: str = "https://api-t1.fyers.in/api/v3"


@dataclass
class MFSStrategyConfig:
    """MFS Strategy Configuration"""
    # Portfolio settings
    portfolio_value: float = 5000
    risk_per_trade_pct: float = 1.0
    max_positions: int = 3

    # MFS specific parameters
    mfs_period_minutes: int = 5
    min_gap_threshold: float = 0.5
    max_gap_threshold: float = 2.0

    # Risk management
    stop_loss_pct: float = 1.0
    target_multiplier: float = 2.0
    trailing_stop_pct: float = 0.5

    # Signal filtering
    min_confidence: float = 0.65
    min_volume_ratio: float = 1.5

    # Position management
    enable_trailing_stops: bool = True
    enable_partial_exits: bool = True
    partial_exit_pct: float = 50.0


@dataclass
class TradingConfig:
    """Trading Configuration"""
    market_start_hour: int = 9
    market_start_minute: int = 15
    market_end_hour: int = 15
    market_end_minute: int = 30
    mfs_start_minute: int = 15
    mfs_end_minute: int = 20
    signal_generation_end_hour: int = 15
    signal_generation_end_minute: int = 0
    monitoring_interval: int = 1
    position_update_interval: int = 5


@dataclass
class WebSocketConfig:
    """WebSocket Configuration"""
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    ping_interval: int = 30
    connection_timeout: int = 30


def load_configuration():
    """Load all configuration from environment variables"""
    try:
        # Fyers configuration
        fyers_config = FyersConfig(
            client_id=os.environ.get('FYERS_CLIENT_ID', ''),
            secret_key=os.environ.get('FYERS_SECRET_KEY', ''),
            access_token=os.environ.get('FYERS_ACCESS_TOKEN'),
            refresh_token=os.environ.get('FYERS_REFRESH_TOKEN')
        )

        # MFS Strategy configuration
        strategy_config = MFSStrategyConfig(
            portfolio_value=float(os.environ.get('PORTFOLIO_VALUE', 5000)),
            risk_per_trade_pct=float(os.environ.get('RISK_PER_TRADE', 1.0)),
            max_positions=int(os.environ.get('MAX_POSITIONS', 3)),
            mfs_period_minutes=int(os.environ.get('MFS_PERIOD_MINUTES', 5)),
            min_gap_threshold=float(os.environ.get('MIN_GAP_THRESHOLD', 0.5)),
            max_gap_threshold=float(os.environ.get('MAX_GAP_THRESHOLD', 2.0)),
            stop_loss_pct=float(os.environ.get('STOP_LOSS_PCT', 1.0)),
            target_multiplier=float(os.environ.get('TARGET_MULTIPLIER', 2.0)),
            trailing_stop_pct=float(os.environ.get('TRAILING_STOP_PCT', 0.5)),
            min_confidence=float(os.environ.get('MIN_CONFIDENCE', 0.65)),
            min_volume_ratio=float(os.environ.get('MIN_VOLUME_RATIO', 1.5)),
            enable_trailing_stops=os.environ.get('ENABLE_TRAILING_STOPS', 'true').lower() == 'true',
            enable_partial_exits=os.environ.get('ENABLE_PARTIAL_EXITS', 'true').lower() == 'true',
            partial_exit_pct=float(os.environ.get('PARTIAL_EXIT_PCT', 50.0))
        )

        # Trading configuration
        trading_config = TradingConfig()

        # WebSocket configuration
        ws_config = WebSocketConfig(
            max_reconnect_attempts=int(os.environ.get('WS_MAX_RECONNECT_ATTEMPTS', 10)),
            ping_interval=int(os.environ.get('WS_PING_INTERVAL', 30)),
            connection_timeout=int(os.environ.get('WS_CONNECTION_TIMEOUT', 30))
        )

        return fyers_config, strategy_config, trading_config, ws_config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


async def run_mfs_strategy():
    """Main function to run the MFS strategy with enhanced authentication"""
    try:
        logger.info("=" * 60)
        logger.info("STARTING 5-MINUTE MARKET FORCE SCALPING STRATEGY")
        logger.info("=" * 60)

        # Load configuration
        fyers_config, strategy_config, trading_config, ws_config = load_configuration()

        # Validate basic configuration
        if not all([fyers_config.client_id, fyers_config.secret_key]):
            logger.error(" Missing required Fyers API credentials")
            logger.error("Please set FYERS_CLIENT_ID and FYERS_SECRET_KEY in .env file")
            logger.error("Run 'python main.py auth' to setup authentication")
            return

        # Enhanced authentication with auto-refresh
        config_dict = {'fyers_config': fyers_config}
        if not authenticate_fyers(config_dict):
            logger.error(" Authentication failed. Please run 'python main.py auth'")
            return

        logger.info(" Authentication successful - Access token validated")

        # Log strategy configuration
        logger.info(f"Portfolio Value: Rs.{strategy_config.portfolio_value:,}")
        logger.info(f"Risk per Trade: {strategy_config.risk_per_trade_pct}%")
        logger.info(f"Max Positions: {strategy_config.max_positions}")
        logger.info(f"MFS Period: First {strategy_config.mfs_period_minutes} minutes (9:15-9:20 AM)")
        logger.info(f"Gap Threshold: {strategy_config.min_gap_threshold}% - {strategy_config.max_gap_threshold}%")

        # TODO: Initialize and run your actual MFS strategy here
        logger.info(" MFS Strategy initialized successfully")
        logger.info("  Strategy implementation placeholder - add your strategy logic here")

        # Example:
        strategy = MFSStrategy(
            fyers_config=config_dict['fyers_config'],
            strategy_config=strategy_config,
            trading_config=trading_config,
            ws_config=ws_config
        )
        await strategy.run()

    except KeyboardInterrupt:
        logger.info(" Strategy stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f" Fatal error in main: {e}")
        logger.exception("Full error details:")


def show_strategy_help():
    """Show strategy configuration guide"""
    print("\n" + "=" * 80)
    print("5-MINUTE MARKET FORCE SCALPING (MFS) STRATEGY - CONFIGURATION GUIDE")
    print("=" * 80)

    print("\n STRATEGY OVERVIEW:")
    print("• Trades during first 5 minutes of market open (9:15-9:20 AM IST)")
    print("• 4 distinct setups based on gap analysis and market breadth")
    print("• Ultra-short holding periods (typically < 5 minutes)")
    print("• High win rate target: 70-80%")

    print("\n CONFIGURATION PARAMETERS:")
    print("Edit .env file to customize:")

    print("\n Portfolio Settings:")
    print("  PORTFOLIO_VALUE=5000          # Total capital (₹5,000)")
    print("  RISK_PER_TRADE=1.0            # Risk 1% per trade")
    print("  MAX_POSITIONS=3               # Max 3 concurrent positions")

    print("\n MFS Parameters:")
    print("  MFS_PERIOD_MINUTES=5          # First 5 minutes only")
    print("  MIN_GAP_THRESHOLD=0.5         # Minimum gap size (0.5%)")
    print("  MAX_GAP_THRESHOLD=2.0         # Maximum gap size (2.0%)")

    print("\n Risk Management:")
    print("  STOP_LOSS_PCT=1.0             # 1% stop loss")
    print("  TARGET_MULTIPLIER=2.0         # 2:1 reward-risk ratio")
    print("  TRAILING_STOP_PCT=0.5         # 0.5% trailing stop")

    print("\n Signal Filtering:")
    print("  MIN_CONFIDENCE=0.65           # Minimum 65% confidence")
    print("  MIN_VOLUME_RATIO=1.5          # 1.5x average volume")

    print("\n TRADING SCHEDULE:")
    print("  Market Open: 09:15 AM IST")
    print("  MFS Period: 09:15 - 09:20 AM (5 minutes)")
    print("  Position Monitoring: Until 3:15 PM")
    print("  Market Close: 03:30 PM IST")

    print("\n EXPECTED PERFORMANCE:")
    print("  Daily Signals: 1-4 setups")
    print("  Win Rate Target: 70-80%")
    print("  Avg Holding: 2-5 minutes")
    print("  Risk-Reward: 1:2 minimum")

    print("\n IMPORTANT:")
    print("  • Start with paper trading")
    print("  • Monitor first week closely")
    print("  • Only trade first 5 minutes")
    print("  • Always use stop losses")


def main():
    """Enhanced main entry point with authentication commands"""

    # Display header
    print("=" * 80)
    print("    5-MINUTE MARKET FORCE SCALPING (MFS) STRATEGY")
    print("    Ultra-Short Scalping System with Enhanced Authentication")
    print("=" * 80)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "run":
            logger.info(" Starting MFS Trading Strategy")
            asyncio.run(run_mfs_strategy())

        elif command == "auth":
            print(" Setting up Fyers API Authentication")
            setup_auth_only()

        elif command == "test-auth":
            print(" Testing Fyers API Authentication")
            test_authentication()

        elif command == "update-pin":
            print(" Updating Trading PIN")
            update_pin_only()

        elif command == "auth-status":
            show_authentication_status()

        elif command == "help":
            show_strategy_help()

        else:
            print(f" Unknown command: {command}")
            print("\n Available commands:")
            commands = [
                ("run", "Run the MFS trading strategy"),
                ("auth", "Setup Fyers API authentication"),
                ("test-auth", "Test authentication status"),
                ("update-pin", "Update trading PIN"),
                ("auth-status", "Show detailed authentication status"),
                ("help", "Show strategy configuration guide"),
            ]

            for cmd, desc in commands:
                print(f"  python main.py {cmd:<15} - {desc}")

    else:
        # Interactive menu
        print(" Ultra-short scalping with 5-minute window")
        print(" Secure authentication with auto-refresh")
        print("\nSelect an option:")

        menu_options = [
            ("1", " Run MFS Trading Strategy"),
            ("2", " Setup Fyers Authentication"),
            ("3", " Test Authentication"),
            ("4", " Update Trading PIN"),
            ("5", " Show Authentication Status"),
            ("6", " Strategy Configuration Guide"),
            ("7", " Exit")
        ]

        for option, description in menu_options:
            print(f"{option:>2}. {description}")

        choice = input(f"\nSelect option (1-{len(menu_options)}): ").strip()

        if choice == "1":
            logger.info(" Starting MFS Strategy")
            asyncio.run(run_mfs_strategy())

        elif choice == "2":
            print(" Setting up Fyers API Authentication")
            setup_auth_only()

        elif choice == "3":
            print(" Testing Fyers API Authentication")
            test_authentication()

        elif choice == "4":
            print(" Updating Trading PIN")
            update_pin_only()

        elif choice == "5":
            show_authentication_status()

        elif choice == "6":
            show_strategy_help()

        elif choice == "7":
            print("\n Goodbye! Happy Trading!")
            print(" Remember: Trade responsibly and manage your risk!")

        else:
            print(f" Invalid choice: {choice}")
            print("Please select a number between 1 and 7")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n Interrupted by user - Goodbye!")
    except Exception as e:
        logger.error(f" Fatal error in main execution: {e}")
        logger.exception("Full error details:")
        sys.exit(1)