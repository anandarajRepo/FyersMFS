# services/fyers_breadth_websocket.py

"""
Real-time market breadth tracking using Fyers WebSocket
"""

import logging
import asyncio
import threading
from typing import Dict, Optional, Callable
from datetime import datetime
from fyers_apiv3.FyersWebsocket import data_ws
from config.breadth_basket import get_quick_breadth_symbols, get_breadth_symbols
from config.mmfs_config import MarketBreadth

logger = logging.getLogger(__name__)


class FyersWebSocketBreadthTracker:
    """Track market breadth in real-time using WebSocket"""

    def __init__(self, access_token: str, client_id: str, use_quick_basket: bool = True):
        """
        Initialize WebSocket breadth tracker

        Args:
            access_token: Fyers access token
            client_id: Fyers client ID
            use_quick_basket: Use 15-stock basket (True) or 30-stock basket (False)
        """
        self.access_token = f"{client_id}:{access_token}"
        self.use_quick_basket = use_quick_basket

        # Get appropriate symbol basket
        if use_quick_basket:
            self.symbols = get_quick_breadth_symbols()
            logger.info(f"WebSocket tracker using quick basket: {len(self.symbols)} stocks")
        else:
            self.symbols = get_breadth_symbols()
            logger.info(f"WebSocket tracker using full basket: {len(self.symbols)} stocks")

        # Track current prices and previous closes
        self.current_prices: Dict[str, float] = {}
        self.previous_closes: Dict[str, float] = {}

        # Breadth metrics
        self.advances = 0
        self.declines = 0
        self.unchanged = 0
        self.last_update = None

        # WebSocket instance
        self.ws = None
        self.is_running = False
        self.is_connected = False

        # Thread for WebSocket
        self.ws_thread = None

        # Callbacks
        self.on_breadth_update_callback: Optional[Callable] = None

        # Statistics
        self.message_count = 0
        self.error_count = 0

    def set_previous_closes(self, closes: Dict[str, float]):
        """
        Set previous close prices for all symbols

        Args:
            closes: Dict mapping symbol to previous close price
        """
        self.previous_closes = closes
        logger.info(f"Set previous closes for {len(closes)} symbols")

    def on_message(self, message):
        """Handle WebSocket messages"""
        try:
            self.message_count += 1

            if isinstance(message, dict):
                symbol = message.get('symbol')
                ltp = message.get('ltp')

                if not ltp:
                    # Try alternative field names
                    ltp = message.get('last_price') or message.get('v', {}).get('lp')

                if symbol and ltp:
                    # Update current price
                    self.current_prices[symbol] = ltp

                    # Recalculate breadth
                    self._recalculate_breadth()

                    # Call callback if registered
                    if self.on_breadth_update_callback:
                        try:
                            self.on_breadth_update_callback(self.get_breadth_data())
                        except Exception as e:
                            logger.error(f"Error in breadth update callback: {e}")

                    # Log periodically
                    if self.message_count % 100 == 0:
                        logger.debug(f"Processed {self.message_count} messages. "
                                     f"Current breadth: Adv={self.advances}, Dec={self.declines}")

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing WebSocket message: {e}")

    def on_error(self, error):
        """Handle WebSocket errors"""
        self.error_count += 1
        logger.error(f"WebSocket error: {error}")

    def on_close(self):
        """Handle WebSocket close"""
        logger.info("WebSocket connection closed")
        self.is_running = False
        self.is_connected = False

    def on_connect(self):
        """Handle WebSocket connection"""
        logger.info(" WebSocket breadth tracker connected successfully")
        self.is_connected = True

    def _recalculate_breadth(self):
        """Recalculate advance/decline based on current prices"""
        if not self.previous_closes:
            logger.debug("No previous closes available yet")
            return

        advances = 0
        declines = 0
        unchanged = 0

        for symbol in self.symbols:
            if symbol not in self.current_prices or symbol not in self.previous_closes:
                continue

            current = self.current_prices[symbol]
            prev_close = self.previous_closes[symbol]

            if prev_close == 0:
                continue

            change_pct = ((current - prev_close) / prev_close) * 100

            # Classify with 0.1% threshold
            if change_pct > 0.1:
                advances += 1
            elif change_pct < -0.1:
                declines += 1
            else:
                unchanged += 1

        # Update breadth metrics
        self.advances = advances
        self.declines = declines
        self.unchanged = unchanged
        self.last_update = datetime.now()

    def start(self):
        """Start WebSocket breadth tracking in background thread"""
        try:
            if self.is_running:
                logger.warning("WebSocket tracker already running")
                return

            logger.info(" Starting WebSocket breadth tracker...")

            # Initialize WebSocket
            self.ws = data_ws.FyersDataSocket(
                access_token=self.access_token,
                log_path="",
                litemode=False,
                write_to_file=False,
                reconnect=True,
                on_connect=self.on_connect,
                on_close=self.on_close,
                on_error=self.on_error,
                on_message=self.on_message
            )

            # Subscribe to symbols
            logger.info(f"Subscribing to {len(self.symbols)} symbols...")
            self.ws.subscribe(symbols=self.symbols, data_type="SymbolUpdate")

            self.is_running = True

            # Start WebSocket in background thread
            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()

            logger.info(" WebSocket breadth tracker started in background")

        except Exception as e:
            logger.error(f" Error starting WebSocket tracker: {e}")
            self.is_running = False

    def _run_websocket(self):
        """Run WebSocket in thread"""
        try:
            self.ws.keep_running()
        except Exception as e:
            logger.error(f"WebSocket thread error: {e}")
            self.is_running = False

    def get_breadth_data(self) -> Dict:
        """Get current breadth data"""
        total = self.advances + self.declines + self.unchanged
        ad_ratio = self.advances / max(self.declines, 1) if self.declines > 0 else 1.0

        return {
            'advances': self.advances,
            'declines': self.declines,
            'unchanged': self.unchanged,
            'total': total,
            'ad_ratio': ad_ratio,
            'timestamp': self.last_update,
            'source': 'websocket',
            'is_connected': self.is_connected,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'symbols_tracked': len(self.current_prices)
        }

    def get_market_breadth(self, threshold: float = 1.5) -> MarketBreadth:
        """Get market breadth classification"""
        ad_ratio = self.advances / max(self.declines, 1) if self.declines > 0 else 1.0

        if ad_ratio >= threshold:
            return MarketBreadth.BULLISH
        elif ad_ratio <= (1 / threshold):
            return MarketBreadth.BEARISH
        else:
            return MarketBreadth.NEUTRAL

    def get_breadth_strength_score(self) -> float:
        """Calculate strength score (0-100)"""
        ad_ratio = self.advances / max(self.declines, 1) if self.declines > 0 else 1.0

        if ad_ratio >= 1.0:
            score = 50 + min((ad_ratio - 1.0) / 2.0, 1.0) * 50
        else:
            score = (ad_ratio - 0.33) / 0.67 * 50

        return max(0, min(100, score))

    def register_callback(self, callback: Callable):
        """Register callback for breadth updates"""
        self.on_breadth_update_callback = callback
        logger.info("Breadth update callback registered")

    def stop(self):
        """Stop WebSocket tracker"""
        logger.info("Stopping WebSocket breadth tracker...")
        self.is_running = False

        if self.ws:
            try:
                self.ws.close()
            except:
                pass

        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2)

        logger.info("WebSocket breadth tracker stopped")

    def get_statistics(self) -> Dict:
        """Get tracker statistics"""
        return {
            'is_running': self.is_running,
            'is_connected': self.is_connected,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'symbols_tracked': len(self.current_prices),
            'total_symbols': len(self.symbols),
            'last_update': self.last_update,
            'current_breadth': {
                'advances': self.advances,
                'declines': self.declines,
                'unchanged': self.unchanged
            }
        }


if __name__ == "__main__":
    print("Fyers WebSocket Breadth Tracker Test")
    print("=" * 60)
    print("\nThis test requires:")
    print("1. Valid Fyers access token")
    print("2. Market hours for real data")
    print("3. Active network connection")