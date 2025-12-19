# services/order_manager.py

"""
Order Management Service
Handles order placement, modification, and tracking
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from config.settings import OrderSide, OrderType, TradingMode, TradingConfig

logger = logging.getLogger(__name__)


class OrderManager:
    """Order management for MMFS strategy"""

    def __init__(self, fyers_client):
        self.fyers = fyers_client
        self.trading_mode = TradingConfig.MODE
        self.orders = {}  # Track placed orders

        logger.info(f"OrderManager initialized in {self.trading_mode.value} mode")

    async def place_order(
            self,
            symbol: str,
            side: OrderSide,
            quantity: int,
            order_type: OrderType = OrderType.MARKET,
            price: float = 0,
            stop_loss: Optional[float] = None,
            target: Optional[float] = None
    ) -> Optional[str]:
        """
        Place an order

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Paper trading simulation
            if self.trading_mode == TradingMode.PAPER:
                order_id = self._simulate_order(symbol, side, quantity, order_type, price)
                logger.info(f"📝 PAPER ORDER: {side.value} {quantity} {symbol} @ {price if price > 0 else 'Market'}")
                return order_id

            # Live trading
            order_data = {
                "symbol": symbol,
                "qty": quantity,
                "type": 2 if order_type == OrderType.MARKET else 1,  # 1=Limit, 2=Market
                "side": 1 if side == OrderSide.BUY else -1,
                "productType": "INTRADAY",
                "limitPrice": 0 if order_type == OrderType.MARKET else price,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False
            }

            response = self.fyers.place_order(data=order_data)

            if response.get('s') == 'ok':
                order_id = response.get('id')
                self.orders[order_id] = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'order_type': order_type,
                    'price': price,
                    'status': 'PLACED',
                    'timestamp': datetime.now()
                }

                logger.info(f"✅ ORDER PLACED: {order_id} - {side.value} {quantity} {symbol}")

                # Place bracket orders if stop_loss or target provided
                if stop_loss:
                    await self.place_stop_loss_order(symbol, quantity, stop_loss, side)

                if target:
                    await self.place_target_order(symbol, quantity, target, side)

                return order_id
            else:
                logger.error(f"❌ Order placement failed: {response}")
                return None

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    async def place_stop_loss_order(
            self,
            symbol: str,
            quantity: int,
            stop_price: float,
            original_side: OrderSide
    ) -> Optional[str]:
        """Place stop loss order"""
        try:
            # Reverse side for exit
            side = OrderSide.SELL if original_side == OrderSide.BUY else OrderSide.BUY

            if self.trading_mode == TradingMode.PAPER:
                order_id = self._simulate_order(symbol, side, quantity, OrderType.STOP_LOSS, stop_price)
                logger.info(f"📝 PAPER SL: {side.value} {quantity} {symbol} @ {stop_price}")
                return order_id

            order_data = {
                "symbol": symbol,
                "qty": quantity,
                "type": 3,  # Stop loss order
                "side": 1 if side == OrderSide.BUY else -1,
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": stop_price,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False
            }

            response = self.fyers.place_order(data=order_data)

            if response.get('s') == 'ok':
                order_id = response.get('id')
                logger.info(f"✅ SL ORDER: {order_id} @ {stop_price}")
                return order_id
            else:
                logger.error(f"❌ SL order failed: {response}")
                return None

        except Exception as e:
            logger.error(f"Error placing stop loss: {e}")
            return None

    async def place_target_order(
            self,
            symbol: str,
            quantity: int,
            target_price: float,
            original_side: OrderSide
    ) -> Optional[str]:
        """Place target order"""
        try:
            # Reverse side for exit
            side = OrderSide.SELL if original_side == OrderSide.BUY else OrderSide.BUY

            if self.trading_mode == TradingMode.PAPER:
                order_id = self._simulate_order(symbol, side, quantity, OrderType.LIMIT, target_price)
                logger.info(f"📝 PAPER TARGET: {side.value} {quantity} {symbol} @ {target_price}")
                return order_id

            order_data = {
                "symbol": symbol,
                "qty": quantity,
                "type": 1,  # Limit order
                "side": 1 if side == OrderSide.BUY else -1,
                "productType": "INTRADAY",
                "limitPrice": target_price,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False
            }

            response = self.fyers.place_order(data=order_data)

            if response.get('s') == 'ok':
                order_id = response.get('id')
                logger.info(f"✅ TARGET ORDER: {order_id} @ {target_price}")
                return order_id
            else:
                logger.error(f"❌ Target order failed: {response}")
                return None

        except Exception as e:
            logger.error(f"Error placing target: {e}")
            return None

    async def modify_order(self, order_id: str, new_price: float = None, new_quantity: int = None) -> bool:
        """Modify existing order"""
        try:
            if self.trading_mode == TradingMode.PAPER:
                logger.info(f"📝 PAPER MODIFY: Order {order_id}")
                return True

            modify_data = {
                "id": order_id,
                "type": 1  # Limit order
            }

            if new_price:
                modify_data["limitPrice"] = new_price
            if new_quantity:
                modify_data["qty"] = new_quantity

            response = self.fyers.modify_order(data=modify_data)

            if response.get('s') == 'ok':
                logger.info(f"✅ ORDER MODIFIED: {order_id}")
                return True
            else:
                logger.error(f"❌ Modify failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return False

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order"""
        try:
            if self.trading_mode == TradingMode.PAPER:
                logger.info(f"📝 PAPER CANCEL: Order {order_id}")
                if order_id in self.orders:
                    self.orders[order_id]['status'] = 'CANCELLED'
                return True

            cancel_data = {"id": order_id}
            response = self.fyers.cancel_order(data=cancel_data)

            if response.get('s') == 'ok':
                logger.info(f"✅ ORDER CANCELLED: {order_id}")
                if order_id in self.orders:
                    self.orders[order_id]['status'] = 'CANCELLED'
                return True
            else:
                logger.error(f"❌ Cancel failed: {response}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status"""
        try:
            if self.trading_mode == TradingMode.PAPER:
                return self.orders.get(order_id)

            # Get order book
            response = self.fyers.orderbook()

            if response.get('s') == 'ok':
                orders = response.get('orderBook', [])
                for order in orders:
                    if order.get('id') == order_id:
                        return order

            return None

        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None

    def get_positions(self) -> list:
        """Get current positions"""
        try:
            if self.trading_mode == TradingMode.PAPER:
                return []

            response = self.fyers.positions()

            if response.get('s') == 'ok':
                return response.get('netPositions', [])

            return []

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def _simulate_order(self, symbol: str, side: OrderSide, quantity: int,
                        order_type: OrderType, price: float) -> str:
        """Simulate order for paper trading"""
        order_id = f"PAPER_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self.orders[order_id] = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'order_type': order_type,
            'price': price,
            'status': 'FILLED',  # Assume instant fill for paper trading
            'timestamp': datetime.now()
        }

        return order_id


if __name__ == "__main__":
    import asyncio
    from services.fyers_auth import FyersAuth
    from config.settings import OrderSide, OrderType


    async def test_order_manager():
        print("Order Manager Test")
        print("=" * 60)

        # Initialize auth
        auth = FyersAuth()
        await auth.initialize()

        if not auth.is_authenticated:
            print("✗ Authentication failed")
            return

        # Create order manager
        order_manager = OrderManager(auth.get_client())

        print(f"\nTrading Mode: {order_manager.trading_mode.value}")
        print("-" * 60)

        # Test order placement (paper trading)
        symbol = "NSE:SBIN-EQ"

        print(f"\nPlacing paper order for {symbol}")
        order_id = await order_manager.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.MARKET,
            stop_loss=800,
            target=850
        )

        if order_id:
            print(f"✓ Order placed: {order_id}")

            # Check status
            status = order_manager.get_order_status(order_id)
            if status:
                print(f"\nOrder Status:")
                print(f"  Symbol: {status['symbol']}")
                print(f"  Side: {status['side'].value}")
                print(f"  Quantity: {status['quantity']}")
                print(f"  Status: {status['status']}")

        print("\n" + "=" * 60)


    asyncio.run(test_order_manager())