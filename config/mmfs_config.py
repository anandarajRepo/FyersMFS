# config/mmfs_config.py

"""
Configuration for 5-Minute Market Force Scalping (MMFS) Strategy
Defines all MMFS-specific parameters and settings
"""

import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class GapType(Enum):
    """Gap classification based on size"""
    SMALL = "SMALL"  # ±0.30%
    MODERATE = "MODERATE"  # ±0.30% to ±0.80%
    STRONG = "STRONG"  # > ±0.80%
    NO_GAP = "NO_GAP"


class MarketBreadth(Enum):
    """Market breadth classification"""
    BULLISH = "BULLISH"  # Advances > Declines by 1.5x
    BEARISH = "BEARISH"  # Declines > Advances by 1.5x
    NEUTRAL = "NEUTRAL"  # Near equal


class MMFSSetupType(Enum):
    """MMFS trade setup types"""
    GAP_UP_BREAKOUT = "GAP_UP_BREAKOUT"  # Setup 1: Gap-Up + Breadth Confirmation
    GAP_UP_FAILURE = "GAP_UP_FAILURE"  # Setup 2: Gap-Up Failure
    GAP_DOWN_RECOVERY = "GAP_DOWN_RECOVERY"  # Setup 3: Gap-Down + Breadth Support
    RANGE_BREAKDOWN = "RANGE_BREAKDOWN"  # Setup 4: Opening Range Breakdown


@dataclass
class MMFSStrategyConfig:
    """5-Minute Market Force Scalping Strategy Configuration"""

    # Portfolio settings
    portfolio_value: float = 100000  # ₹1 lakh
    risk_per_trade_pct: float = 0.5  # 0.5% risk per trade (conservative for scalping)
    max_positions: int = 1  # Max 1 trade per direction

    # MMFS specific timing
    execution_start_hour: int = 9
    execution_start_minute: int = 15
    execution_end_hour: int = 9
    execution_end_minute: int = 20  # 5-minute execution window

    # Holding period
    min_holding_minutes: int = 1  # Minimum 1 minute
    max_holding_minutes: int = 5  # Maximum 5 minutes

    # Gap classification thresholds (%)
    small_gap_threshold: float = 0.30
    moderate_gap_threshold: float = 0.80

    # Market breadth requirements
    breadth_bullish_ratio: float = 1.5  # Advances/Declines ratio for bullish
    breadth_bearish_ratio: float = 1.5  # Declines/Advances ratio for bearish

    # Setup 1: Gap-Up + Breadth Confirmation
    setup1_min_gap_pct: float = 0.30  # Minimum gap up %
    setup1_require_vwap_above: bool = True  # Must close above VWAP
    setup1_max_rejection_wick_pct: float = 30  # Max upper wick as % of candle

    # Setup 2: Gap-Up Failure
    setup2_min_gap_pct: float = 0.50  # Minimum gap up % for failure trade
    setup2_require_vwap_rejection: bool = True  # Must reject VWAP
    setup2_min_upper_wick_pct: float = 40  # Minimum upper wick %
    setup2_require_volume_spike: bool = True

    # Setup 3: Gap-Down Recovery
    setup3_min_gap_pct: float = 0.30  # Minimum gap down %
    setup3_require_vwap_reclaim: bool = True  # Must reclaim VWAP

    # Setup 4: Opening Range Breakdown
    setup4_max_gap_pct: float = 0.30  # Small gap only
    setup4_require_volume_breakout: bool = True
    setup4_scalp_target_pct: float = 0.25  # Fixed scalp target

    # Risk management
    risk_reward_ratio: float = 1.5  # Default 1:1.5
    use_fixed_stops: bool = True  # Use candle high/low for stops
    trail_profit: bool = False  # No trailing for scalping

    # Exit rules
    max_profit_target_pct: float = 0.50  # Maximum profit target for scalping
    time_based_exit: bool = True  # Exit after max holding period
    break_even_after_minutes: int = 2  # Move to breakeven after 2 minutes

    # Volume filters
    min_volume_ratio: float = 1.5  # Current vs average volume
    require_volume_confirmation: bool = True

    # VIX filter (optional)
    use_vix_filter: bool = True
    vix_rising_favor_breakout: bool = True  # Favor breakouts when VIX rising
    min_vix_change_pct: float = 5.0  # Min VIX change % to consider

    # Daily limits
    max_trades_per_day: int = 2  # Maximum 2 trades total
    max_loss_per_day_pct: float = 1.0  # Stop after 1% daily loss
    stop_after_first_loss: bool = True  # Stop trading till 9:45 after first loss

    # Instrument preferences
    prefer_index_options: bool = True  # Prefer NIFTY/BANKNIFTY options
    prefer_atm_options: bool = True  # Prefer at-the-money options
    option_strike_range: int = 2  # Number of strikes away from ATM

    # Signal confidence thresholds
    min_confidence_setup1: float = 0.70  # Gap-up breakout
    min_confidence_setup2: float = 0.65  # Gap-up failure
    min_confidence_setup3: float = 0.70  # Gap-down recovery
    min_confidence_setup4: float = 0.60  # Range breakdown scalp


