# utils/helpers.py

"""
Helper functions for MMFS strategy
"""

from datetime import datetime, time
import pytz
from typing import Tuple


def get_current_ist_time() -> datetime:
    """Get current time in IST"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)


def is_market_open() -> Tuple[bool, str]:
    """
    Check if market is currently open

    Returns:
        Tuple of (is_open, reason)
    """
    now = get_current_ist_time()
    current_time = now.time()

    # Check if weekend
    if now.weekday() >= 5:  # Saturday or Sunday
        return False, "Market closed - Weekend"

    # Market hours: 9:15 AM to 3:30 PM IST
    market_open = time(9, 15)
    market_close = time(15, 30)

    if current_time < market_open:
        return False, "Market not yet open"
    elif current_time > market_close:
        return False, "Market closed for the day"
    else:
        return True, "Market is open"


def format_currency(amount: float, currency: str = '₹') -> str:
    """Format currency with Indian numbering system"""
    if amount < 0:
        return f"-{currency}{abs(amount):,.2f}"
    return f"{currency}{amount:,.2f}"


def calculate_position_size(
        portfolio_value: float,
        risk_per_trade_pct: float,
        entry_price: float,
        stop_loss: float
) -> int:
    """
    Calculate position size based on risk

    Args:
        portfolio_value: Total portfolio value
        risk_per_trade_pct: Risk percentage per trade
        entry_price: Entry price
        stop_loss: Stop loss price

    Returns:
        Position size (number of units)
    """
    risk_amount = portfolio_value * (risk_per_trade_pct / 100)
    price_risk = abs(entry_price - stop_loss)

    if price_risk == 0:
        return 0

    position_size = int(risk_amount / price_risk)
    return position_size


def round_to_tick_size(price: float, tick_size: float = 0.05) -> float:
    """Round price to tick size"""
    return round(price / tick_size) * tick_size


def calculate_gap_percent(previous_close: float, current_open: float) -> float:
    """Calculate gap percentage"""
    if previous_close == 0:
        return 0
    return ((current_open - previous_close) / previous_close) * 100


def format_time_duration(seconds: int) -> str:
    """Format seconds into readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def is_within_execution_window(
        current_time: time,
        start_hour: int = 9,
        start_minute: int = 15,
        end_hour: int = 9,
        end_minute: int = 20
) -> bool:
    """Check if current time is within execution window"""
    start = time(start_hour, start_minute)
    end = time(end_hour, end_minute)
    return start <= current_time < end


def calculate_risk_reward_ratio(entry: float, stop: float, target: float) -> float:
    """Calculate risk-reward ratio"""
    risk = abs(entry - stop)
    reward = abs(target - entry)

    if risk == 0:
        return 0

    return reward / risk


if __name__ == "__main__":
    print("Helper Functions Test")
    print("=" * 60)

    # Test market open check
    is_open, reason = is_market_open()
    print(f"\nMarket Status: {is_open}")
    print(f"Reason: {reason}")

    # Test current time
    current_time = get_current_ist_time()
    print(f"\nCurrent IST Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Test currency formatting
    print(f"\nCurrency Format: {format_currency(123456.789)}")

    # Test position sizing
    portfolio = 100000
    risk_pct = 0.5
    entry = 21500
    stop = 21450

    size = calculate_position_size(portfolio, risk_pct, entry, stop)
    print(f"\nPosition Size: {size} units")
    print(f"  Portfolio: {format_currency(portfolio)}")
    print(f"  Risk: {risk_pct}%")
    print(f"  Entry: {entry}, Stop: {stop}")

    # Test risk-reward
    target = 21575
    rr = calculate_risk_reward_ratio(entry, stop, target)
    print(f"\nRisk-Reward Ratio: 1:{rr:.2f}")

    print("\n" + "=" * 60)