# services/fyers_breadth_service.py

"""
Fyers API-based Market Breadth Service
Calculates advance/decline using actual stock quotes from Fyers
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from config.mmfs_config import MarketBreadth
from config.breadth_basket import get_breadth_symbols, get_quick_breadth_symbols

logger = logging.getLogger(__name__)


class FyersMarketBreadthService:
    """Calculate market breadth using Fyers API stock quotes"""

    def __init__(self, fyers_client, use_quick_basket: bool = False):
        """
        Initialize Fyers-based breadth service

        Args:
            fyers_client: Authenticated Fyers API client
            use_quick_basket: Use smaller 15-stock basket for faster calculation
        """
        self.fyers = fyers_client
        self.use_quick_basket = use_quick_basket

        # Get appropriate symbol basket
        if use_quick_basket:
            self.symbols = get_quick_breadth_symbols()
            logger.info(f"Using quick basket: {len(self.symbols)} stocks")
        else:
            self.symbols = get_breadth_symbols()
            logger.info(f"Using full basket: {len(self.symbols)} stocks")

        # Cache for breadth data
        self.last_breadth_data = None
        self.last_update_time = None
        self.cache_duration_seconds = 60  # Cache for 1 minute

        # Track previous close prices
        self.previous_closes: Dict[str, float] = {}

    def fetch_advance_decline_data(self) -> Optional[Dict]:
        """
        Fetch current advance/decline data using Fyers API

        Returns:
            Dict with advance, decline, unchanged counts
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Using cached breadth data")
                return self.last_breadth_data

            # Fetch quotes for all symbols in basket
            quotes_data = self._fetch_basket_quotes()

            if not quotes_data:
                logger.warning("Failed to fetch basket quotes")
                return self._get_fallback_breadth_data()

            # Calculate advances/declines
            breadth_data = self._calculate_breadth_from_quotes(quotes_data)

            if breadth_data:
                self.last_breadth_data = breadth_data
                self.last_update_time = datetime.now()

                logger.info(f" Market Breadth: Adv={breadth_data['advances']}, "
                            f"Dec={breadth_data['declines']}, Unch={breadth_data['unchanged']}")

                return breadth_data

            return self._get_fallback_breadth_data()

        except Exception as e:
            logger.error(f"Error fetching breadth data: {e}")
            return self._get_fallback_breadth_data()

    def _fetch_basket_quotes(self) -> Optional[Dict[str, Dict]]:
        """Fetch quotes for all symbols in basket"""
        try:
            # Fyers API supports fetching multiple symbols at once
            # Format: "symbol1,symbol2,symbol3"
            symbols_str = ",".join(self.symbols)

            data = {"symbols": symbols_str}
            response = self.fyers.quotes(data=data)

            if response.get('s') != 'ok':
                logger.error(f"Quotes API error: {response.get('message', 'Unknown error')}")
                return None

            quotes_list = response.get('d', [])
            if not quotes_list:
                logger.warning("No quotes data returned")
                return None

            # Parse quotes into dict
            quotes_dict = {}
            for quote in quotes_list:
                symbol = quote.get('n')
                quote_data = quote.get('v', {})

                if symbol and quote_data:
                    quotes_dict[symbol] = {
                        'ltp': quote_data.get('lp', 0),  # Last traded price
                        'prev_close': quote_data.get('prev_close_price', 0),
                        'change': quote_data.get('ch', 0),
                        'change_pct': quote_data.get('chp', 0)
                    }

            logger.debug(f"Fetched quotes for {len(quotes_dict)} symbols")
            return quotes_dict

        except Exception as e:
            logger.error(f"Error fetching basket quotes: {e}")
            return None

    def _calculate_breadth_from_quotes(self, quotes_data: Dict[str, Dict]) -> Optional[Dict]:
        """Calculate advance/decline from quote data"""
        try:
            advances = 0
            declines = 0
            unchanged = 0

            for symbol, quote in quotes_data.items():
                change_pct = quote.get('change_pct', 0)

                # Classify as advance/decline/unchanged
                if change_pct > 0.1:  # More than 0.1% up
                    advances += 1
                elif change_pct < -0.1:  # More than 0.1% down
                    declines += 1
                else:  # Within 0.1% range
                    unchanged += 1

            total = advances + declines + unchanged

            if total == 0:
                return None

            return {
                'advances': advances,
                'declines': declines,
                'unchanged': unchanged,
                'total': total,
                'timestamp': datetime.now(),
                'source': 'fyers_api',
                'basket_size': len(self.symbols)
            }

        except Exception as e:
            logger.error(f"Error calculating breadth: {e}")
            return None

    def calculate_breadth_ratio(self, breadth_data: Optional[Dict] = None) -> Tuple[float, str]:
        """Calculate advance/decline ratio and classify"""
        if not breadth_data:
            breadth_data = self.fetch_advance_decline_data()

        if not breadth_data:
            return 1.0, "UNKNOWN"

        advances = breadth_data['advances']
        declines = breadth_data['declines']

        # Avoid division by zero
        if declines == 0:
            declines = 1
        if advances == 0:
            advances = 1

        ad_ratio = advances / declines

        # Classify
        if ad_ratio >= 1.5:
            classification = "BULLISH"
        elif ad_ratio <= (1 / 1.5):
            classification = "BEARISH"
        else:
            classification = "NEUTRAL"

        logger.debug(f"Breadth Ratio: {ad_ratio:.2f} ({classification})")
        return ad_ratio, classification

    def get_market_breadth(self, breadth_ratio_threshold: float = 1.5) -> MarketBreadth:
        """Get market breadth classification"""
        ad_ratio, _ = self.calculate_breadth_ratio()

        if ad_ratio >= breadth_ratio_threshold:
            return MarketBreadth.BULLISH
        elif ad_ratio <= (1 / breadth_ratio_threshold):
            return MarketBreadth.BEARISH
        else:
            return MarketBreadth.NEUTRAL

    def get_breadth_summary(self) -> Dict:
        """Get comprehensive market breadth summary"""
        try:
            breadth_data = self.fetch_advance_decline_data()

            if not breadth_data:
                return {'available': False, 'error': 'Failed to fetch breadth data'}

            ad_ratio, classification = self.calculate_breadth_ratio(breadth_data)

            total = breadth_data['total']
            adv_pct = (breadth_data['advances'] / total * 100) if total > 0 else 0
            dec_pct = (breadth_data['declines'] / total * 100) if total > 0 else 0
            unch_pct = (breadth_data['unchanged'] / total * 100) if total > 0 else 0

            return {
                'available': True,
                'advances': breadth_data['advances'],
                'declines': breadth_data['declines'],
                'unchanged': breadth_data['unchanged'],
                'total': total,
                'advance_pct': round(adv_pct, 1),
                'decline_pct': round(dec_pct, 1),
                'unchanged_pct': round(unch_pct, 1),
                'ad_ratio': round(ad_ratio, 2),
                'classification': classification,
                'is_bullish': ad_ratio >= 1.5,
                'is_bearish': ad_ratio <= (1 / 1.5),
                'is_neutral': (1 / 1.5) < ad_ratio < 1.5,
                'timestamp': breadth_data['timestamp'].isoformat(),
                'source': 'fyers_api',
                'basket_size': breadth_data.get('basket_size', len(self.symbols))
            }

        except Exception as e:
            logger.error(f"Error generating breadth summary: {e}")
            return {'available': False, 'error': str(e)}

    def is_breadth_bullish(self, min_ratio: float = 1.5) -> bool:
        """Check if market breadth is bullish"""
        ad_ratio, _ = self.calculate_breadth_ratio()
        return ad_ratio >= min_ratio

    def is_breadth_bearish(self, min_ratio: float = 1.5) -> bool:
        """Check if market breadth is bearish"""
        ad_ratio, _ = self.calculate_breadth_ratio()
        return ad_ratio <= (1 / min_ratio)

    def get_breadth_strength_score(self) -> float:
        """Calculate strength score (0-100)"""
        try:
            ad_ratio, _ = self.calculate_breadth_ratio()

            if ad_ratio >= 1.0:
                score = 50 + min((ad_ratio - 1.0) / 2.0, 1.0) * 50
            else:
                score = (ad_ratio - 0.33) / 0.67 * 50

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error calculating strength score: {e}")
            return 50

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.last_breadth_data or not self.last_update_time:
            return False

        elapsed = (datetime.now() - self.last_update_time).total_seconds()
        return elapsed < self.cache_duration_seconds

    def _get_fallback_breadth_data(self) -> Optional[Dict]:
        """Get fallback breadth data"""
        if self.last_breadth_data:
            logger.info("Using last known breadth data as fallback")
            return self.last_breadth_data

        logger.warning("No breadth data available, returning neutral")
        return {
            'advances': len(self.symbols) // 2,
            'declines': len(self.symbols) // 2,
            'unchanged': 0,
            'total': len(self.symbols),
            'timestamp': datetime.now(),
            'is_fallback': True
        }


if __name__ == "__main__":
    print("Fyers Market Breadth Service Test")
    print("=" * 60)
    print("\nThis test requires authenticated Fyers API client")
    print("Run this test during market hours for real data")