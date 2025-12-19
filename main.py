# main.py

"""
FyersMMFS - 5-Minute Market Force Scalping Strategy
Main entry point for the trading system
"""

import asyncio
import sys
from pathlib import Path

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
        logger.info("🚀 FyersMMFS - Starting System")
        logger.info("=" * 80)

        # Step 1: Load and validate configuration
        logger.info("\n📋 Step 1: Loading Configuration")
        strategy_config, trading_config = load_mmfs_config_from_env()

        validation = validate_mmfs_config(strategy_config)
        if not validation['valid']:
            logger.error(f"❌ Invalid configuration: {validation['errors']}")
            return

        if validation['warnings']:
            for warning in validation['warnings']:
                logger.warning(f"⚠️  {warning}")

        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  Portfolio: ₹{strategy_config.portfolio_value:,}")
        logger.info(f"  Risk per Trade: {strategy_config.risk_per_trade_pct}%")
        logger.info(f"  Max Trades: {strategy_config.max_trades_per_day}")

        # Step 2: Check market status
        logger.info("\n🕐 Step 2: Checking Market Status")
        is_open, reason = is_market_open()
        logger.info(f"  Market Status: {reason}")

        if not is_open:
            logger.warning("⚠️  Market is not open. Running in test mode.")

        # Step 3: Initialize Fyers authentication
        logger.info("\n🔐 Step 3: Authenticating with Fyers")
        auth = FyersAuth()
        success = await auth.initialize()

        if not success:
            logger.error("❌ Authentication failed")
            logger.info("\nTo set up authentication:")
            logger.info("1. python services/fyers_auth.py --generate-url")
            logger.info("2. Visit the URL and authorize")
            logger.info("3. python services/fyers_auth.py --generate-token YOUR_AUTH_CODE")
            return

        logger.info("✓ Authentication successful")

        # Step 4: Initialize services
        logger.info("\n⚙️  Step 4: Initializing Services")

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

        logger.info("✓ Services initialized")

        # Step 5: Load symbols
        logger.info("\n📊 Step 5: Loading Trading Symbols")
        primary_symbols = get_primary_symbols()
        symbol_list = list(primary_symbols.keys())

        logger.info(f"  Primary symbols: {', '.join(symbol_list)}")
        logger.info(f"  Total: {len(symbol_list)} symbols")

        # Step 6: Create and start strategy
        logger.info("\n🎯 Step 6: Initializing MMFS Strategy")

        strategy = MMFSStrategy(
            strategy_config=strategy_config,
            trading_config=trading_config,
            data_service=data_service,
            order_manager=order_manager,
            breadth_service=breadth_service,
            symbols=symbol_list
        )

        logger.info("✓ Strategy initialized")
        logger.info("\n" + "=" * 80)

        # Start strategy
        await strategy.start()

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error running MMFS strategy: {e}", exc_info=True)
    finally:
        logger.info("\n" + "=" * 80)
        logger.info("🛑 System Shutdown Complete")
        logger.info("=" * 80)


async def test_components():
    """Test individual components"""
    logger.info("🧪 Testing Components")
    logger.info("=" * 60)

    # Test authentication
    logger.info("\n1. Testing Authentication:")
    auth = FyersAuth()
    success = await auth.initialize()
    logger.info(f"  {'✓' if success else '✗'} Authentication")

    if success:
        # Test data service
        logger.info("\n2. Testing Data Service:")
        data_service = DataService(auth.get_client())
        symbol = "NSE:NIFTY50-INDEX"

        prev_data = await data_service.get_previous_day_data(symbol)
        logger.info(f"  {'✓' if prev_data else '✗'} Previous day data")

        quote = await data_service.get_current_quote(symbol)
        logger.info(f"  {'✓' if quote else '✗'} Current quote")

        # Test market breadth
        logger.info("\n3. Testing Market Breadth:")
        breadth_service = SimulatedMarketBreadthService()
        summary = breadth_service.get_breadth_summary()
        logger.info(f"  {'✓' if summary['available'] else '✗'} Market breadth")
        logger.info(f"  Classification: {summary.get('classification', 'Unknown')}")

    logger.info("\n" + "=" * 60)


def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║               FyersMMFS Trading System                     ║
    ║        5-Minute Market Force Scalping Strategy             ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        print("Usage: python main.py <command>")
        print("\nCommands:")
        print("  run         - Run MMFS strategy (live/paper)")
        print("  test        - Test components")
        print("  sim         - Run with simulated market breadth")
        print("  auth        - Generate authentication URL")
        print("\nExamples:")
        print("  python main.py run")
        print("  python main.py test")
        print("  python main.py sim")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "run":
        asyncio.run(run_mmfs_strategy(use_simulated_breadth=False))

    elif command == "sim":
        asyncio.run(run_mmfs_strategy(use_simulated_breadth=True))

    elif command == "test":
        asyncio.run(test_components())

    elif command == "auth":
        auth = FyersAuth()
        auth.generate_auth_url()

    else:
        print(f"Unknown command: {command}")
        print("Run 'python main.py' without arguments for help")
        sys.exit(1)


if __name__ == "__main__":
    main()