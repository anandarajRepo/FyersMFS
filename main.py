# main.py

"""
FyersMMFS - 5-Minute Market Force Scalping Strategy
Main entry point for the trading system
"""

import asyncio
import sys
from pathlib import Path
from utils.enhanced_auth_helper import (
    setup_auth_only,
    authenticate_fyers,
    test_authentication,
    update_pin_only,
    show_authentication_status
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.helpers import is_market_open
from config import (
    load_mmfs_config_from_env,
    validate_mmfs_config,
    get_mmfs_symbols,
    get_primary_symbols
)
from services import (
    FyersAuth,
    DataService,
    MarketBreadthService,
    SimulatedMarketBreadthService,
    OrderManager
)
from strategy import MMFSStrategy

# Setup logger
logger = setup_logger('mmfs')


async def run_mmfs_strategy(use_simulated_breadth: bool = False):
    """
    Run MMFS Strategy

    Args:
        use_simulated_breadth: Use simulated market breadth for testing
    """
    try:
        logger.info("=" * 80)
        logger.info(" FyersMMFS - Starting System")
        logger.info("=" * 80)

        # Step 1: Load and validate configuration
        logger.info("\n Step 1: Loading Configuration")
        strategy_config, trading_config = load_mmfs_config_from_env()

        validation = validate_mmfs_config(strategy_config)
        if not validation['valid']:
            logger.error(f" Invalid configuration: {validation['errors']}")
            return

        if validation['warnings']:
            for warning in validation['warnings']:
                logger.warning(f"  {warning}")

        logger.info(f" Configuration loaded successfully")
        logger.info(f"  Portfolio: Rs.{strategy_config.portfolio_value:,}")
        logger.info(f"  Risk per Trade: {strategy_config.risk_per_trade_pct}%")
        logger.info(f"  Max Trades: {strategy_config.max_trades_per_day}")

        # Step 2: Check market status
        logger.info("\n Step 2: Checking Market Status")
        is_open, reason = is_market_open()
        logger.info(f"  Market Status: {reason}")

        if not is_open:
            logger.warning("  Market is not open. Running in test mode.")

        # Step 3: Initialize Fyers authentication
        logger.info("\n Step 3: Authenticating with Fyers")
        auth = FyersAuth()
        success = await auth.initialize()

        if not success:
            logger.error(" Authentication failed")
            logger.info("\nTo set up authentication:")
            logger.info("1. python services/fyers_auth.py --generate-url")
            logger.info("2. Visit the URL and authorize")
            logger.info("3. python services/fyers_auth.py --generate-token YOUR_AUTH_CODE")
            return

        logger.info(" Authentication successful")

        # Step 4: Initialize services
        logger.info("\n  Step 4: Initializing Services")

        fyers_client = auth.get_client()
        data_service = DataService(fyers_client)
        order_manager = OrderManager(fyers_client)

        # Market breadth service
        if use_simulated_breadth:
            logger.info("  Using simulated market breadth")
            breadth_service = SimulatedMarketBreadthService(
                simulated_advances=150,
                simulated_declines=100
            )
        else:
            logger.info("  Using real NSE market breadth")
            breadth_service = MarketBreadthService()

        logger.info(" Services initialized")

        # Step 5: Load symbols
        logger.info("\n Step 5: Loading Trading Symbols")
        primary_symbols = get_primary_symbols()
        symbol_list = list(primary_symbols.keys())

        logger.info(f"  Primary symbols: {', '.join(symbol_list)}")
        logger.info(f"  Total: {len(symbol_list)} symbols")

        # Step 6: Create and start strategy
        logger.info("\n Step 6: Initializing MMFS Strategy")

        strategy = MMFSStrategy(
            strategy_config=strategy_config,
            trading_config=trading_config,
            data_service=data_service,
            order_manager=order_manager,
            breadth_service=breadth_service,
            symbols=symbol_list
        )

        logger.info(" Strategy initialized")
        logger.info("\n" + "=" * 80)

        # Start strategy
        await strategy.start()

    except KeyboardInterrupt:
        logger.info("\n\n  Interrupted by user")
    except Exception as e:
        logger.error(f"\n Error running MMFS strategy: {e}", exc_info=True)
    finally:
        logger.info("\n" + "=" * 80)
        logger.info(" System Shutdown Complete")
        logger.info("=" * 80)


async def test_components():
    """Test individual components"""
    logger.info(" Testing Components")
    logger.info("=" * 60)

    # Test authentication
    logger.info("\n1. Testing Authentication:")
    auth = FyersAuth()
    success = await auth.initialize()
    logger.info(f"  {'' if success else ''} Authentication")

    if success:
        # Test data service
        logger.info("\n2. Testing Data Service:")
        data_service = DataService(auth.get_client())
        symbol = "NSE:NIFTY50-INDEX"

        prev_data = await data_service.get_previous_day_data(symbol)
        logger.info(f"  {'' if prev_data else ''} Previous day data")

        quote = await data_service.get_current_quote(symbol)
        logger.info(f"  {'' if quote else ''} Current quote")

        # Test market breadth
        logger.info("\n3. Testing Market Breadth:")
        breadth_service = SimulatedMarketBreadthService()
        summary = breadth_service.get_breadth_summary()
        logger.info(f"  {'' if summary['available'] else ''} Market breadth")
        logger.info(f"  Classification: {summary.get('classification', 'Unknown')}")

    logger.info("\n" + "=" * 60)
    
    
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
            logger.error(" Authentication failed. Please run 'python main.py auth' to setup authentication")
            return

        logger.info(" Authentication successful - Access token validated")

        # Log strategy configuration
        logger.info(f"Portfolio Value: ₹{strategy_config.portfolio_value:,}")
        logger.info(f"Risk per Trade: {strategy_config.risk_per_trade_pct}%")
        logger.info(f"Max Positions: {strategy_config.max_positions}")
        logger.info(f"MFS Period: First 5 minutes of market")

        # Create and run strategy
        strategy = MFSStrategy(
            fyers_config=config_dict['fyers_config'],
            strategy_config=strategy_config,
            trading_config=trading_config,
            ws_config=ws_config
        )

        # Run strategy
        logger.info(" Initializing MFS Strategy...")
        await strategy.run()

    except KeyboardInterrupt:
        logger.info(" Strategy stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f" Fatal error in main: {e}")
        logger.exception("Full error details:")


def main():
    """Enhanced main entry point with authentication commands"""

    # Display header
    print("=" * 80)
    print("    5-MINUTE MARKET FORCE SCALPING (MFS) STRATEGY")
    print("    Advanced Ultra-Short Scalping System")
    print("=" * 80)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "run":
            logger.info(" Starting 5-Minute Market Force Scalping Strategy")
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
                print(f"  python main.py {cmd:<12} - {desc}")

    else:
        # Interactive menu
        print(" Advanced 5-minute scalping with real-time data")
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
    main()