# strategy/mmfs_strategy.py

"""
5-Minute Market Force Scalping (MMFS) Strategy Implementation
Ultra-short scalping strategy for opening minutes (9:15-9:20 AM)
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional

from config.mmfs_config import (
    MMFSStrategyConfig, MMFSTradingConfig,
    GapType, MarketBreadth, MMFSSetupType
)
from config.settings import SignalType
from models.mmfs_models import (
    PreMarketData, MMFSSignal, MMFSPosition,
    MMFSTradeResult, MMFSStrategyMetrics, MMFSMarketState
)
from services.market_breadth_service import MarketBreadthService
from services.data_service import DataService
from services.order_manager import OrderManager

logger = logging.getLogger(__name__)


class MMFSStrategy:
    """5-Minute Market Force Scalping Strategy"""

    def __init__(
            self,
            strategy_config: MMFSStrategyConfig,
            trading_config: MMFSTradingConfig,
            data_service: DataService,
            order_manager: OrderManager,
            breadth_service: MarketBreadthService,
            symbols: List[str]
    ):
        self.strategy_config = strategy_config
        self.trading_config = trading_config
        self.data_service = data_service
        self.order_manager = order_manager
        self.breadth_service = breadth_service
        self.symbols = symbols

        # Market state
        self.market_state = MMFSMarketState(
            advances=0, declines=0, ad_ratio=1.0,
            breadth_classification=MarketBreadth.NEUTRAL,
            breadth_strength=50.0
        )

        # Pre-market data cache
        self.premarket_data: Dict[str, PreMarketData] = {}

        # First candle data (9:15-9:16)
        self.first_candle_data: Dict[str, Dict] = {}

        # 5-minute range data (9:15-9:20)
        self.five_min_range: Dict[str, Dict] = {}

        # Active positions
        self.positions: Dict[str, MMFSPosition] = {}

        # Completed trades
        self.completed_trades: List[MMFSTradeResult] = []

        # Strategy metrics
        self.metrics = MMFSStrategyMetrics()

        # Control flags
        self.is_running = False
        self.premarket_collected = False
        self.first_candle_tracked = False

        logger.info(" MMFS Strategy initialized")

    async def start(self):
        """Start MMFS strategy"""
        logger.info("=" * 80)
        logger.info(" Starting MMFS Strategy")
        logger.info(f" Portfolio: Rs.{self.strategy_config.portfolio_value:,}")
        logger.info(f" Risk per Trade: {self.strategy_config.risk_per_trade_pct}%")
        logger.info(f" Max Trades: {self.strategy_config.max_trades_per_day}")
        logger.info(f" Execution Window: 9:15-9:20 AM")
        logger.info("=" * 80)

        self.is_running = True

        try:
            # Main strategy loop
            while self.is_running:
                current_time = datetime.now().time()

                # Step 1: Collect pre-market data (9:00-9:14)
                if self._is_premarket_time(current_time) and not self.premarket_collected:
                    await self._collect_premarket_data()
                    self.premarket_collected = True

                # Step 2: Update market breadth (9:15)
                if self._is_market_open(current_time) and not self.market_state.premarket_data_collected:
                    await self._update_market_breadth()
                    self.market_state.premarket_data_collected = True

                # Step 3: Track first candle (9:15-9:16)
                if self._is_first_candle_time(current_time):
                    await self._track_first_candle()
                    if current_time >= time(9, 16) and not self.first_candle_tracked:
                        self.market_state.first_candle_complete = True
                        self.first_candle_tracked = True
                        logger.info(" First candle tracking complete")

                # Step 4: Track 5-minute range (9:15-9:20)
                if self._is_execution_window(current_time):
                    self.market_state.is_execution_window = True
                    await self._track_five_min_range()

                # Step 5: Evaluate setups and generate signals (9:16-9:20)
                if self._is_signal_generation_time(current_time):
                    await self._evaluate_setups()

                # Step 6: Monitor active positions
                if len(self.positions) > 0:
                    await self._monitor_positions()

                # Step 7: Check if trading day complete (after 9:25)
                if current_time > time(9, 25):
                    logger.info(" MMFS execution window complete for the day")
                    break

                await asyncio.sleep(1)  # Check every second

        except Exception as e:
            logger.error(f" Error in MMFS strategy: {e}", exc_info=True)
        finally:
            await self.stop()

    async def _collect_premarket_data(self):
        """Collect pre-market data for all symbols"""
        logger.info(" Collecting pre-market data...")

        for symbol in self.symbols:
            try:
                # Fetch previous day data
                # This is a placeholder - implement actual data fetching
                # You would typically use data_service to fetch historical data

                # For now, create dummy data structure
                # Replace with actual implementation
                logger.debug(f"Collecting data for {symbol}")

                # Example implementation:
                # prev_data = await self.data_service.get_previous_day_data(symbol)
                # current_open = await self.data_service.get_current_open(symbol)

                # premarket = PreMarketData(
                #     symbol=symbol,
                #     previous_close=prev_data['close'],
                #     today_open=current_open,
                #     prev_high=prev_data['high'],
                #     prev_low=prev_data['low'],
                #     prev_vwap=prev_data['vwap']
                # )
                #
                # self.premarket_data[symbol] = premarket
                # logger.info(f"  {symbol}: Gap {premarket.gap_pct:+.2f}% ({premarket.gap_type.value})")

            except Exception as e:
                logger.error(f"Error collecting premarket data for {symbol}: {e}")

        self.market_state.symbols_analyzed = len(self.premarket_data)
        logger.info(f" Pre-market data collected for {self.market_state.symbols_analyzed} symbols")

    async def _update_market_breadth(self):
        """Update market breadth classification"""
        logger.info(" Updating market breadth...")

        try:
            breadth_data = self.breadth_service.fetch_advance_decline_data()
            if breadth_data:
                ad_ratio, classification = self.breadth_service.calculate_breadth_ratio(breadth_data)
                strength = self.breadth_service.get_breadth_strength_score()

                self.market_state.advances = breadth_data['advances']
                self.market_state.declines = breadth_data['declines']
                self.market_state.ad_ratio = ad_ratio
                self.market_state.breadth_classification = self.breadth_service.get_market_breadth()
                self.market_state.breadth_strength = strength

                logger.info(f" Market Breadth: {classification} (A/D: {ad_ratio:.2f}, Strength: {strength:.0f}/100)")
            else:
                logger.warning(" Could not fetch market breadth data")
        except Exception as e:
            logger.error(f"Error updating market breadth: {e}")

    async def _track_first_candle(self):
        """Track first 1-minute candle (9:15-9:16)"""
        if self.market_state.first_candle_complete:
            return

        for symbol in self.symbols:
            try:
                # Fetch current candle data
                # Placeholder implementation - replace with actual data fetching
                # candle = await self.data_service.get_current_candle(symbol, timeframe='1min')

                # self.first_candle_data[symbol] = {
                #     'high': candle['high'],
                #     'low': candle['low'],
                #     'open': candle['open'],
                #     'close': candle['close'],
                #     'vwap': candle['vwap'],
                #     'volume': candle['volume'],
                #     'volume_ratio': candle['volume'] / candle.get('avg_volume', 1)
                # }

                pass

            except Exception as e:
                logger.error(f"Error tracking first candle for {symbol}: {e}")

    async def _track_five_min_range(self):
        """Track 5-minute range (9:15-9:20)"""
        for symbol in self.symbols:
            try:
                # Update 5-minute range
                # Placeholder - implement actual tracking
                pass

            except Exception as e:
                logger.error(f"Error tracking 5-min range for {symbol}: {e}")

    async def _evaluate_setups(self):
        """Evaluate all four MMFS setups"""
        if len(self.premarket_data) == 0:
            return

        for symbol, premarket in self.premarket_data.items():
            # Skip if already have position
            if symbol in self.positions:
                continue

            # Check if can take more trades
            can_trade, reason = self.market_state.can_take_trade(
                self.strategy_config.max_trades_per_day,
                self.strategy_config.max_loss_per_day_pct,
                self.strategy_config.portfolio_value
            )

            if not can_trade:
                logger.debug(f"Cannot take trade: {reason}")
                break

            # Evaluate each setup
            signal = None

            if self._should_evaluate_setup1(premarket):
                signal = await self._evaluate_setup1_gap_up_breakout(symbol, premarket)

            elif self._should_evaluate_setup2(premarket):
                signal = await self._evaluate_setup2_gap_up_failure(symbol, premarket)

            elif self._should_evaluate_setup3(premarket):
                signal = await self._evaluate_setup3_gap_down_recovery(symbol, premarket)

            elif self._should_evaluate_setup4(premarket):
                signal = await self._evaluate_setup4_range_breakdown(symbol, premarket)

            if signal:
                await self._execute_signal(signal)

    def _should_evaluate_setup1(self, premarket: PreMarketData) -> bool:
        """Check if should evaluate Setup 1: Gap-Up Breakout"""
        return (premarket.gap_pct >= self.strategy_config.setup1_min_gap_pct and
                self.market_state.breadth_classification == MarketBreadth.BULLISH)

    def _should_evaluate_setup2(self, premarket: PreMarketData) -> bool:
        """Check if should evaluate Setup 2: Gap-Up Failure"""
        return (premarket.gap_pct >= self.strategy_config.setup2_min_gap_pct and
                self.market_state.breadth_classification in [MarketBreadth.BEARISH, MarketBreadth.NEUTRAL])

    def _should_evaluate_setup3(self, premarket: PreMarketData) -> bool:
        """Check if should evaluate Setup 3: Gap-Down Recovery"""
        return (premarket.gap_pct <= -self.strategy_config.setup3_min_gap_pct and
                self.market_state.breadth_classification == MarketBreadth.BULLISH)

    def _should_evaluate_setup4(self, premarket: PreMarketData) -> bool:
        """Check if should evaluate Setup 4: Range Breakdown"""
        return (abs(premarket.gap_pct) < self.strategy_config.setup4_max_gap_pct and
                self.market_state.breadth_classification == MarketBreadth.NEUTRAL)

    async def _evaluate_setup1_gap_up_breakout(self, symbol: str, premarket: PreMarketData) -> Optional[MMFSSignal]:
        """
        Setup 1: Gap-Up Breakout (LONG)

        Conditions:
        - Gap ≥ +0.30%
        - Market breadth BULLISH (A/D > 1.5x)
        - First candle closes above VWAP
        - No major rejection wick

        Entry: Above first candle high
        Stop: First candle low
        Target: Previous day high or 1:1.5 RR
        """
        # Get first candle data
        if symbol not in self.first_candle_data:
            return None

        first_candle = self.first_candle_data[symbol]

        # Check VWAP alignment
        if self.strategy_config.setup1_require_vwap_above:
            if first_candle['close'] <= first_candle['vwap']:
                return None

        # Check rejection wick
        candle_range = first_candle['high'] - first_candle['low']
        if candle_range > 0:
            upper_wick = first_candle['high'] - max(first_candle['open'], first_candle['close'])
            rejection_pct = (upper_wick / candle_range) * 100

            if rejection_pct > self.strategy_config.setup1_max_rejection_wick_pct:
                return None
        else:
            return None

        # Calculate entry, stop, target
        entry_price = first_candle['high']
        stop_loss = first_candle['low']

        # Target: Previous day high or RR-based
        rr_target = entry_price + (entry_price - stop_loss) * self.strategy_config.risk_reward_ratio
        target_price = min(rr_target, premarket.prev_high)

        # Calculate confidence
        confidence = self._calculate_setup1_confidence(premarket, first_candle)

        if confidence < self.strategy_config.min_confidence_setup1:
            return None

        # Create signal
        signal = MMFSSignal(
            symbol=symbol,
            setup_type=MMFSSetupType.GAP_UP_BREAKOUT,
            signal_type=SignalType.LONG,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            gap_pct=premarket.gap_pct,
            gap_type=premarket.gap_type,
            market_breadth=self.market_state.breadth_classification,
            ad_ratio=self.market_state.ad_ratio,
            first_candle_high=first_candle['high'],
            first_candle_low=first_candle['low'],
            first_candle_close=first_candle['close'],
            first_candle_vwap=first_candle['vwap'],
            confidence=confidence,
            volume_ratio=first_candle.get('volume_ratio', 1.0),
            vwap_alignment=True
        )

        logger.info(f" Setup 1 Signal: {symbol} LONG @ {entry_price:.2f} "
                    f"(Gap: {premarket.gap_pct:+.2f}%, Confidence: {confidence:.0%})")

        return signal

    def _calculate_setup1_confidence(self, premarket: PreMarketData, first_candle: Dict) -> float:
        """Calculate confidence score for Setup 1"""
        score = 0.5  # Base score

        # Gap strength
        if premarket.gap_pct > 0.5:
            score += 0.15
        elif premarket.gap_pct > 0.3:
            score += 0.10

        # Breadth strength
        if self.market_state.breadth_strength > 70:
            score += 0.15
        elif self.market_state.breadth_strength > 60:
            score += 0.10

        # Volume confirmation
        volume_ratio = first_candle.get('volume_ratio', 1.0)
        if volume_ratio > 2.0:
            score += 0.10
        elif volume_ratio > 1.5:
            score += 0.05

        return min(score, 1.0)

    async def _evaluate_setup2_gap_up_failure(self, symbol: str, premarket: PreMarketData) -> Optional[MMFSSignal]:
        """
        Setup 2: Gap-Up Failure (SHORT)

        To be implemented with similar structure to Setup 1
        """
        # TODO: Implement Setup 2 logic
        return None

    async def _evaluate_setup3_gap_down_recovery(self, symbol: str, premarket: PreMarketData) -> Optional[MMFSSignal]:
        """
        Setup 3: Gap-Down Recovery (LONG)

        To be implemented
        """
        # TODO: Implement Setup 3 logic
        return None

    async def _evaluate_setup4_range_breakdown(self, symbol: str, premarket: PreMarketData) -> Optional[MMFSSignal]:
        """
        Setup 4: Opening Range Breakdown (Scalp)

        To be implemented
        """
        # TODO: Implement Setup 4 logic
        return None

    async def _execute_signal(self, signal: MMFSSignal):
        """Execute MMFS trade signal"""
        logger.info(f" Executing {signal.setup_type.value} signal for {signal.symbol}")

        # Calculate position size
        risk_amount = self.strategy_config.portfolio_value * (self.strategy_config.risk_per_trade_pct / 100)
        price_risk = abs(signal.entry_price - signal.stop_loss)

        if price_risk > 0:
            quantity = int(risk_amount / price_risk)
        else:
            logger.warning(f"Invalid price risk for {signal.symbol}, skipping trade")
            return

        logger.info(f"  Position Size: {quantity} units")
        logger.info(f"  Risk Amount: ₹{risk_amount:.2f}")
        logger.info(f"  Entry: {signal.entry_price}, Stop: {signal.stop_loss}, Target: {signal.target_price}")

        # Create position tracking
        position = MMFSPosition(
            symbol=signal.symbol,
            setup_type=signal.setup_type,
            signal_type=signal.signal_type,
            entry_price=signal.entry_price,
            quantity=quantity,
            stop_loss=signal.stop_loss,
            target_price=signal.target_price,
            gap_pct=signal.gap_pct,
            market_breadth=signal.market_breadth,
            entry_vwap=signal.first_candle_vwap,
            entry_time=datetime.now(),
            entry_minute=signal.signal_minute,
            max_holding_minutes=self.strategy_config.max_holding_minutes
        )

        try:
            # Place order using order manager
            # Placeholder - implement actual order placement
            # order_id = await self.order_manager.place_order(
            #     symbol=signal.symbol,
            #     side='BUY' if signal.signal_type == SignalType.LONG else 'SELL',
            #     quantity=quantity,
            #     price=signal.entry_price
            # )
            # position.order_id = order_id

            self.positions[signal.symbol] = position
            logger.info(f" Position opened for {signal.symbol}")

        except Exception as e:
            logger.error(f" Error executing signal: {e}")

    async def _monitor_positions(self):
        """Monitor active MMFS positions"""
        current_time = datetime.now()

        for symbol, position in list(self.positions.items()):
            try:
                # Check holding time
                holding_duration = position.get_holding_duration()

                # Time-based exit
                if position.should_exit_by_time():
                    logger.info(f" Time-based exit for {symbol} (held {holding_duration:.1f}min)")
                    await self._exit_position(position, "TIME_BASED")
                    continue

                # Update current price and P&L
                # Placeholder - fetch actual current price
                # current_price = await self.data_service.get_current_price(symbol)
                # position.update_price(current_price)

                # Check stop loss and target
                # if position.signal_type == SignalType.LONG:
                #     if current_price <= position.current_stop_loss:
                #         await self._exit_position(position, "STOP_LOSS")
                #     elif current_price >= position.target_price:
                #         await self._exit_position(position, "TARGET")

                # Move to breakeven after configured time
                if (not position.moved_to_breakeven and
                        holding_duration >= self.strategy_config.break_even_after_minutes):
                    if self._should_move_to_breakeven(position):
                        await self._move_to_breakeven(position)

            except Exception as e:
                logger.error(f"Error monitoring position for {symbol}: {e}")

    def _should_move_to_breakeven(self, position: MMFSPosition) -> bool:
        """Check if position should be moved to breakeven"""
        # Check if position is in profit
        if position.signal_type == SignalType.LONG:
            return position.current_price > position.entry_price
        else:
            return position.current_price < position.entry_price

    async def _move_to_breakeven(self, position: MMFSPosition):
        """Move stop loss to breakeven"""
        logger.info(f" Moving {position.symbol} to breakeven")

        position.current_stop_loss = position.entry_price
        position.moved_to_breakeven = True
        position.breakeven_time = datetime.now()

        # Update stop loss order
        # Placeholder - implement actual stop loss modification
        # await self.order_manager.modify_stop_loss(position.sl_order_id, position.entry_price)

    async def _exit_position(self, position: MMFSPosition, exit_reason: str):
        """Exit MMFS position"""
        logger.info(f" Exiting {position.symbol} - Reason: {exit_reason}")

        # Placeholder - get actual exit price
        exit_price = position.current_price if position.current_price > 0 else position.entry_price

        # Create trade result
        trade = MMFSTradeResult(
            symbol=position.symbol,
            setup_type=position.setup_type,
            signal_type=position.signal_type,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            entry_time=position.entry_time,
            exit_time=datetime.now(),
            exit_reason=exit_reason,
            max_favorable_excursion=position.max_favorable_excursion,
            max_adverse_excursion=position.max_adverse_excursion,
            gap_pct=position.gap_pct,
            market_breadth=position.market_breadth,
            signal_minute=position.entry_minute
        )

        # Update metrics
        self.metrics.update_from_trade(trade)
        self.market_state.update_after_trade(trade.net_pnl)
        self.completed_trades.append(trade)

        # Remove position
        del self.positions[position.symbol]

        # Log trade result
        result_emoji = "" if trade.is_winner() else "" if trade.is_loser() else "⚖"
        logger.info(f"{result_emoji} Trade Complete: {trade.symbol} | "
                    f"P&L: ₹{trade.net_pnl:+,.2f} ({trade.return_pct:+.2f}%) | "
                    f"Held: {trade.holding_duration_seconds}s")

        # Check if should stop trading after first loss
        if (self.strategy_config.stop_after_first_loss and
                trade.is_loser() and
                self.market_state.trades_today == 1):
            self.market_state.stop_trading_till_945 = True
            logger.warning(" First trade was a loss. Stopping trading till 9:45 AM")

    # Helper methods

    def _is_premarket_time(self, current_time: time) -> bool:
        """Check if it's pre-market time"""
        return time(9, 0) <= current_time < time(9, 15)

    def _is_market_open(self, current_time: time) -> bool:
        """Check if market is open"""
        return current_time >= time(9, 15)

    def _is_execution_window(self, current_time: time) -> bool:
        """Check if in execution window (9:15-9:20)"""
        return time(9, 15) <= current_time < time(9, 20)

    def _is_first_candle_time(self, current_time: time) -> bool:
        """Check if tracking first candle"""
        return time(9, 15) <= current_time <= time(9, 16)

    def _is_signal_generation_time(self, current_time: time) -> bool:
        """Check if time to generate signals"""
        return time(9, 16) <= current_time < time(9, 20)

    async def stop(self):
        """Stop MMFS strategy"""
        logger.info("=" * 80)
        logger.info(" Stopping MMFS Strategy")
        self.is_running = False

        # Close any open positions
        for symbol in list(self.positions.keys()):
            await self._exit_position(self.positions[symbol], "STRATEGY_STOP")

        # Print final metrics
        self._print_final_metrics()

    def _print_final_metrics(self):
        """Print final strategy metrics"""
        logger.info("=" * 80)
        logger.info(" MMFS Strategy - Final Metrics")
        logger.info("=" * 80)
        logger.info(f"Total Trades: {self.metrics.total_trades}")
        logger.info(f"Winners: {self.metrics.winning_trades} | Losers: {self.metrics.losing_trades}")
        logger.info(f"Win Rate: {self.metrics.win_rate:.1f}%")
        logger.info(f"Gross P&L: ₹{self.metrics.gross_pnl:+,.2f}")
        logger.info(f"Net P&L: ₹{self.metrics.net_pnl:+,.2f}")
        logger.info(f"Profit Factor: {self.metrics.profit_factor:.2f}")
        logger.info(f"Expectancy: ₹{self.metrics.expectancy:+,.2f}")
        logger.info(f"\nSetup Performance:")
        logger.info(f"  Setup 1 (Gap-Up Breakout): {self.metrics.get_setup_win_rate(MMFSSetupType.GAP_UP_BREAKOUT):.1f}% ({self.metrics.setup1_wins}/{self.metrics.setup1_trades})")
        logger.info(f"  Setup 2 (Gap-Up Failure): {self.metrics.get_setup_win_rate(MMFSSetupType.GAP_UP_FAILURE):.1f}% ({self.metrics.setup2_wins}/{self.metrics.setup2_trades})")
        logger.info(
            f"  Setup 3 (Gap-Down Recovery): {self.metrics.get_setup_win_rate(MMFSSetupType.GAP_DOWN_RECOVERY):.1f}% ({self.metrics.setup3_wins}/{self.metrics.setup3_trades})")
        logger.info(f"  Setup 4 (Range Breakdown): {self.metrics.get_setup_win_rate(MMFSSetupType.RANGE_BREAKDOWN):.1f}% ({self.metrics.setup4_wins}/{self.metrics.setup4_trades})")
        logger.info("=" * 80)


if __name__ == "__main__":
    print("MMFS Strategy - Template created successfully")
    print("This file contains the main strategy implementation structure")
    print("Complete the setup evaluation methods and integrate with your existing infrastructure")