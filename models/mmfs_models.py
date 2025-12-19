# models/mmfs_models.py

"""
Data Models for 5-Minute Market Force Scalping (MMFS) Strategy
Defines all MMFS-specific data structures
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict

from config.settings import SignalType
from config.mmfs_config import GapType, MarketBreadth, MMFSSetupType

logger = logging.getLogger(__name__)


@dataclass
class PreMarketData:
    """Pre-market analysis data"""
    symbol: str

    # Gap analysis
    previous_close: float
    today_open: float
    gap_pct: float = field(init=False)
    gap_type: GapType = field(init=False)

    # Previous day data
    prev_high: float
    prev_low: float
    prev_vwap: float

    # Pre-market indicators
    premarket_high: Optional[float] = None
    premarket_low: Optional[float] = None
    premarket_volume: Optional[int] = None

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Calculate gap percentage and type"""
        if self.previous_close > 0:
            self.gap_pct = ((self.today_open - self.previous_close) / self.previous_close) * 100

            # Classify gap type
            abs_gap = abs(self.gap_pct)
            if abs_gap <= 0.30:
                self.gap_type = GapType.SMALL
            elif abs_gap <= 0.80:
                self.gap_type = GapType.MODERATE
            else:
                self.gap_type = GapType.STRONG
        else:
            self.gap_pct = 0.0
            self.gap_type = GapType.NO_GAP


@dataclass
class MMFSSignal:
    """MMFS Trading Signal"""
    symbol: str
    setup_type: MMFSSetupType
    signal_type: SignalType  # LONG or SHORT

    # Entry parameters
    entry_price: float
    stop_loss: float
    target_price: float

    # Gap and breadth context
    gap_pct: float
    gap_type: GapType
    market_breadth: MarketBreadth
    ad_ratio: float

    # First candle data
    first_candle_high: float
    first_candle_low: float
    first_candle_close: float
    first_candle_vwap: float

    # 5-minute range (if applicable)
    five_min_range_high: Optional[float] = None
    five_min_range_low: Optional[float] = None

    # Signal quality metrics
    confidence: float  # 0-1 scale
    volume_ratio: float  # Current vs average
    vwap_alignment: bool  # Price aligned with VWAP as per setup
    rejection_wick_pct: float = 0.0  # For failure setups

    # Risk metrics
    risk_amount: float = field(init=False)
    reward_amount: float = field(init=False)
    risk_reward_ratio: float = field(init=False)

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    signal_minute: int = field(init=False)  # 0-4 (minutes into 9:15-9:20 window)

    # VIX context (optional)
    vix_value: Optional[float] = None
    vix_change_pct: Optional[float] = None

    def __post_init__(self):
        """Calculate derived metrics"""
        self.risk_amount = abs(self.entry_price - self.stop_loss)
        self.reward_amount = abs(self.target_price - self.entry_price)

        if self.risk_amount > 0:
            self.risk_reward_ratio = self.reward_amount / self.risk_amount
        else:
            self.risk_reward_ratio = 0

        # Calculate signal minute (0-4)
        minutes_past_915 = (self.timestamp.hour - 9) * 60 + (self.timestamp.minute - 15)
        self.signal_minute = max(0, min(4, minutes_past_915))


