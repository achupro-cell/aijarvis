import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_demo_data(n_records=1000):
    """Create demo OHLCV data for testing"""
    
    # Generate timestamps
    end_time = datetime.now()
    timestamps = [end_time - timedelta(hours=i) for i in range(n_records-1, -1, -1)]
    
    # Generate price data with random walk
    np.random.seed(42)
    base_price = 50000  # Starting price for BTC
    
    # Random walk with trend
    returns = np.random.normal(0.0001, 0.02, n_records)  # Small positive trend with volatility
    prices = [base_price]
    
    for i in range(1, n_records):
        prices.append(prices[-1] * (1 + returns[i]))
    
    # Create OHLCV data
    data = []
    for i, timestamp in enumerate(timestamps):
        close_price = prices[i]
        
        # Generate realistic OHLC
        volatility = 0.01  # 1% intraday volatility
        
        high = close_price * (1 + np.random.uniform(0, volatility))
        low = close_price * (1 - np.random.uniform(0, volatility))
        
        # Ensure O is within H-L range
        open_price = np.random.uniform(low, high)
        
        # Generate volume (correlated with price movement)
        volume_base = 1000
        volume_variation = abs(returns[i]) * 10  # Higher volume with higher price movement
        volume = volume_base * (1 + volume_variation) * np.random.uniform(0.5, 2.0)
        
        data.append({
            'open_time': timestamp,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': round(volume, 2),
            'close_time': timestamp + timedelta(hours=1),
            'quote_asset_volume': round(volume * close_price, 2),
            'number_of_trades': int(np.random.uniform(100, 1000)),
            'taker_buy_base_asset_volume': round(volume * 0.5, 2),
            'taker_buy_quote_asset_volume': round(volume * 0.5 * close_price, 2),
            'ignore': 0
        })
    
    return pd.DataFrame(data)

def save_demo_data():
    """Save demo data to files"""
    df = create_demo_data(2000)  # Create ~83 days of hourly data
    
    # Save as CSV for easy access
    df.to_csv('demo_btcusdt_1h.csv', index=False)
    print(f"Demo data saved: {len(df)} records")
    print(f"Date range: {df['open_time'].min()} to {df['open_time'].max()}")
    
    return df

if __name__ == "__main__":
    df = save_demo_data()
    print("\nSample data:")
    print(df[['open_time', 'open', 'high', 'low', 'close', 'volume']].head())