# config/breadth_basket.py

"""
Stock basket for market breadth calculation
Using liquid Nifty 50 stocks
"""

# Top 30 Nifty stocks for breadth calculation (liquid & representative)
BREADTH_BASKET = {
    # IT Sector
    'TCS': 'NSE:TCS-EQ',
    'INFY': 'NSE:INFY-EQ',
    'HCLTECH': 'NSE:HCLTECH-EQ',
    'WIPRO': 'NSE:WIPRO-EQ',
    'TECHM': 'NSE:TECHM-EQ',

    # Banking
    'HDFCBANK': 'NSE:HDFCBANK-EQ',
    'ICICIBANK': 'NSE:ICICIBANK-EQ',
    'KOTAKBANK': 'NSE:KOTAKBANK-EQ',
    'AXISBANK': 'NSE:AXISBANK-EQ',
    'SBIN': 'NSE:SBIN-EQ',

    # Energy
    'RELIANCE': 'NSE:RELIANCE-EQ',
    'ONGC': 'NSE:ONGC-EQ',
    'BPCL': 'NSE:BPCL-EQ',
    'IOC': 'NSE:IOC-EQ',

    # Automobiles
    'MARUTI': 'NSE:MARUTI-EQ',
    'M&M': 'NSE:M&M-EQ',
    'TATAMOTORS': 'NSE:TATAMOTORS-EQ',
    'BAJAJ-AUTO': 'NSE:BAJAJ-AUTO-EQ',

    # FMCG
    'HINDUNILVR': 'NSE:HINDUNILVR-EQ',
    'ITC': 'NSE:ITC-EQ',
    'NESTLEIND': 'NSE:NESTLEIND-EQ',
    'BRITANNIA': 'NSE:BRITANNIA-EQ',

    # Pharma
    'SUNPHARMA': 'NSE:SUNPHARMA-EQ',
    'DRREDDY': 'NSE:DRREDDY-EQ',
    'CIPLA': 'NSE:CIPLA-EQ',

    # Metals
    'TATASTEEL': 'NSE:TATASTEEL-EQ',
    'HINDALCO': 'NSE:HINDALCO-EQ',
    'JSWSTEEL': 'NSE:JSWSTEEL-EQ',

    # Telecom
    'BHARTIARTL': 'NSE:BHARTIARTL-EQ',

    # Infrastructure
    'LT': 'NSE:LT-EQ'
}


def get_breadth_symbols():
    """Get list of symbols for breadth calculation"""
    return list(BREADTH_BASKET.values())


def get_breadth_symbol_names():
    """Get list of symbol names"""
    return list(BREADTH_BASKET.keys())


# Smaller basket for faster calculation (top 15 liquid stocks)
BREADTH_BASKET_QUICK = {
    'TCS': 'NSE:TCS-EQ',
    'INFY': 'NSE:INFY-EQ',
    'RELIANCE': 'NSE:RELIANCE-EQ',
    'HDFCBANK': 'NSE:HDFCBANK-EQ',
    'ICICIBANK': 'NSE:ICICIBANK-EQ',
    'SBIN': 'NSE:SBIN-EQ',
    'HINDUNILVR': 'NSE:HINDUNILVR-EQ',
    'ITC': 'NSE:ITC-EQ',
    'KOTAKBANK': 'NSE:KOTAKBANK-EQ',
    'LT': 'NSE:LT-EQ',
    'AXISBANK': 'NSE:AXISBANK-EQ',
    'MARUTI': 'NSE:MARUTI-EQ',
    'SUNPHARMA': 'NSE:SUNPHARMA-EQ',
    'TATASTEEL': 'NSE:TATASTEEL-EQ',
    'BHARTIARTL': 'NSE:BHARTIARTL-EQ'
}


def get_quick_breadth_symbols():
    """Get smaller basket for quick breadth calculation"""
    return list(BREADTH_BASKET_QUICK.values())


if __name__ == "__main__":
    print("Market Breadth Basket Configuration")
    print("=" * 60)
    print(f"\nFull Basket: {len(BREADTH_BASKET)} stocks")
    print(f"Quick Basket: {len(BREADTH_BASKET_QUICK)} stocks")

    print("\nFull Basket Symbols:")
    for name, symbol in list(BREADTH_BASKET.items())[:5]:
        print(f"  {name}: {symbol}")
    print(f"  ... and {len(BREADTH_BASKET) - 5} more")