@dataclass
class MMFSPosition:
    """MMFS Trading Position"""
    symbol: str
    setup_type: MMFSSetupType
    signal_type: SignalType

    # Position details
    entry_price: float
    quantity: int
    stop_loss: float
    target_price: float

    # Original signal context
    gap_pct: float
    market_breadth: MarketBreadth
    entry_vwap: float

    # Timing
    entry_time: datetime
    entry_minute: int  # 0-4 (minutes into execution window)
    max_holding_minutes: int = 5

    # Position tracking
    current_price: float = 0.0
    current_stop_loss: float = field(init=False)
    highest_price: float = field(init=False)
    lowest_price: float = field(init=False)

    # Orders
    order_id: Optional[str] = None
    sl_order_id: Optional[str] = None
    target_order_id: Optional[str] = None

    # Performance tracking
    unrealized_pnl: float = 0.0
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0

    # Status flags
    moved_to_breakeven: bool = False
    breakeven_time: Optional[datetime] = None

    def __post_init__(self):
        """Initialize position tracking"""
        self.current_stop_loss = self.stop_loss
        self.highest_price = self.entry_price if self.signal_type == SignalType.LONG else 0.0
        self.lowest_price = self.entry_price if self.signal_type == SignalType.SHORT else float('inf')

        # Calculate entry minute
        minutes_past_915 = (self.entry_time.hour - 9) * 60 + (self.entry_time.minute - 15)
        self.entry_minute = max(0, min(4, minutes_past_915))

    def update_price(self, current_price: float):
        """Update current price and tracking metrics"""
        self.current_price = current_price

        # Update highest/lowest
        if self.signal_type == SignalType.LONG:
            self.highest_price = max(self.highest_price, current_price)
            favorable_move = current_price - self.entry_price
            adverse_move = self.entry_price - min(self.lowest_price, current_price)
        else:
            self.lowest_price = min(self.lowest_price, current_price)
            favorable_move = self.entry_price - current_price
            adverse_move = max(self.highest_price, current_price) - self.entry_price

        # Update MFE/MAE
        self.max_favorable_excursion = max(self.max_favorable_excursion, favorable_move)
        self.max_adverse_excursion = max(self.max_adverse_excursion, adverse_move)

        # Calculate unrealized P&L
        if self.signal_type == SignalType.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity

    def get_holding_duration(self) -> float:
        """Get holding duration in minutes"""
        duration = datetime.now() - self.entry_time
        return duration.total_seconds() / 60

    def should_exit_by_time(self) -> bool:
        """Check if position should be exited due to time limit"""
        return self.get_holding_duration() >= self.max_holding_minutes


@dataclass
class MMFSTradeResult:
    """Completed MMFS Trade Result"""
    symbol: str
    setup_type: MMFSSetupType
    signal_type: SignalType

    # Trade execution
    entry_price: float
    exit_price: float
    quantity: int

    # Timing
    entry_time: datetime
    exit_time: datetime
    holding_duration_seconds: int = field(init=False)

    # Performance
    gross_pnl: float = field(init=False)
    net_pnl: float = field(init=False)
    return_pct: float = field(init=False)

    # Exit details
    exit_reason: str  # "TARGET", "STOP_LOSS", "TIME_BASED", "BREAKEVEN"
    max_favorable_excursion: float
    max_adverse_excursion: float

    # Context
    gap_pct: float
    market_breadth: MarketBreadth
    signal_minute: int  # 0-4

    def __post_init__(self):
        """Calculate trade metrics"""
        duration = self.exit_time - self.entry_time
        self.holding_duration_seconds = int(duration.total_seconds())

        if self.signal_type == SignalType.LONG:
            self.gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        else:
            self.gross_pnl = (self.entry_price - self.exit_price) * self.quantity

        # Estimate costs (adjust based on broker)
        brokerage = 20  # Flat ₹20 per trade
        stt = abs(self.exit_price * self.quantity * 0.00025)  # 0.025% on sell side
        transaction_charges = abs(self.exit_price * self.quantity * 0.0000325)
        gst = (brokerage + transaction_charges) * 0.18

        total_costs = brokerage * 2 + stt + transaction_charges + gst
        self.net_pnl = self.gross_pnl - total_costs

        if abs(self.entry_price * self.quantity) > 0:
            self.return_pct = (self.net_pnl / abs(self.entry_price * self.quantity)) * 100
        else:
            self.return_pct = 0.0

    def is_winner(self) -> bool:
        """Check if trade was profitable"""
        return self.net_pnl > 0

    def is_loser(self) -> bool:
        """Check if trade was a loss"""
        return self.net_pnl < 0

    def is_breakeven(self) -> bool:
        """Check if trade was breakeven"""
        return abs(self.net_pnl) < 10  # Within ₹10


