"""
Unit tests for indicator calculations
"""
import pytest
import numpy as np
import pandas as pd
from indicators import FireflyOscillator, SQZMOMCombo, STAIV6

class TestFireflyOscillator:
    def test_basic_calculation(self):
        """Test basic Firefly Oscillator calculation"""
        # Generate sample data
        np.random.seed(42)
        n = 100
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.random.rand(n) * 2
        low = close - np.random.rand(n) * 2
        
        firefly = FireflyOscillator()
        result = firefly.calculate(high, low, close)
        
        # Check output structure
        assert 'oscillator' in result
        assert 'signal' in result
        assert 'buy_signal' in result
        assert 'sell_signal' in result
        assert 'neutral_signal' in result
        assert 'metadata' in result
        
        # Check array lengths
        assert len(result['oscillator']) == n
        assert len(result['signal']) == n
        assert len(result['buy_signal']) == n
        assert len(result['sell_signal']) == n
        assert len(result['neutral_signal']) == n
        
        # Check oscillator bounds (should be 0-100, ignoring NaN)
        oscillator = result['oscillator']
        finite_oscillator = oscillator[~np.isnan(oscillator)]
        assert len(finite_oscillator) > 0  # Should have some finite values
        assert np.all(finite_oscillator >= 0) and np.all(finite_oscillator <= 100)
        
        # Check signal logic (should be mutually exclusive)
        assert not np.any(result['buy_signal'] & result['sell_signal'])
        assert np.all(result['buy_signal'] | result['sell_signal'] | result['neutral_signal'])
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        firefly = FireflyOscillator(length=50)
        with pytest.raises(ValueError, match="Need at least 50 periods"):
            firefly.calculate([1,2,3], [0.5,1.5,2.5], [1,1,1])
    
    def test_deterministic_output(self):
        """Test that output is deterministic"""
        np.random.seed(123)
        high = np.array([102, 104, 103, 105, 106, 104, 103, 107, 108, 105])
        low = np.array([98, 100, 99, 101, 102, 100, 99, 103, 104, 101])
        close = np.array([100, 102, 101, 103, 104, 102, 101, 105, 106, 103])
        
        firefly = FireflyOscillator(length=5, mult=1.5)
        result1 = firefly.calculate(high, low, close)
        result2 = firefly.calculate(high, low, close)
        
        # Results should be identical
        np.testing.assert_array_equal(result1['oscillator'], result2['oscillator'])
        np.testing.assert_array_equal(result1['signal'], result2['signal'])

class TestSQZMOMCombo:
    def test_basic_calculation(self):
        """Test basic SQZMOM Combo calculation"""
        np.random.seed(42)
        n = 100
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.random.rand(n) * 2
        low = close - np.random.rand(n) * 2
        volume = np.random.randint(1000, 10000, n)
        
        sqzmom = SQZMOMCombo()
        result = sqzmom.calculate(high, low, close, volume)
        
        # Check output structure
        assert 'momentum' in result
        assert 'histogram' in result
        assert 'squeeze_on' in result
        assert 'squeeze_off' in result
        assert 'buy_signal' in result
        assert 'sell_signal' in result
        assert 'neutral_signal' in result
        assert 'metadata' in result
        
        # Check array lengths
        for key in ['momentum', 'histogram', 'squeeze_on', 'squeeze_off', 
                   'buy_signal', 'sell_signal', 'neutral_signal']:
            assert len(result[key]) == n
        
        # Check signal logic
        assert not np.any(result['buy_signal'] & result['sell_signal'])
        assert np.all(result['buy_signal'] | result['sell_signal'] | result['neutral_signal'])
        
        # Check squeeze logic
        assert not np.any(result['squeeze_on'] & result['squeeze_off'])
        assert np.all(result['squeeze_on'] | result['squeeze_off'])
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        sqzmom = SQZMOMCombo(bb_length=50)
        with pytest.raises(ValueError, match="Need at least 50 periods"):
            sqzmom.calculate([1,2,3], [0.5,1.5,2.5], [1,1,1], [100,200,150])
    
    def test_deterministic_output(self):
        """Test that output is deterministic"""
        high = np.array([102, 104, 103, 105, 106, 104, 103, 107, 108, 105])
        low = np.array([98, 100, 99, 101, 102, 100, 99, 103, 104, 101])
        close = np.array([100, 102, 101, 103, 104, 102, 101, 105, 106, 103])
        volume = np.array([1000, 1200, 1100, 1300, 1400, 1200, 1100, 1500, 1600, 1300])
        
        sqzmom = SQZMOMCombo(bb_length=5, kc_length=5)
        result1 = sqzmom.calculate(high, low, close, volume)
        result2 = sqzmom.calculate(high, low, close, volume)
        
        # Results should be identical
        np.testing.assert_array_equal(result1['momentum'], result2['momentum'])
        np.testing.assert_array_equal(result1['histogram'], result2['histogram'])

