# main.py - Complete Example for MMFS Strategy with Authentication

"""
5-Minute Market Force Scalping (MMFS) Strategy
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
            logging.FileHandler(os.path.join(log_dir, 'mmfs_strategy.log')),
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

# Import strategy and services
from strategy.mmfs_strategy import MMFSStrategy
from services.data_service import DataService
from services.order_manager import OrderManager
from services.market_breadth_service import MarketBreadthService
from config.symbols import get_primary_symbols, format_symbol_for_fyers
from config.mmfs_config import MMFSStrategyConfig, MMFSTradingConfig


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

        # MMFS Strategy configuration
        strategy_config = MMFSStrategyConfig(
            portfolio_value=float(os.environ.get('PORTFOLIO_VALUE', 5000)),
            risk_per_trade_pct=float(os.environ.get('RISK_PER_TRADE', 1.0)),
            max_positions=int(os.environ.get('MAX_POSITIONS', 1)),
            small_gap_threshold=float(os.environ.get('MIN_GAP_THRESHOLD', 0.30)),
            moderate_gap_threshold=float(os.environ.get('MODERATE_GAP_THRESHOLD', 0.80)),
            risk_reward_ratio=float(os.environ.get('RISK_REWARD_RATIO', 1.5)),
            max_trades_per_day=int(os.environ.get('MAX_TRADES_PER_DAY', 2)),
            stop_after_first_loss=os.environ.get('STOP_AFTER_FIRST_LOSS', 'true').lower() == 'true'
        )

        # Trading configuration
        trading_config = MMFSTradingConfig()

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


async def run_mmfs_strategy():
    """Main function to run the MMFS strategy with enhanced authentication"""
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
        logger.info(f"MMFS Period: First {strategy_config.execution_end_minute - strategy_config.execution_start_minute} minutes (9:15-9:20 AM)")
        logger.info(f"Gap Threshold: {strategy_config.small_gap_threshold}% - {strategy_config.moderate_gap_threshold}%")

        # Create Fyers client directly using the authenticated access token
        try:
            from fyers_apiv3 import fyersModel

            # Create Fyers client with authenticated access token
            fyers_client = fyersModel.FyersModel(
                client_id=fyers_config.client_id,
                is_async=False,
                token=fyers_config.access_token,
                # log_path=os.path.join('logs', 'fyers_api.log')
            )

            logger.info(" Fyers client initialized successfully")

            # Quick validation test
            try:
                profile_response = fyers_client.get_profile()
                if profile_response.get('s') == 'ok':
                    profile_data = profile_response.get('data', {})
                    logger.info(f" Connected as: {profile_data.get('name', 'Unknown')}")
                else:
                    logger.warning(f" Profile validation returned: {profile_response.get('message', 'Unknown error')}")
            except Exception as e:
                logger.warning(f" Could not validate profile (will continue anyway): {e}")

        except Exception as e:
            logger.error(f" Failed to initialize Fyers client: {e}")
            return

        # Initialize services
        logger.info("Initializing services...")

        data_service = DataService(fyers_client)
        order_manager = OrderManager(fyers_client)
        breadth_service = MarketBreadthService()

        # Get trading symbols
        primary_symbols = get_primary_symbols()
        symbol_list = [format_symbol_for_fyers(name) for name in primary_symbols.keys()]

        logger.info(f" Trading symbols: {', '.join(primary_symbols.keys())}")

        # Initialize and run MMFS strategy
        logger.info(" MMFS Strategy initialized successfully")
        logger.info(" Starting strategy execution...")

        strategy = MMFSStrategy(
            strategy_config=strategy_config,
            trading_config=trading_config,
            data_service=data_service,
            order_manager=order_manager,
            breadth_service=breadth_service,
            symbols=symbol_list
        )

        await strategy.start()

    except KeyboardInterrupt:
        logger.info(" Strategy stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f" Fatal error in main: {e}")
        logger.exception("Full error details:")


def show_strategy_help():
    """Show strategy configuration guide"""
    print("\n" + "=" * 80)
    print("5-MINUTE MARKET FORCE SCALPING (MMFS) STRATEGY - CONFIGURATION GUIDE")
    print("=" * 80)

    print("\n STRATEGY OVERVIEW:")
    print("• Trades during first 5 minutes of market open (9:15-9:20 AM IST)")
    print("• 4 distinct setups based on gap analysis and market breadth")
    print("• Ultra-short holding periods (typically < 5 minutes)")
    print("• High win rate target: 70-80%")

    print("\n⚙ CONFIGURATION PARAMETERS:")
    print("Edit .env file to customize:")

    print("\n Portfolio Settings:")
    print("  PORTFOLIO_VALUE=5000          # Total capital (₹5,000)")
    print("  RISK_PER_TRADE=1.0            # Risk 1% per trade")
    print("  MAX_POSITIONS=1               # Max 1 concurrent position")

    print("\n MMFS Parameters:")
    print("  MIN_GAP_THRESHOLD=0.30        # Minimum gap size (0.30%)")
    print("  MODERATE_GAP_THRESHOLD=0.80   # Moderate gap threshold (0.80%)")

    print("\n🛡 Risk Management:")
    print("  RISK_REWARD_RATIO=1.5         # 1.5:1 reward-risk ratio")
    print("  MAX_TRADES_PER_DAY=2          # Maximum 2 trades per day")
    print("  STOP_AFTER_FIRST_LOSS=true    # Stop trading till 9:45 after first loss")

    print("\n TRADING SCHEDULE:")
    print("  Market Open: 09:15 AM IST")
    print("  MMFS Period: 09:15 - 09:20 AM (5 minutes)")
    print("  Position Monitoring: Until 3:15 PM")
    print("  Market Close: 03:30 PM IST")

    print("\n EXPECTED PERFORMANCE:")
    print("  Daily Signals: 1-4 setups")
    print("  Win Rate Target: 70-80%")
    print("  Avg Holding: 2-5 minutes")
    print("  Risk-Reward: 1:1.5 minimum")

    print("\n IMPORTANT:")
    print("  • Start with paper trading")
    print("  • Monitor first week closely")
    print("  • Only trade first 5 minutes")
    print("  • Always use stop losses")


def main():
    """Enhanced main entry point with authentication commands"""

    # Display header
    print("=" * 80)
    print("    5-MINUTE MARKET FORCE SCALPING (MMFS) STRATEGY")
    print("    Ultra-Short Scalping System with Enhanced Authentication")
    print("=" * 80)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "run":
            logger.info(" Starting MMFS Trading Strategy")
            asyncio.run(run_mmfs_strategy())

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
                ("run", "Run the MMFS trading strategy"),
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
        print("⚡ Ultra-short scalping with 5-minute window")
        print(" Secure authentication with auto-refresh")
        print("\nSelect an option:")

        menu_options = [
            ("1", " Run MMFS Trading Strategy"),
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
            logger.info(" Starting MMFS Strategy")
            asyncio.run(run_mmfs_strategy())

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