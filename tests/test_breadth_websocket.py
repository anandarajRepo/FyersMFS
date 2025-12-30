# tests/test_breadth_websocket.py

"""
Test script for WebSocket-based market breadth tracking
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hybrid_breadth_service import HybridMarketBreadthService
from fyers_apiv3 import fyersModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_hybrid_breadth_service():
    """Test hybrid breadth service with WebSocket"""

    print("=" * 80)
    print(" HYBRID MARKET BREADTH SERVICE TEST")
    print("=" * 80)

    # Load environment
    load_dotenv()

    client_id = os.environ.get('FYERS_CLIENT_ID')
    access_token = os.environ.get('FYERS_ACCESS_TOKEN')

    if not client_id or not access_token:
        print(" ERROR: Missing FYERS_CLIENT_ID or FYERS_ACCESS_TOKEN")
        return False

    try:
        # Create Fyers client
        fyers_client = fyersModel.FyersModel(
            client_id=client_id,
            is_async=False,
            token=access_token
        )

        print(" Fyers client created")

        # Create hybrid service
        print("\nInitializing hybrid breadth service...")
        breadth_service = HybridMarketBreadthService(
            fyers_client=fyers_client,
            access_token=access_token,
            client_id=client_id,
            use_quick_basket=True,
            enable_websocket=True
        )

        # Initialize
        if not breadth_service.initialize():
            print(" Initialization failed")
            return False

        print(" Hybrid service initialized successfully")

        # Test for 30 seconds
        print(f"\nMonitoring market breadth for 30 seconds...")
        print("(Press Ctrl+C to stop early)\n")

        start_time = time.time()
        update_count = 0

        try:
            while time.time() - start_time < 30:
                # Get breadth summary
                summary = breadth_service.get_breadth_summary()

                if summary.get('available'):
                    update_count += 1

                    source = "WS" if summary.get('websocket_active') else "REST"

                    print(f"[{update_count:3d}] [{source:4s}] "
                          f"Breadth: {summary['classification']:8s} | "
                          f"A/D: {summary['ad_ratio']:5.2f} | "
                          f"Adv: {summary['advances']:2d} ({summary['advance_pct']:4.1f}%) | "
                          f"Dec: {summary['declines']:2d} ({summary['decline_pct']:4.1f}%)")
                else:
                    print(f"[{update_count:3d}] ERROR: {summary.get('error')}")

                time.sleep(2)  # Update every 2 seconds

        except KeyboardInterrupt:
            print("\n\n Test interrupted by user")

        # Get final statistics
        print(f"\n" + "=" * 80)
        print(" STATISTICS")
        print("=" * 80)

        stats = breadth_service.get_statistics()
        print(f"WebSocket Enabled: {stats['websocket_enabled']}")
        print(f"Using WebSocket Data: {stats['using_websocket_data']}")

        if 'websocket_stats' in stats:
            ws_stats = stats['websocket_stats']
            print(f"\nWebSocket Statistics:")
            print(f"  Connected: {ws_stats['is_connected']}")
            print(f"  Messages Received: {ws_stats['message_count']}")
            print(f"  Errors: {ws_stats['error_count']}")
            print(f"  Symbols Tracked: {ws_stats['symbols_tracked']}/{ws_stats['total_symbols']}")

        # Stop service
        breadth_service.stop()
        print(f"\n Service stopped cleanly")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("\nWARNING: This test requires:")
    print("1. Valid Fyers API credentials in .env")
    print("2. Market hours (9:15 AM - 3:30 PM IST)")
    print("3. Active internet connection")

    input("\nPress Enter to start test...")

    success = test_hybrid_breadth_service()

    if success:
        print("\n TEST PASSED")
    else:
        print("\n TEST FAILED")