# services/market_breadth_service.py

"""
Market Breadth Service for MMFS Strategy
Fetches advance/decline data and calculates market breadth indicators
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from enum import Enum

from config.mmfs_config import MarketBreadth

logger = logging.getLogger(__name__)


class MarketBreadthService:
    """Service to fetch and analyze market breadth data"""

    def __init__(self):
        # NSE API endpoints
        self.nse_base_url = "https://www.nseindia.com"
        self.market_status_url = f"{self.nse_base_url}/api/marketStatus"
        self.advance_decline_url = f"{self.nse_base_url}/api/market-data-pre-open"

        # Headers for NSE API
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        # Cache for breadth data
        self.last_breadth_data = None
        self.last_update_time = None
        self.cache_duration_seconds = 60  # Cache for 1 minute

    def get_session(self) -> requests.Session:
        """Create a session with proper headers for NSE"""
        session = requests.Session()
        session.headers.update(self.headers)

        # Get cookies by visiting the main page first
        try:
            session.get(self.nse_base_url, timeout=10)
        except:
            pass

        return session

    def fetch_advance_decline_data(self) -> Optional[Dict]:
        """
        Fetch current advance/decline data from NSE

        Returns:
            Dict with advance, decline, unchanged counts or None if failed
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Using cached breadth data")
                return self.last_breadth_data

            session = self.get_session()

            # Try fetching from NSE market data API
            response = session.get(self.advance_decline_url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                breadth_data = self._parse_nse_breadth_data(data)

                if breadth_data:
                    self.last_breadth_data = breadth_data
                    self.last_update_time = datetime.now()

                    logger.info(f"Market Breadth Updated: Adv={breadth_data['advances']}, "
                                f"Dec={breadth_data['declines']}, Unch={breadth_data['unchanged']}")

                    return breadth_data

            logger.warning(f"Failed to fetch breadth data: Status {response.status_code}")
            return self._get_fallback_breadth_data()

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching breadth data: {e}")
            return self._get_fallback_breadth_data()
        except Exception as e:
            logger.error(f"Error fetching advance/decline data: {e}")
            return self._get_fallback_breadth_data()

    def _parse_nse_breadth_data(self, data: dict) -> Optional[Dict]:
        """Parse NSE API response to extract advance/decline counts"""
        try:
            # NSE pre-open data structure varies, try different paths
            if 'data' in data:
                market_data = data['data']

                # Count advances, declines, unchanged
                advances = 0
                declines = 0
                unchanged = 0

                if isinstance(market_data, list):
                    for item in market_data:
                        if 'change' in item or 'pChange' in item:
                            change = item.get('pChange', item.get('change', 0))

                            if change > 0:
                                advances += 1
                            elif change < 0:
                                declines += 1
                            else:
                                unchanged += 1

                if advances > 0 or declines > 0:
                    return {
                        'advances': advances,
                        'declines': declines,
                        'unchanged': unchanged,
                        'total': advances + declines + unchanged,
                        'timestamp': datetime.now()
                    }

            return None

        except Exception as e:
            logger.error(f"Error parsing NSE breadth data: {e}")
            return None

    def _is_cache_valid(self) -> bool:
        """Check if cached breadth data is still valid"""
        if not self.last_breadth_data or not self.last_update_time:
            return False

        elapsed = (datetime.now() - self.last_update_time).total_seconds()
        return elapsed < self.cache_duration_seconds

    def _get_fallback_breadth_data(self) -> Optional[Dict]:
        """
        Get fallback breadth data using alternative method
        Can be enhanced to use broker API or other data sources
        """
        # Return cached data if available
        if self.last_breadth_data:
            logger.info("Using last known breadth data as fallback")
            return self.last_breadth_data

        # Return neutral/unknown data
        logger.warning("No breadth data available, returning neutral")
        return {
            'advances': 100,  # Neutral assumption
            'declines': 100,
            'unchanged': 50,
            'total': 250,
            'timestamp': datetime.now(),
            'is_fallback': True
        }

    def calculate_breadth_ratio(self, breadth_data: Optional[Dict] = None) -> Tuple[float, str]:
        """
        Calculate advance/decline ratio and classify market breadth

        Returns:
            Tuple of (ratio, classification_str)
        """
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

        # Calculate advance/decline ratio
        ad_ratio = advances / declines

        # Classify market breadth
        if ad_ratio >= 1.5:
            classification = "BULLISH"
        elif ad_ratio <= (1 / 1.5):
            classification = "BEARISH"
        else:
            classification = "NEUTRAL"

        logger.debug(f"Breadth Ratio: {ad_ratio:.2f} ({classification})")

        return ad_ratio, classification

    def get_market_breadth(self, breadth_ratio_threshold: float = 1.5) -> MarketBreadth:
        """
        Get market breadth classification using configured threshold

        Args:
            breadth_ratio_threshold: Ratio threshold for bullish/bearish

        Returns:
            MarketBreadth enum value
        """
        ad_ratio, _ = self.calculate_breadth_ratio()

        if ad_ratio >= breadth_ratio_threshold:
            return MarketBreadth.BULLISH
        elif ad_ratio <= (1 / breadth_ratio_threshold):
            return MarketBreadth.BEARISH
        else:
            return MarketBreadth.NEUTRAL

    def is_breadth_bullish(self, min_ratio: float = 1.5) -> bool:
        """Check if market breadth is bullish"""
        ad_ratio, _ = self.calculate_breadth_ratio()
        return ad_ratio >= min_ratio

    def is_breadth_bearish(self, min_ratio: float = 1.5) -> bool:
        """Check if market breadth is bearish"""
        ad_ratio, _ = self.calculate_breadth_ratio()
        return ad_ratio <= (1 / min_ratio)

    def is_breadth_neutral(self, ratio_range: float = 1.5) -> bool:
        """Check if market breadth is neutral"""
        ad_ratio, _ = self.calculate_breadth_ratio()
        return (1 / ratio_range) < ad_ratio < ratio_range

    def get_breadth_summary(self) -> Dict:
        """Get comprehensive breadth summary"""
        try:
            data = self.fetch_advance_decline_data()
            if not data:
                return {'available': False, 'error': 'No breadth data'}

            total = data['total']

            # Calculate ad_ratio if not present in data
            if 'ad_ratio' in data:
                ad_ratio = data['ad_ratio']
            else:
                # Calculate it from advances/declines
                advances = data['advances']
                declines = data['declines']
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

    def validate_breadth_for_setup(self, setup_type: str, required_breadth: MarketBreadth) -> bool:
        """
        Validate if current market breadth matches setup requirements

        Args:
            setup_type: Setup identifier (setup1, setup2, etc.)
            required_breadth: Required breadth classification

        Returns:
            True if breadth matches requirement
        """
        try:
            current_breadth = self.get_market_breadth()

            matches = current_breadth == required_breadth

            logger.debug(f"Breadth validation for {setup_type}: "
                         f"Required={required_breadth.value}, Current={current_breadth.value}, Match={matches}")

            return matches

        except Exception as e:
            logger.error(f"Error validating breadth for setup: {e}")
            return False

    def get_breadth_strength_score(self) -> float:
        """
        Calculate a strength score (0-100) based on advance/decline ratio

        Returns:
            Score from 0 (very bearish) to 100 (very bullish)
        """
        try:
            ad_ratio, _ = self.calculate_breadth_ratio()

            # Normalize ratio to 0-100 scale
            # Ratio of 3.0 = 100 (very bullish)
            # Ratio of 0.33 = 0 (very bearish)
            # Ratio of 1.0 = 50 (neutral)

            if ad_ratio >= 1.0:
                # Bullish side: map 1.0-3.0 to 50-100
                score = 50 + min((ad_ratio - 1.0) / 2.0, 1.0) * 50
            else:
                # Bearish side: map 0.33-1.0 to 0-50
                score = (ad_ratio - 0.33) / 0.67 * 50

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error calculating breadth strength score: {e}")
            return 50  # Neutral on error


# Simulated market breadth for testing/development
class SimulatedMarketBreadthService(MarketBreadthService):
    """Simulated market breadth service for testing"""

    def __init__(self, simulated_advances: int = 120, simulated_declines: int = 80):
        super().__init__()
        self.simulated_advances = simulated_advances
        self.simulated_declines = simulated_declines

    def fetch_advance_decline_data(self) -> Optional[Dict]:
        """Return simulated breadth data"""
        logger.info(f"Using simulated market breadth: Adv={self.simulated_advances}, Dec={self.simulated_declines}")

        return {
            'advances': self.simulated_advances,
            'declines': self.simulated_declines,
            'unchanged': 50,
            'total': self.simulated_advances + self.simulated_declines + 50,
            'timestamp': datetime.now(),
            'is_simulated': True
        }

    def set_simulated_breadth(self, advances: int, declines: int):
        """Update simulated breadth values"""
        self.simulated_advances = advances
        self.simulated_declines = declines
        self.last_breadth_data = None  # Clear cache


if __name__ == "__main__":
    print("Market Breadth Service Test")
    print("=" * 60)

    # Test with simulated data
    print("\n1. Testing with Simulated Data:")

    # Bullish scenario
    bullish_service = SimulatedMarketBreadthService(simulated_advances=180, simulated_declines=80)
    summary = bullish_service.get_breadth_summary()
    print(f"\nBullish Scenario:")
    print(f"  Advances: {summary['advances']} ({summary['advance_pct']}%)")
    print(f"  Declines: {summary['declines']} ({summary['decline_pct']}%)")
    print(f"  A/D Ratio: {summary['ad_ratio']}")
    print(f"  Classification: {summary['classification']}")
    print(f"  Strength Score: {bullish_service.get_breadth_strength_score():.1f}/100")

    # Bearish scenario
    bearish_service = SimulatedMarketBreadthService(simulated_advances=70, simulated_declines=170)
    summary = bearish_service.get_breadth_summary()
    print(f"\nBearish Scenario:")
    print(f"  Advances: {summary['advances']} ({summary['advance_pct']}%)")
    print(f"  Declines: {summary['declines']} ({summary['decline_pct']}%)")
    print(f"  A/D Ratio: {summary['ad_ratio']}")
    print(f"  Classification: {summary['classification']}")
    print(f"  Strength Score: {bearish_service.get_breadth_strength_score():.1f}/100")

    # Neutral scenario
    neutral_service = SimulatedMarketBreadthService(simulated_advances=125, simulated_declines=125)
    summary = neutral_service.get_breadth_summary()
    print(f"\nNeutral Scenario:")
    print(f"  Advances: {summary['advances']} ({summary['advance_pct']}%)")
    print(f"  Declines: {summary['declines']} ({summary['decline_pct']}%)")
    print(f"  A/D Ratio: {summary['ad_ratio']}")
    print(f"  Classification: {summary['classification']}")
    print(f"  Strength Score: {neutral_service.get_breadth_strength_score():.1f}/100")

    # Test real NSE data (may fail if network issues)
    print(f"\n2. Testing with Real NSE Data:")
    try:
        real_service = MarketBreadthService()
        summary = real_service.get_breadth_summary()

        if summary['available']:
            print(f"   Successfully fetched real market breadth")
            print(f"  Advances: {summary['advances']}")
            print(f"  Declines: {summary['declines']}")
            print(f"  A/D Ratio: {summary['ad_ratio']}")
            print(f"  Classification: {summary['classification']}")
            print(f"  Fallback Mode: {summary['is_fallback']}")
        else:
            print(f"   Failed to fetch: {summary.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Error: {e}")