@dataclass
class MMFSTradingConfig:
    """MMFS Trading session configuration"""

    # Market hours (IST)
    market_start_hour: int = 9
    market_start_minute: int = 15
    market_end_hour: int = 15
    market_end_minute: int = 30

    # MMFS specific timing
    strategy_start_hour: int = 9
    strategy_start_minute: int = 15
    strategy_end_hour: int = 9
    strategy_end_minute: int = 20  # Only trade first 5 minutes

    # Resume trading time (after first loss)
    resume_trading_hour: int = 9
    resume_trading_minute: int = 45

    # Monitoring intervals
    monitoring_interval: int = 1  # Check every second during execution window
    position_update_interval: int = 1  # Update positions every second

    # Pre-market data collection
    collect_premarket_data: bool = True
    premarket_start_hour: int = 9
    premarket_start_minute: int = 0


def get_mmfs_default_config():
    """Get default MMFS strategy configuration"""
    return {
        'strategy': MMFSStrategyConfig(),
        'trading': MMFSTradingConfig()
    }


def get_mmfs_aggressive_config():
    """Get aggressive MMFS configuration for experienced traders"""
    config = MMFSStrategyConfig(
        portfolio_value=200000,  # ₹2 lakh
        risk_per_trade_pct=0.75,  # Higher risk
        max_positions=2,  # Allow 2 positions
        max_trades_per_day=3,
        stop_after_first_loss=False,  # Continue after first loss
        risk_reward_ratio=2.0,  # Higher RR
        max_profit_target_pct=0.75
    )

    return {
        'strategy': config,
        'trading': MMFSTradingConfig()
    }


def get_mmfs_conservative_config():
    """Get conservative MMFS configuration for beginners"""
    config = MMFSStrategyConfig(
        portfolio_value=50000,  # ₹50k
        risk_per_trade_pct=0.25,  # Very low risk
        max_positions=1,
        max_trades_per_day=1,  # Only 1 trade per day
        stop_after_first_loss=True,
        risk_reward_ratio=2.0,  # Higher RR for safety
        use_vix_filter=True,
        min_confidence_setup1=0.75,
        min_confidence_setup2=0.70,
        min_confidence_setup3=0.75,
        min_confidence_setup4=0.70
    )

    return {
        'strategy': config,
        'trading': MMFSTradingConfig()
    }