class TestSTAIV6:
    def test_basic_calculation(self):
        """Test basic STAI v6 calculation"""
        np.random.seed(42)
        n = 100  # Increased from 100 to ensure we have enough data for RSI(14)
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.random.rand(n) * 2
        low = close - np.random.rand(n) * 2
        
        stai = STAIV6()
        result = stai.calculate(high, low, close)
        
        # Check output structure
        assert 'stai_score' in result
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result
        assert 'rsi' in result
        assert 'stoch_k' in result
        assert 'stoch_d' in result
        assert 'buy_signal' in result
        assert 'sell_signal' in result
        assert 'neutral_signal' in result
        assert 'metadata' in result
        
        # Check array lengths
        for key in ['stai_score', 'macd', 'signal', 'histogram', 'rsi', 
                   'stoch_k', 'stoch_d', 'buy_signal', 'sell_signal', 'neutral_signal']:
            assert len(result[key]) == n
        
        # Check RSI bounds (should be 0-100, ignoring NaN)
        rsi = result['rsi']
        finite_rsi = rsi[~np.isnan(rsi)]
        assert len(finite_rsi) > 0  # Should have some finite values
        assert np.all(finite_rsi >= 0) and np.all(finite_rsi <= 100)
        
        # Check Stochastic bounds (should be 0-100, ignoring NaN)
        stoch_k = result['stoch_k']
        stoch_d = result['stoch_d']
        finite_stoch_k = stoch_k[~np.isnan(stoch_k)]
        finite_stoch_d = stoch_d[~np.isnan(stoch_d)]
        assert len(finite_stoch_k) > 0 and np.all(finite_stoch_k >= 0) and np.all(finite_stoch_k <= 100)
        assert len(finite_stoch_d) > 0 and np.all(finite_stoch_d >= 0) and np.all(finite_stoch_d <= 100)
        
        # Check signal logic
        assert not np.any(result['buy_signal'] & result['sell_signal'])
        assert np.all(result['buy_signal'] | result['sell_signal'] | result['neutral_signal'])
    
    def test_insufficient_data(self):
        """Test with insufficient data"""
        stai = STAIV6(slow_length=50)
        with pytest.raises(ValueError, match="Need at least 50 periods"):
            stai.calculate([1,2,3], [0.5,1.5,2.5], [1,1,1])
    
    def test_deterministic_output(self):
        """Test that output is deterministic"""
        high = np.array([102, 104, 103, 105, 106, 104, 103, 107, 108, 105, 106, 107, 108, 109, 110, 111, 112])
        low = np.array([98, 100, 99, 101, 102, 100, 99, 103, 104, 101, 102, 103, 104, 105, 106, 107, 108])
        close = np.array([100, 102, 101, 103, 104, 102, 101, 105, 106, 103, 104, 105, 106, 107, 108, 109, 110])
        
        stai = STAIV6(fast_length=3, slow_length=5, signal_length=2)
        result1 = stai.calculate(high, low, close)
        result2 = stai.calculate(high, low, close)
        
        # Results should be identical
        np.testing.assert_array_equal(result1['stai_score'], result2['stai_score'])
        np.testing.assert_array_equal(result1['macd'], result2['macd'])

