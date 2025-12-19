# services/data_service.py

"""
Market Data Service
Handles fetching historical and real-time market data
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


class DataService:
    """Market data service for MMFS strategy"""

    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.cache = {}

        logger.info("DataService initialized")

    async def get_previous_day_data(self, symbol: str) -> Optional[Dict]:
        """
        Get previous day's OHLCV data

        Returns:
            Dict with keys: open, high, low, close, volume, vwap
        """
        try:
            # Get data for last 2 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)  # Get 5 days to ensure we have data

            data = {
                "symbol": symbol,
                "resolution": "D",  # Daily
                "date_format": "1",
                "range_from": start_date.strftime("%Y-%m-%d"),
                "range_to": end_date.strftime("%Y-%m-%d"),
                "cont_flag": "1"
            }

            response = self.fyers.history(data=data)

            if response.get('s') == 'ok':
                candles = response.get('candles', [])

                if len(candles) >= 2:
                    # Get second last candle (previous complete day)
                    prev_candle = candles[-2]

                    result = {
                        'date': datetime.fromtimestamp(prev_candle[0]),
                        'open': prev_candle[1],
                        'high': prev_candle[2],
                        'low': prev_candle[3],
                        'close': prev_candle[4],
                        'volume': prev_candle[5],
                        'vwap': (prev_candle[2] + prev_candle[3] + prev_candle[4]) / 3  # Approximation
                    }

                    logger.info(f" Previous day data for {symbol}: Close={result['close']}")
                    return result
                else:
                    logger.warning(f"Insufficient historical data for {symbol}")
                    return None
            else:
                logger.error(f"Failed to fetch historical data: {response}")
                return None

        except Exception as e:
            logger.error(f"Error fetching previous day data for {symbol}: {e}")
            return None

    async def get_current_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get current quote for symbol

        Returns:
            Dict with current price, bid, ask, volume, etc.
        """
        try:
            data = {"symbols": symbol}
            response = self.fyers.quotes(data=data)

            if response.get('s') == 'ok':
                quotes = response.get('d', [])
                if quotes:
                    quote = quotes[0]

                    result = {
                        'symbol': quote.get('n'),
                        'last_price': quote.get('v', {}).get('lp'),
                        'open': quote.get('v', {}).get('open_price'),
                        'high': quote.get('v', {}).get('high_price'),
                        'low': quote.get('v', {}).get('low_price'),
                        'close': quote.get('v', {}).get('prev_close_price'),
                        'volume': quote.get('v', {}).get('volume'),
                        'change': quote.get('v', {}).get('ch'),
                        'change_pct': quote.get('v', {}).get('chp'),
                        'timestamp': datetime.now()
                    }

                    return result

            logger.error(f"Failed to fetch quote: {response}")
            return None

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    async def get_intraday_data(self, symbol: str, interval: str = "1") -> Optional[pd.DataFrame]:
        """
        Get intraday data

        Args:
            symbol: Trading symbol
            interval: Time interval (1, 5, 15, etc. in minutes)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Get data from market open
            today = datetime.now()
            start_time = today.replace(hour=9, minute=0, second=0, microsecond=0)

            data = {
                "symbol": symbol,
                "resolution": interval,
                "date_format": "1",
                "range_from": start_time.strftime("%Y-%m-%d"),
                "range_to": today.strftime("%Y-%m-%d"),
                "cont_flag": "1"
            }

            response = self.fyers.history(data=data)

            if response.get('s') == 'ok':
                candles = response.get('candles', [])

                if candles:
                    df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                    df.set_index('timestamp', inplace=True)

                    return df

            logger.warning(f"No intraday data available for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return None

    async def get_first_candle(self, symbol: str) -> Optional[Dict]:
        """
        Get first 1-minute candle (9:15-9:16)

        Returns:
            Dict with OHLC, volume, VWAP
        """
        try:
            # Get 1-minute data
            df = await self.get_intraday_data(symbol, interval="1")

            if df is not None and len(df) > 0:
                # Get first candle after 9:15
                first_candle = df.iloc[0]

                result = {
                    'timestamp': first_candle.name,
                    'open': first_candle['open'],
                    'high': first_candle['high'],
                    'low': first_candle['low'],
                    'close': first_candle['close'],
                    'volume': first_candle['volume'],
                    'vwap': (first_candle['high'] + first_candle['low'] + first_candle['close']) / 3
                }

                return result

            return None

        except Exception as e:
            logger.error(f"Error getting first candle for {symbol}: {e}")
            return None

    async def calculate_vwap(self, symbol: str) -> Optional[float]:
        """Calculate VWAP for current day"""
        try:
            df = await self.get_intraday_data(symbol, interval="1")

            if df is not None and len(df) > 0:
                df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
                df['pv'] = df['typical_price'] * df['volume']

                vwap = df['pv'].sum() / df['volume'].sum()
                return vwap

            return None

        except Exception as e:
            logger.error(f"Error calculating VWAP for {symbol}: {e}")
            return None

    def get_market_depth(self, symbol: str) -> Optional[Dict]:
        """Get market depth (Level 2 data)"""
        try:
            data = {"symbol": symbol, "ohlcv_flag": "1"}
            response = self.fyers.depth(data=data)

            if response.get('s') == 'ok':
                return response.get('d', {})

            return None

        except Exception as e:
            logger.error(f"Error fetching market depth for {symbol}: {e}")
            return None


if __name__ == "__main__":
    import asyncio
    from services.fyers_auth import FyersAuth


    async def test_data_service():
        print("Data Service Test")
        print("=" * 60)

        # Initialize auth
        auth = FyersAuth()
        await auth.initialize()

        if not auth.is_authenticated:
            print("✗ Authentication failed")
            return

        # Create data service
        data_service = DataService(auth.get_client())

        # Test symbol
        symbol = "NSE:NIFTY50-INDEX"

        print(f"\nTesting with {symbol}")
        print("-" * 60)

        # Get previous day data
        print("\n1. Previous Day Data:")
        prev_data = await data_service.get_previous_day_data(symbol)
        if prev_data:
            print(f"  Date: {prev_data['date']}")
            print(f"  Close: {prev_data['close']}")
            print(f"  High: {prev_data['high']}")
            print(f"  Low: {prev_data['low']}")

        # Get current quote
        print("\n2. Current Quote:")
        quote = await data_service.get_current_quote(symbol)
        if quote:
            print(f"  Last Price: {quote['last_price']}")
            print(f"  Change: {quote['change']} ({quote['change_pct']}%)")

        # Get VWAP
        print("\n3. VWAP:")
        vwap = await data_service.calculate_vwap(symbol)
        if vwap:
            print(f"  VWAP: {vwap:.2f}")

        print("\n" + "=" * 60)


    asyncio.run(test_data_service())