def validate_mmfs_config(config: MMFSStrategyConfig) -> dict:
    """Validate MMFS configuration parameters"""
    validation = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # Portfolio validation
    if config.portfolio_value <= 0:
        validation['errors'].append("Portfolio value must be positive")
        validation['valid'] = False

    if config.portfolio_value < 25000:
        validation['warnings'].append("Portfolio value quite low for scalping")

    # Risk validation
    if config.risk_per_trade_pct <= 0 or config.risk_per_trade_pct > 2:
        validation['errors'].append("Risk per trade should be between 0.1% and 2%")
        validation['valid'] = False

    if config.risk_per_trade_pct > 1.0:
        validation['warnings'].append("High risk per trade for scalping strategy")

    # Position limits
    if config.max_positions <= 0 or config.max_positions > 3:
        validation['errors'].append("Max positions should be between 1 and 3 for scalping")
        validation['valid'] = False

    # Timing validation
    if config.execution_end_minute - config.execution_start_minute != 5:
        validation['warnings'].append("Execution window should be exactly 5 minutes")

    # Holding period
    if config.max_holding_minutes > 10:
        validation['warnings'].append("Max holding period too long for scalping strategy")

    # Gap thresholds
    if config.small_gap_threshold >= config.moderate_gap_threshold:
        validation['errors'].append("Small gap threshold must be less than moderate")
        validation['valid'] = False

    # Risk-reward
    if config.risk_reward_ratio < 1.0:
        validation['warnings'].append("Risk-reward ratio below 1:1 not recommended")

    # Daily limits
    if config.max_trades_per_day > 5:
        validation['warnings'].append("Too many trades per day for scalping strategy")

    if config.max_loss_per_day_pct > 2.0:
        validation['warnings'].append("Daily loss limit high for scalping")

    return validation


# Load configuration from environment variables
def load_mmfs_config_from_env() -> tuple:
    """Load MMFS configuration from environment variables"""

    strategy_config = MMFSStrategyConfig(
        portfolio_value=float(os.environ.get('MMFS_PORTFOLIO_VALUE', 100000)),
        risk_per_trade_pct=float(os.environ.get('MMFS_RISK_PER_TRADE', 0.5)),
        max_positions=int(os.environ.get('MMFS_MAX_POSITIONS', 1)),
        max_trades_per_day=int(os.environ.get('MMFS_MAX_TRADES_PER_DAY', 2)),
        risk_reward_ratio=float(os.environ.get('MMFS_RISK_REWARD_RATIO', 1.5)),
        stop_after_first_loss=os.environ.get('MMFS_STOP_AFTER_FIRST_LOSS', 'true').lower() == 'true',
        use_vix_filter=os.environ.get('MMFS_USE_VIX_FILTER', 'true').lower() == 'true'
    )

    trading_config = MMFSTradingConfig()

    return strategy_config, trading_config


if __name__ == "__main__":
    print("MMFS Strategy Configuration Test")
    print("=" * 60)

    # Test default configuration
    default_config = get_mmfs_default_config()
    print("\nDefault Configuration:")
    print(f"  Portfolio: ₹{default_config['strategy'].portfolio_value:,}")
    print(f"  Risk per Trade: {default_config['strategy'].risk_per_trade_pct}%")
    print(f"  Max Positions: {default_config['strategy'].max_positions}")
    print(
        f"  Execution Window: {default_config['strategy'].execution_start_hour}:{default_config['strategy'].execution_start_minute:02d} - {default_config['strategy'].execution_end_hour}:{default_config['strategy'].execution_end_minute:02d}")

    # Validate configuration
    validation = validate_mmfs_config(default_config['strategy'])
    print(f"\nConfiguration Validation:")
    print(f"  Valid: {validation['valid']}")
    if validation['errors']:
        print(f"  Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")

    # Test different profiles
    print(f"\n" + "=" * 60)
    print("Configuration Profiles:")

    profiles = {
        'Conservative': get_mmfs_conservative_config(),
        'Default': get_mmfs_default_config(),
        'Aggressive': get_mmfs_aggressive_config()
    }

    for name, config in profiles.items():
        print(f"\n{name} Profile:")
        print(f"  Portfolio: ₹{config['strategy'].portfolio_value:,}")
        print(f"  Risk: {config['strategy'].risk_per_trade_pct}%")
        print(f"  Max Trades/Day: {config['strategy'].max_trades_per_day}")
        print(f"  RR Ratio: {config['strategy'].risk_reward_ratio}:1")