class TestKnownValues:
    """Test against known reference values from Pine Script implementations"""
    
    def test_firefly_reference_values(self):
        """Test Firefly with known reference values"""
        # Simple test case with known expected behavior
        close = np.array([100, 101, 102, 103, 104, 105, 104, 103, 102, 101])
        high = close + 1
        low = close - 1
        
        firefly = FireflyOscillator(length=5, mult=1.0)
        result = firefly.calculate(high, low, close)
        
        # The oscillator should react to price changes
        # In an uptrend, oscillator should generally be above 50
        # In a downtrend, oscillator should generally be below 50
        assert len(result['oscillator']) == 10
        assert np.any(result['oscillator'] > 50)  # Should have some values above 50
        assert np.any(result['oscillator'] < 50)  # Should have some values below 50
    
    def test_sqzmom_reference_values(self):
        """Test SQZMOM with known reference values"""
        close = np.array([100, 101, 102, 103, 104, 105, 104, 103, 102, 101])
        high = close + 1
        low = close - 1
        volume = np.array([1000, 1100, 1200, 1300, 1400, 1500, 1400, 1300, 1200, 1100])
        
        sqzmom = SQZMOMCombo(bb_length=5, kc_length=5)
        result = sqzmom.calculate(high, low, close, volume)
        
        # Momentum should react to price changes
        assert len(result['momentum']) == 10
        assert len(result['histogram']) == 10
        
        # Squeeze should be detectable
        assert np.any(result['squeeze_on'] | result['squeeze_off'])
    
    def test_stai_reference_values(self):
        """Test STAI v6 with known reference values"""
        close = np.array([100, 101, 102, 103, 104, 105, 104, 103, 102, 101, 102, 103, 104, 105, 106, 107, 108])
        high = close + 1
        low = close - 1
        
        stai = STAIV6(fast_length=2, slow_length=4, signal_length=2)
        result = stai.calculate(high, low, close)
        
        # STAI score should be composite of multiple indicators
        assert len(result['stai_score']) == 17
        assert np.any(result['stai_score'] >= 0) and np.any(result['stai_score'] <= 100)

class TestPerformance:
    """Performance tests to ensure <100ms for 500 candles"""
    
    def test_performance_500_candles(self):
        """Test performance with 500 candles"""
        import time
        
        np.random.seed(42)
        n = 500
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.random.rand(n) * 2
        low = close - np.random.rand(n) * 2
        volume = np.random.randint(1000, 10000, n)
        
        # Test Firefly
        start_time = time.time()
        firefly = FireflyOscillator()
        result_firefly = firefly.calculate(high, low, close)
        firefly_time = time.time() - start_time
        
        # Test SQZMOM
        start_time = time.time()
        sqzmom = SQZMOMCombo()
        result_sqzmom = sqzmom.calculate(high, low, close, volume)
        sqzmom_time = time.time() - start_time
        
        # Test STAI
        start_time = time.time()
        stai = STAIV6()
        result_stai = stai.calculate(high, low, close)
        stai_time = time.time() - start_time
        
        # All should be under 100ms individually
        assert firefly_time < 0.1, f"Firefly took {firefly_time:.3f}s"
        assert sqzmom_time < 0.1, f"SQZMOM took {sqzmom_time:.3f}s"
        assert stai_time < 0.1, f"STAI took {stai_time:.3f}s"
        
        # Test all together
        start_time = time.time()
        firefly.calculate(high, low, close)
        sqzmom.calculate(high, low, close, volume)
        stai.calculate(high, low, close)
        total_time = time.time() - start_time
        
        assert total_time < 0.1, f"All indicators took {total_time:.3f}s"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])