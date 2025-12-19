# config/symbols.py

"""
Symbol configuration for MMFS strategy
"""

# MMFS Trading Symbols
MMFS_SYMBOLS = {
    # Index Options (Primary instruments for MMFS)
    'NIFTY': {
        'symbol': 'NSE:NIFTY50-INDEX',
        'exchange': 'NSE',
        'segment': 'INDEX',
        'lot_size': 50,
        'type': 'INDEX',
        'tick_size': 0.05,
        'priority': 1
    },
    'BANKNIFTY': {
        'symbol': 'NSE:NIFTY BANK-INDEX',
        'exchange': 'NSE',
        'segment': 'INDEX',
        'lot_size': 30,
        'type': 'INDEX',
        'tick_size': 0.05,
        'priority': 2
    },
    'FINNIFTY': {
        'symbol': 'NSE:NIFTY FIN SERVICE-INDEX',
        'exchange': 'NSE',
        'segment': 'INDEX',
        'lot_size': 60,
        'type': 'INDEX',
        'tick_size': 0.05,
        'priority': 3
    },

    # Index Futures
    'NIFTY_FUT': {
        'symbol': 'NSE:NIFTY50-INDEX',
        'exchange': 'NSE',
        'segment': 'FUTURE',
        'lot_size': 50,
        'type': 'FUTURE',
        'tick_size': 0.05,
        'priority': 4
    },
    'BANKNIFTY_FUT': {
        'symbol': 'NSE:NIFTY BANK-INDEX',
        'exchange': 'NSE',
        'segment': 'FUTURE',
        'lot_size': 30,
        'type': 'FUTURE',
        'tick_size': 0.05,
        'priority': 5
    },

    # Top F&O Stocks (Secondary instruments)
    'RELIANCE': {
        'symbol': 'NSE:RELIANCE-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 250,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 10
    },
    'TCS': {
        'symbol': 'NSE:TCS-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 150,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 11
    },
    'HDFCBANK': {
        'symbol': 'NSE:HDFCBANK-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 550,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 12
    },
    'INFY': {
        'symbol': 'NSE:INFY-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 300,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 13
    },
    'ICICIBANK': {
        'symbol': 'NSE:ICICIBANK-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 1100,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 14
    },
    'SBIN': {
        'symbol': 'NSE:SBIN-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 1500,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 15
    },
    'HINDUNILVR': {
        'symbol': 'NSE:HINDUNILVR-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 300,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 16
    },
    'ITC': {
        'symbol': 'NSE:ITC-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 1600,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 17
    },
    'KOTAKBANK': {
        'symbol': 'NSE:KOTAKBANK-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 400,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 18
    },
    'LT': {
        'symbol': 'NSE:LT-EQ',
        'exchange': 'NSE',
        'segment': 'EQUITY',
        'lot_size': 300,
        'type': 'STOCK',
        'tick_size': 0.05,
        'priority': 19
    },
}

# Symbol groups for different trading strategies
SYMBOL_GROUPS = {
    'INDICES': ['NIFTY', 'BANKNIFTY', 'FINNIFTY'],
    'INDEX_FUTURES': ['NIFTY_FUT', 'BANKNIFTY_FUT'],
    'STOCKS': ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
               'SBIN', 'HINDUNILVR', 'ITC', 'KOTAKBANK', 'LT'],
    'PRIMARY': ['NIFTY', 'BANKNIFTY'],  # Primary focus for MMFS
    'SECONDARY': ['FINNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK']  # Secondary
}


def get_mmfs_symbols():
    """Get all MMFS trading symbols"""
    return MMFS_SYMBOLS


def get_symbol_by_name(name: str):
    """Get symbol configuration by name"""
    return MMFS_SYMBOLS.get(name.upper())


def get_symbols_by_group(group_name: str):
    """Get symbols belonging to a specific group"""
    if group_name not in SYMBOL_GROUPS:
        return []

    symbol_names = SYMBOL_GROUPS[group_name]
    return {name: MMFS_SYMBOLS[name] for name in symbol_names if name in MMFS_SYMBOLS}


def get_primary_symbols():
    """Get primary trading symbols"""
    return get_symbols_by_group('PRIMARY')


def get_all_symbol_names():
    """Get list of all symbol names"""
    return list(MMFS_SYMBOLS.keys())


def format_symbol_for_fyers(symbol_name: str):
    """Format symbol name for Fyers API"""
    config = get_symbol_by_name(symbol_name)
    if config:
        return config['symbol']
    return None


if __name__ == "__main__":
    print("MMFS Symbol Configuration")
    print("=" * 60)

    print("\nPrimary Symbols:")
    for name, config in get_primary_symbols().items():
        print(f"  {name}: {config['symbol']} (Lot: {config['lot_size']})")

    print("\nAll Symbol Groups:")
    for group, symbols in SYMBOL_GROUPS.items():
        print(f"  {group}: {', '.join(symbols)}")

    print("\nTotal Symbols:", len(MMFS_SYMBOLS))