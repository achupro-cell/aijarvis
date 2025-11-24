#!/usr/bin/env python3
"""
Demo script to test the indicator service
"""
import requests
import time
import numpy as np
import json

def generate_sample_data(n=100):
    """Generate sample OHLCV data"""
    np.random.seed(42)
    
    # Generate realistic price data
    close_prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high_prices = close_prices + np.random.rand(n) * 2
    low_prices = close_prices - np.random.rand(n) * 2
    volumes = np.random.randint(1000, 10000, n)
    
    return {
        "high": high_prices.tolist(),
        "low": low_prices.tolist(),
        "close": close_prices.tolist(),
        "volume": volumes.tolist()
    }

def test_rest_api():
    """Test REST API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Indicator Service REST API")
    print("=" * 50)
    
    # Test health check
    print("\n1. Health Check:")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print(f"✓ Service is healthy: {response.json()}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to service. Make sure it's running on port 8000")
        return
    
    # Test single indicator
    print("\n2. Single Indicator (Firefly):")
    data = generate_sample_data(50)  # Use 50 data points
    payload = {
        "high": data["high"],
        "low": data["low"],
        "close": data["close"],
        "indicators": ["firefly"]
    }
    
    start_time = time.time()
    response = requests.post(f"{base_url}/calculate", json=payload)
    process_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Firefly calculated in {process_time:.3f}s")
        print(f"  Input length: {result['data']['input_length']}")
        
        # Handle None values in oscillator range
        oscillator = result['data']['indicators']['firefly']['oscillator']
        finite_osc = [x for x in oscillator if x is not None]
        if finite_osc:
            print(f"  Oscillator range: {min(finite_osc):.2f} - {max(finite_osc):.2f}")
        else:
            print(f"  Oscillator range: No finite values")
    else:
        print(f"✗ Firefly calculation failed: {response.status_code}")
    
    # Test multiple indicators
    print("\n3. Multiple Indicators (All):")
    payload = {
        "high": data["high"],
        "low": data["low"],
        "close": data["close"],
        "volume": data["volume"],
        "indicators": ["firefly", "sqzmom", "stai"]
    }
    
    start_time = time.time()
    response = requests.post(f"{base_url}/calculate", json=payload)
    process_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ All indicators calculated in {process_time:.3f}s")
        print(f"  Indicators: {list(result['data']['indicators'].keys())}")
        
        # Show composite signals
        composite = result['data']['composite_signals']
        buy_signals = sum(composite['buy_signal'])
        sell_signals = sum(composite['sell_signal'])
        neutral_signals = sum(composite['neutral_signal'])
        
        print(f"  Composite signals:")
        print(f"    Buy: {buy_signals}")
        print(f"    Sell: {sell_signals}")
        print(f"    Neutral: {neutral_signals}")
    else:
        print(f"✗ Multiple indicators calculation failed: {response.status_code}")
    
    # Test performance with 500 candles
    print("\n4. Performance Test (500 candles):")
    data_500 = generate_sample_data(500)
    payload = {
        "high": data_500["high"],
        "low": data_500["low"],
        "close": data_500["close"],
        "volume": data_500["volume"],
        "indicators": ["firefly", "sqzmom", "stai"]
    }
    
    start_time = time.time()
    response = requests.post(f"{base_url}/calculate", json=payload)
    process_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        if process_time < 0.1:
            print(f"✓ Performance test passed: {process_time:.3f}s (< 100ms)")
        else:
            print(f"⚠ Performance test warning: {process_time:.3f}s (should be < 100ms)")
        print(f"  Processed {result['data']['input_length']} candles")
    else:
        print(f"✗ Performance test failed: {response.status_code}")
    
    # Test cache endpoint
    print("\n5. Cache Test:")
    response = requests.get(f"{base_url}/cache/firefly")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Cache endpoint working")
        print(f"  Last updated: {result['data']['timestamp']}")
        print(f"  Data length: {result['data']['data_length']}")
    else:
        print(f"✗ Cache test failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 REST API testing complete!")

def test_direct_indicators():
    """Test indicators directly without API"""
    print("\n🔬 Testing Indicators Directly")
    print("=" * 50)
    
    try:
        from indicators import FireflyOscillator, SQZMOMCombo, STAIV6
        
        # Generate test data
        np.random.seed(42)
        n = 100
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.random.rand(n) * 2
        low = close - np.random.rand(n) * 2
        volume = np.random.randint(1000, 10000, n)
        
        # Test Firefly
        print("\n1. Firefly Oscillator:")
        firefly = FireflyOscillator()
        start_time = time.time()
        result = firefly.calculate(high, low, close)
        process_time = time.time() - start_time
        
        print(f"✓ Calculated in {process_time:.3f}s")
        oscillator = result['oscillator']
        finite_osc = oscillator[~np.isnan(oscillator)]
        if len(finite_osc) > 0:
            print(f"  Oscillator range: {min(finite_osc):.2f} - {max(finite_osc):.2f}")
        else:
            print(f"  Oscillator range: No finite values")
        print(f"  Buy signals: {sum(result['buy_signal'])}")
        print(f"  Sell signals: {sum(result['sell_signal'])}")
        
        # Test SQZMOM
        print("\n2. SQZMOM Combo:")
        sqzmom = SQZMOMCombo()
        start_time = time.time()
        result = sqzmom.calculate(high, low, close, volume)
        process_time = time.time() - start_time
        
        print(f"✓ Calculated in {process_time:.3f}s")
        print(f"  Squeeze periods: {sum(result['squeeze_on'])}")
        print(f"  Buy signals: {sum(result['buy_signal'])}")
        print(f"  Sell signals: {sum(result['sell_signal'])}")
        
        # Test STAI
        print("\n3. STAI v6:")
        stai = STAIV6()
        start_time = time.time()
        result = stai.calculate(high, low, close)
        process_time = time.time() - start_time
        
        print(f"✓ Calculated in {process_time:.3f}s")
        stai_score = result['stai_score']
        rsi = result['rsi']
        finite_stai = stai_score[~np.isnan(stai_score)]
        finite_rsi = rsi[~np.isnan(rsi)]
        if len(finite_stai) > 0:
            print(f"  STAI score range: {min(finite_stai):.2f} - {max(finite_stai):.2f}")
        else:
            print(f"  STAI score range: No finite values")
        if len(finite_rsi) > 0:
            print(f"  RSI range: {min(finite_rsi):.2f} - {max(finite_rsi):.2f}")
        else:
            print(f"  RSI range: No finite values")
        print(f"  Buy signals: {sum(result['buy_signal'])}")
        print(f"  Sell signals: {sum(result['sell_signal'])}")
        
    except Exception as e:
        print(f"✗ Error testing indicators directly: {e}")

def main():
    """Main demo function"""
    print("🎯 Indicator Service Demo")
    print("This demo tests both the REST API and direct indicator calculations")
    
    # Test indicators directly first
    test_direct_indicators()
    
    # Then test REST API
    test_rest_api()
    
    print("\n📝 Demo Notes:")
    print("- The service should respond in <100ms for 500 candles")
    print("- All indicators return deterministic values for the same input")
    print("- Composite signals aggregate individual indicator signals")
    print("- Cache stores the latest calculation results for quick access")

if __name__ == '__main__':
    main()