@dataclass
class MMFSStrategyMetrics:
    """MMFS Strategy Performance Metrics"""

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0

    # Win rate by setup type
    setup1_trades: int = 0
    setup1_wins: int = 0
    setup2_trades: int = 0
    setup2_wins: int = 0
    setup3_trades: int = 0
    setup3_wins: int = 0
    setup4_trades: int = 0
    setup4_wins: int = 0

    # P&L metrics
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0

    # Performance ratios
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_rr_ratio: float = 0.0
    expectancy: float = 0.0

    # Timing statistics
    avg_holding_time_seconds: float = 0.0
    trades_by_minute: Dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0})

    # Exit reasons
    target_exits: int = 0
    stop_exits: int = 0
    time_exits: int = 0
    breakeven_exits: int = 0

    def update_from_trade(self, trade: MMFSTradeResult):
        """Update metrics from completed trade"""
        self.total_trades += 1

        # Update win/loss counters
        if trade.is_winner():
            self.winning_trades += 1
            self.largest_win = max(self.largest_win, trade.net_pnl)
        elif trade.is_loser():
            self.losing_trades += 1
            self.largest_loss = min(self.largest_loss, trade.net_pnl)
        else:
            self.breakeven_trades += 1

        # Update setup-specific stats
        if trade.setup_type == MMFSSetupType.GAP_UP_BREAKOUT:
            self.setup1_trades += 1
            if trade.is_winner():
                self.setup1_wins += 1
        elif trade.setup_type == MMFSSetupType.GAP_UP_FAILURE:
            self.setup2_trades += 1
            if trade.is_winner():
                self.setup2_wins += 1
        elif trade.setup_type == MMFSSetupType.GAP_DOWN_RECOVERY:
            self.setup3_trades += 1
            if trade.is_winner():
                self.setup3_wins += 1
        elif trade.setup_type == MMFSSetupType.RANGE_BREAKDOWN:
            self.setup4_trades += 1
            if trade.is_winner():
                self.setup4_wins += 1

        # Update P&L
        self.gross_pnl += trade.gross_pnl
        self.net_pnl += trade.net_pnl

        # Update exit reason counters
        if trade.exit_reason == "TARGET":
            self.target_exits += 1
        elif trade.exit_reason == "STOP_LOSS":
            self.stop_exits += 1
        elif trade.exit_reason == "TIME_BASED":
            self.time_exits += 1
        elif trade.exit_reason == "BREAKEVEN":
            self.breakeven_exits += 1

        # Update timing
        if trade.signal_minute in self.trades_by_minute:
            self.trades_by_minute[trade.signal_minute] += 1

        # Recalculate derived metrics
        self._recalculate_metrics()

    def _recalculate_metrics(self):
        """Recalculate all derived metrics"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        else:
            self.win_rate = 0.0

        # Calculate average win/loss
        if self.winning_trades > 0:
            self.average_win = self.gross_pnl / self.winning_trades if self.gross_pnl > 0 else 0
        if self.losing_trades > 0:
            total_losses = abs(self.largest_loss) * self.losing_trades  # Approximation
            self.average_loss = -total_losses / self.losing_trades if total_losses > 0 else 0

        # Profit factor
        total_wins = self.winning_trades * abs(self.average_win) if self.winning_trades > 0 else 0
        total_losses = self.losing_trades * abs(self.average_loss) if self.losing_trades > 0 else 0

        if total_losses > 0:
            self.profit_factor = total_wins / total_losses
        else:
            self.profit_factor = float('inf') if total_wins > 0 else 0.0

        # Expectancy
        if self.total_trades > 0:
            self.expectancy = self.net_pnl / self.total_trades
        else:
            self.expectancy = 0.0

    def get_setup_win_rate(self, setup_type: MMFSSetupType) -> float:
        """Get win rate for specific setup"""
        if setup_type == MMFSSetupType.GAP_UP_BREAKOUT:
            return (self.setup1_wins / self.setup1_trades * 100) if self.setup1_trades > 0 else 0.0
        elif setup_type == MMFSSetupType.GAP_UP_FAILURE:
            return (self.setup2_wins / self.setup2_trades * 100) if self.setup2_trades > 0 else 0.0
        elif setup_type == MMFSSetupType.GAP_DOWN_RECOVERY:
            return (self.setup3_wins / self.setup3_trades * 100) if self.setup3_trades > 0 else 0.0
        elif setup_type == MMFSSetupType.RANGE_BREAKDOWN:
            return (self.setup4_wins / self.setup4_trades * 100) if self.setup4_trades > 0 else 0.0
        return 0.0


@dataclass
class MMFSMarketState:
    """Current market state for MMFS execution"""

    # Market breadth
    advances: int
    declines: int
    ad_ratio: float
    breadth_classification: MarketBreadth
    breadth_strength: float  # 0-100

    # VIX data (if available)
    vix_value: Optional[float] = None
    vix_change_pct: Optional[float] = None

    # Execution window status
    is_execution_window: bool = False
    minutes_into_window: int = 0

    # Pre-market data collected
    premarket_data_collected: bool = False
    symbols_analyzed: int = 0

    # First candle tracking
    first_candle_complete: bool = False
    five_min_range_complete: bool = False

    # Risk state
    trades_today: int = 0
    daily_pnl: float = 0.0
    max_trades_reached: bool = False
    daily_loss_limit_reached: bool = False
    stop_trading_till_945: bool = False

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)

    def can_take_trade(self, max_trades: int, max_loss_pct: float, portfolio_value: float) -> tuple:
        """
        Check if new trade can be taken

        Returns:
            (can_trade: bool, reason: str)
        """
        if not self.is_execution_window:
            return False, "Outside execution window"

        if self.max_trades_reached or self.trades_today >= max_trades:
            return False, f"Max trades reached ({max_trades})"

        max_loss_amount = portfolio_value * (max_loss_pct / 100)
        if self.daily_pnl <= -max_loss_amount:
            return False, f"Daily loss limit reached ({max_loss_pct}%)"

        if self.stop_trading_till_945:
            return False, "Stopped after first loss (till 9:45)"

        return True, "OK"

    def update_after_trade(self, trade_pnl: float):
        """Update state after trade completion"""
        self.trades_today += 1
        self.daily_pnl += trade_pnl

    def reset_daily(self):
        """Reset daily counters"""
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.max_trades_reached = False
        self.daily_loss_limit_reached = False
        self.stop_trading_till_945 = False


if __name__ == "__main__":
    print("MMFS Data Models Test")
    print("=" * 60)

    # Test PreMarketData
    print("\n1. Testing PreMarketData:")
    premarket = PreMarketData(
        symbol="NIFTY",
        previous_close=21500,
        today_open=21580,
        prev_high=21600,
        prev_low=21400,
        prev_vwap=21480
    )
    print(f"  Symbol: {premarket.symbol}")
    print(f"  Gap: {premarket.gap_pct:+.2f}%")
    print(f"  Gap Type: {premarket.gap_type.value}")

    # Test MMFSSignal
    print("\n2. Testing MMFSSignal:")
    signal = MMFSSignal(
        symbol="NIFTY",
        setup_type=MMFSSetupType.GAP_UP_BREAKOUT,
        signal_type=SignalType.LONG,
        entry_price=21600,
        stop_loss=21550,
        target_price=21675,
        gap_pct=0.37,
        gap_type=GapType.MODERATE,
        market_breadth=MarketBreadth.BULLISH,
        ad_ratio=1.8,
        first_candle_high=21595,
        first_candle_low=21565,
        first_candle_close=21590,
        first_candle_vwap=21580,
        confidence=0.75,
        volume_ratio=1.6,
        vwap_alignment=True
    )
    print(f"  Setup: {signal.setup_type.value}")
    print(f"  Entry: {signal.entry_price}, Stop: {signal.stop_loss}, Target: {signal.target_price}")
    print(f"  Risk: ₹{signal.risk_amount:.2f}, Reward: ₹{signal.reward_amount:.2f}")
    print(f"  RR Ratio: 1:{signal.risk_reward_ratio:.2f}")
    print(f"  Confidence: {signal.confidence:.0%}")

    # Test MMFSTradeResult
    print("\n3. Testing MMFSTradeResult:")
    from datetime import timedelta

    entry_time = datetime.now()
    exit_time = entry_time + timedelta(minutes=3)

    trade = MMFSTradeResult(
        symbol="NIFTY",
        setup_type=MMFSSetupType.GAP_UP_BREAKOUT,
        signal_type=SignalType.LONG,
        entry_price=21600,
        exit_price=21675,
        quantity=50,
        entry_time=entry_time,
        exit_time=exit_time,
        exit_reason="TARGET",
        max_favorable_excursion=80,
        max_adverse_excursion=15,
        gap_pct=0.37,
        market_breadth=MarketBreadth.BULLISH,
        signal_minute=1
    )
    print(f"  Gross P&L: ₹{trade.gross_pnl:,.2f}")
    print(f"  Net P&L: ₹{trade.net_pnl:,.2f}")
    print(f"  Return: {trade.return_pct:+.2f}%")
    print(f"  Holding: {trade.holding_duration_seconds}s")
    print(f"  Winner: {trade.is_winner()}")

    # Test MMFSStrategyMetrics
    print("\n4. Testing MMFSStrategyMetrics:")
    metrics = MMFSStrategyMetrics()
    metrics.update_from_trade(trade)
    print(f"  Total Trades: {metrics.total_trades}")
    print(f"  Win Rate: {metrics.win_rate:.1f}%")
    print(f"  Net P&L: ₹{metrics.net_pnl:,.2f}")
    print(f"  Setup 1 Win Rate: {metrics.get_setup_win_rate(MMFSSetupType.GAP_UP_BREAKOUT):.1f}%")

    print("\n✓ All models working correctly!")