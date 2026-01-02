# services/hybrid_breadth_service.py

"""
Hybrid Market Breadth Service
Uses REST API for initialization and WebSocket for real-time updates
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from services.fyers_breadth_service import FyersMarketBreadthService
from services.fyers_breadth_websocket import FyersWebSocketBreadthTracker
from config.mmfs_config import MarketBreadth

logger = logging.getLogger(__name__)


class HybridMarketBreadthService:
    """
    Hybrid breadth service combining REST API and WebSocket
    - Uses REST API for initial data and fallback
    - Uses WebSocket for real-time updates
    """

    def __init__(self, fyers_client, access_token: str, client_id: str,
                 use_quick_basket: bool = True, enable_websocket: bool = True):
        """
        Initialize hybrid breadth service

        Args:
            fyers_client: Fyers API client for REST calls
            access_token: Access token for WebSocket
            client_id: Client ID for WebSocket
            use_quick_basket: Use 15-stock basket (faster)
            enable_websocket: Enable real-time WebSocket updates
        """
        self.fyers_client = fyers_client
        self.enable_websocket = enable_websocket

        # Initialize REST API service
        self.rest_service = FyersMarketBreadthService(
            fyers_client,
            use_quick_basket=use_quick_basket
        )

        # Initialize WebSocket tracker
        self.ws_tracker = None
        if enable_websocket:
            self.ws_tracker = FyersWebSocketBreadthTracker(
                access_token,
                client_id,
                use_quick_basket=use_quick_basket
            )

        self.use_websocket_data = False
        logger.info(f"Hybrid breadth service initialized (WebSocket: {'enabled' if enable_websocket else 'disabled'})")

    def initialize(self) -> bool:
        """
        Initialize the service
        - Fetch initial data via REST
        - Set previous closes for WebSocket
        - Start WebSocket tracker
        """
        try:
            logger.info("Initializing hybrid breadth service...")

            # Step 1: Fetch initial breadth data via REST
            initial_data = self.rest_service.fetch_advance_decline_data()
            if not initial_data:
                logger.error("Failed to fetch initial breadth data")
                return False

            logger.info(f" Initial breadth: Adv={initial_data['advances']}, Dec={initial_data['declines']}")

            # Step 2: Get previous closes for WebSocket
            if self.enable_websocket and self.ws_tracker:
                logger.info("Setting up WebSocket tracker...")

                # Fetch quotes to get previous close prices
                quotes = self.rest_service._fetch_basket_quotes()
                if quotes:
                    prev_closes = {
                        symbol: data.get('prev_close', 0)
                        for symbol, data in quotes.items()
                    }

                    self.ws_tracker.set_previous_closes(prev_closes)
                    logger.info(f"Set previous closes for {len(prev_closes)} symbols")

                    # Start WebSocket
                    self.ws_tracker.start()

                    # Wait a moment for connection
                    import time
                    time.sleep(2)

                    if self.ws_tracker.is_connected:
                        logger.info(" WebSocket tracker connected and running")
                        self.use_websocket_data = True
                    else:
                        logger.warning(" WebSocket connection delayed, using REST fallback")
                else:
                    logger.warning("Could not fetch quotes for WebSocket initialization")

            return True

        except Exception as e:
            logger.error(f"Error initializing hybrid breadth service: {e}")
            return False

    def fetch_advance_decline_data(self) -> Optional[Dict]:
        """
        Fetch advance/decline data
        Uses WebSocket data if available, otherwise REST API
        """
        try:
            # Try WebSocket first if enabled and connected
            if self.use_websocket_data and self.ws_tracker and self.ws_tracker.is_connected:
                ws_data = self.ws_tracker.get_breadth_data()

                # Only use WebSocket data if we have recent updates
                if ws_data.get('last_update'):
                    elapsed = (datetime.now() - ws_data['last_update']).total_seconds()

                    if elapsed < 60:  # Data less than 1 minute old
                        logger.debug("Using WebSocket breadth data (real-time)")
                        return ws_data
                    else:
                        logger.debug(f"WebSocket data stale ({elapsed:.0f}s old), falling back to REST")

            # Fallback to REST API
            logger.debug("Using REST API breadth data")
            return self.rest_service.fetch_advance_decline_data()

        except Exception as e:
            logger.error(f"Error fetching breadth data: {e}")
            return None

    def get_market_breadth(self, threshold: float = 1.5) -> MarketBreadth:
        """Get market breadth classification"""
        if self.use_websocket_data and self.ws_tracker and self.ws_tracker.is_connected:
            return self.ws_tracker.get_market_breadth(threshold)
        else:
            return self.rest_service.get_market_breadth(threshold)

    def get_breadth_summary(self) -> Dict:
        """Get comprehensive breadth summary"""
        try:
            data = self.fetch_advance_decline_data()
            if not data:
                return {'available': False, 'error': 'No breadth data'}

            total = data['total']
            # Calculate ad_ratio if not present (REST API doesn't include it)
            if 'ad_ratio' in data:
                ad_ratio = data['ad_ratio']
            else:
                declines = data['declines']
                advances = data['advances']
                ad_ratio = advances / max(declines, 1) if declines > 0 else 1.0

            # Classify
            if ad_ratio >= 1.5:
                classification = "BULLISH"
            elif ad_ratio <= (1 / 1.5):
                classification = "BEARISH"
            else:
                classification = "NEUTRAL"

            return {
                'available': True,
                'advances': data['advances'],
                'declines': data['declines'],
                'unchanged': data['unchanged'],
                'total': total,
                'advance_pct': round((data['advances'] / total * 100) if total > 0 else 0, 1),
                'decline_pct': round((data['declines'] / total * 100) if total > 0 else 0, 1),
                'unchanged_pct': round((data['unchanged'] / total * 100) if total > 0 else 0, 1),
                'ad_ratio': round(ad_ratio, 2),
                'classification': classification,
                'is_bullish': ad_ratio >= 1.5,
                'is_bearish': ad_ratio <= (1 / 1.5),
                'is_neutral': (1 / 1.5) < ad_ratio < 1.5,
                'timestamp': data['timestamp'].isoformat() if data.get('timestamp') else None,
                'source': data.get('source', 'unknown'),
                'websocket_active': self.use_websocket_data and self.ws_tracker.is_connected if self.ws_tracker else False
            }

        except Exception as e:
            logger.error(f"Error generating breadth summary: {e}")
            return {'available': False, 'error': str(e)}

    def get_breadth_strength_score(self) -> float:
        """Get breadth strength score (0-100)"""
        if self.use_websocket_data and self.ws_tracker and self.ws_tracker.is_connected:
            return self.ws_tracker.get_breadth_strength_score()
        else:
            return self.rest_service.get_breadth_strength_score()

    def calculate_breadth_ratio(self, breadth_data: Optional[Dict] = None):
        """Calculate breadth ratio"""
        return self.rest_service.calculate_breadth_ratio(breadth_data)

    def stop(self):
        """Stop the service"""
        logger.info("Stopping hybrid breadth service...")
        if self.ws_tracker:
            self.ws_tracker.stop()
        logger.info("Hybrid breadth service stopped")

    def get_statistics(self) -> Dict:
        """Get service statistics"""
        stats = {
            'websocket_enabled': self.enable_websocket,
            'using_websocket_data': self.use_websocket_data
        }

        if self.ws_tracker:
            stats['websocket_stats'] = self.ws_tracker.get_statistics()

        return stats


if __name__ == "__main__":
    print("Hybrid Market Breadth Service")
    print("=" * 60)
    print("\nCombines REST API and WebSocket for optimal performance")
    print("- REST API: Initial data and fallback")
    print("- WebSocket: Real-time updates during trading")