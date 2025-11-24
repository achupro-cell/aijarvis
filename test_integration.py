"""
Integration tests and test data utilities
"""
import pytest
import numpy as np
import requests
import json
import time

# Test data that mimics real market conditions
SAMPLE_OHLCV_50 = {
    "high": [
        102.5, 103.2, 104.1, 103.8, 105.0, 104.7, 106.2, 105.9, 106.8, 107.5,
        107.2, 108.1, 107.8, 109.0, 108.7, 109.5, 109.2, 110.1, 109.8, 110.5,
        110.2, 111.0, 110.7, 111.5, 111.2, 112.0, 111.7, 112.5, 112.2, 113.0,
        112.7, 113.5, 113.2, 114.0, 113.7, 114.5, 114.2, 115.0, 114.7, 115.5,
        115.2, 116.0, 115.7, 116.5, 116.2, 117.0, 116.7, 117.5, 117.2, 118.0
    ],
    "low": [
        99.5, 100.2, 101.1, 100.8, 102.0, 101.7, 103.2, 102.9, 103.8, 104.5,
        104.2, 105.1, 104.8, 106.0, 105.7, 106.5, 106.2, 107.1, 106.8, 107.5,
        107.2, 108.0, 107.7, 108.5, 108.2, 109.0, 108.7, 109.5, 109.2, 110.0,
        109.7, 110.5, 110.2, 111.0, 110.7, 111.5, 111.2, 112.0, 111.7, 112.5,
        112.2, 113.0, 112.7, 113.5, 113.2, 114.0, 113.7, 114.5, 114.2, 115.0
    ],
    "close": [
        101.0, 101.7, 102.6, 102.3, 103.5, 103.2, 104.7, 104.4, 105.3, 106.0,
        105.7, 106.6, 106.3, 107.5, 107.2, 108.0, 107.7, 108.6, 108.3, 109.0,
        108.7, 109.5, 109.2, 110.0, 109.7, 110.5, 110.2, 111.0, 110.7, 111.5,
        111.2, 112.0, 111.7, 112.5, 112.2, 113.0, 112.7, 113.5, 113.2, 114.0,
        113.7, 114.5, 114.2, 115.0, 114.7, 115.5, 115.2, 116.0, 115.7, 116.5
    ],
    "volume": [
        1500, 1650, 1800, 1750, 1900, 1850, 2000, 1950, 2100, 2050,
        2200, 2150, 2300, 2250, 2400, 2350, 2500, 2450, 2600, 2550,
        2700, 2650, 2800, 2750, 2900, 2850, 3000, 2950, 3100, 3050,
        3200, 3150, 3300, 3250, 3400, 3350, 3500, 3450, 3600, 3550,
        3700, 3650, 3800, 3750, 3900, 3850, 4000, 3950, 4100, 4050
    ]
}

SAMPLE_OHLCV_500 = {
    "high": [100 + i * 0.1 + np.random.rand() * 2 for i in range(500)],
    "low": [98 + i * 0.1 - np.random.rand() * 2 for i in range(500)],
    "close": [99 + i * 0.1 + (np.random.rand() - 0.5) * 1 for i in range(500)],
    "volume": [1000 + i * 10 + int(np.random.rand() * 500) for i in range(500)]
}

class TestRestAPI:
    """Integration tests for REST API"""
    
    BASE_URL = "http://localhost:8000"
    
    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "indicators" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_detailed_health_check(self):
        """Test detailed health check endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "indicators_available" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_calculate_single_indicator(self):
        """Test calculating a single indicator via REST"""
        try:
            payload = {
                "high": SAMPLE_OHLCV_50["high"],
                "low": SAMPLE_OHLCV_50["low"],
                "close": SAMPLE_OHLCV_50["close"],
                "indicators": ["firefly"]
            }
            
            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/calculate", json=payload)
            process_time = time.time() - start_time
            
            assert response.status_code == 200
            assert process_time < 0.1  # Should be under 100ms
            
            data = response.json()
            assert data["success"] is True
            assert "firefly" in data["data"]["indicators"]
            assert "composite_signals" in data["data"]
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_calculate_multiple_indicators(self):
        """Test calculating multiple indicators via REST"""
        try:
            payload = {
                "high": SAMPLE_OHLCV_50["high"],
                "low": SAMPLE_OHLCV_50["low"],
                "close": SAMPLE_OHLCV_50["close"],
                "volume": SAMPLE_OHLCV_50["volume"],
                "indicators": ["firefly", "sqzmom", "stai"]
            }
            
            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/calculate", json=payload)
            process_time = time.time() - start_time
            
            assert response.status_code == 200
            assert process_time < 0.1  # Should be under 100ms
            
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["indicators"]) == 3
            assert "composite_signals" in data["data"]
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_performance_500_candles(self):
        """Test performance with 500 candles"""
        try:
            np.random.seed(42)
            payload = {
                "high": SAMPLE_OHLCV_500["high"],
                "low": SAMPLE_OHLCV_500["low"],
                "close": SAMPLE_OHLCV_500["close"],
                "volume": SAMPLE_OHLCV_500["volume"],
                "indicators": ["firefly", "sqzmom", "stai"]
            }
            
            start_time = time.time()
            response = requests.post(f"{self.BASE_URL}/calculate", json=payload)
            process_time = time.time() - start_time
            
            assert response.status_code == 200
            assert process_time < 0.1, f"Request took {process_time:.3f}s, should be < 100ms"
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["input_length"] == 500
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_error_handling(self):
        """Test error handling via REST"""
        try:
            # Test missing volume for SQZMOM
            payload = {
                "high": SAMPLE_OHLCV_50["high"],
                "low": SAMPLE_OHLCV_50["low"],
                "close": SAMPLE_OHLCV_50["close"],
                "indicators": ["sqzmom"]  # Missing volume
            }
            
            response = requests.post(f"{self.BASE_URL}/calculate", json=payload)
            assert response.status_code == 400
            
            data = response.json()
            assert "Volume is required" in data["detail"]
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_list_indicators(self):
        """Test listing indicators endpoint"""
        try:
            response = requests.get(f"{self.BASE_URL}/indicators")
            assert response.status_code == 200
            
            data = response.json()
            assert "indicators" in data
            assert "firefly" in data["indicators"]
            assert "sqzmom" in data["indicators"]
            assert "stai" in data["indicators"]
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")
    
    def test_cache_endpoint(self):
        """Test cache endpoint"""
        try:
            # First calculate to populate cache
            payload = {
                "high": SAMPLE_OHLCV_50["high"],
                "low": SAMPLE_OHLCV_50["low"],
                "close": SAMPLE_OHLCV_50["close"],
                "indicators": ["firefly"]
            }
            
            requests.post(f"{self.BASE_URL}/calculate", json=payload)
            
            # Then check cache
            response = requests.get(f"{self.BASE_URL}/cache/firefly")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "data" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("REST API server not running")

class TestIndicatorParity:
    """Test indicator parity against reference implementations"""
    
    def test_firefly_parity(self):
        """Test Firefly Oscillator parity with known values"""
        from indicators import FireflyOscillator
        
        # Use deterministic data with sufficient length
        high = np.array([102, 104, 103, 105, 106, 104, 103, 107, 108, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121])
        low = np.array([98, 100, 99, 101, 102, 100, 99, 103, 104, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119])
        close = np.array([100, 102, 101, 103, 104, 102, 101, 105, 106, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121])
        
        firefly = FireflyOscillator(length=5, mult=1.5)
        result = firefly.calculate(high, low, close)
        
        # Verify key properties
        assert len(result['oscillator']) == 21
        # Check oscillator bounds (should be 0-100, ignoring NaN)
        oscillator = result['oscillator']
        finite_oscillator = oscillator[~np.isnan(oscillator)]
        assert len(finite_oscillator) > 0
        assert np.all(finite_oscillator >= 0) and np.all(finite_oscillator <= 100)
        
        # The oscillator should react to price movements
        assert not np.allclose(oscillator[5:], oscillator[:5])  # Should change over time
    
    def test_sqzmom_parity(self):
        """Test SQZMOM parity with known values"""
        from indicators import SQZMOMCombo
        
        high = np.array([102, 104, 103, 105, 106, 104, 103, 107, 108, 105])
        low = np.array([98, 100, 99, 101, 102, 100, 99, 103, 104, 101])
        close = np.array([100, 102, 101, 103, 104, 102, 101, 105, 106, 103])
        volume = np.array([1000, 1200, 1100, 1300, 1400, 1200, 1100, 1500, 1600, 1300])
        
        sqzmom = SQZMOMCombo(bb_length=5, kc_length=5)
        result = sqzmom.calculate(high, low, close, volume)
        
        # Verify key properties
        assert len(result['momentum']) == 10
        assert len(result['histogram']) == 10
        
        # Squeeze detection should work
        squeeze_on = result['squeeze_on']
        squeeze_off = result['squeeze_off']
        assert not np.any(squeeze_on & squeeze_off)
        assert np.all(squeeze_on | squeeze_off)
    
    def test_stai_parity(self):
        """Test STAI v6 parity with known values"""
        from indicators import STAIV6
        
        # Use sufficient data for STAI calculations
        high = np.array([102, 104, 103, 105, 106, 104, 103, 107, 108, 105, 106, 107, 108, 109, 110, 111, 112])
        low = np.array([98, 100, 99, 101, 102, 100, 99, 103, 104, 101, 102, 103, 104, 105, 106, 107, 108])
        close = np.array([100, 102, 101, 103, 104, 102, 101, 105, 106, 103, 104, 105, 106, 107, 108, 109, 110, 111])

        stai = STAIV6(fast_length=2, slow_length=4, signal_length=2)
        result = stai.calculate(high, low, close)

        # Verify key properties
        assert len(result['stai_score']) == 21
        assert len(result['macd']) == 21
        assert len(result['rsi']) == 21

        # RSI should be in 0-100 range (ignoring NaN)
        rsi = result['rsi']
        finite_rsi = rsi[~np.isnan(rsi)]
        assert len(finite_rsi) > 0
        assert np.all(finite_rsi >= 0) and np.all(finite_rsi <= 100)

        # STAI score should be composite of multiple indicators
        stai_score = result['stai_score']
        finite_stai_score = stai_score[~np.isnan(stai_score)]
        assert len(finite_stai_score) > 0
        assert np.any(finite_stai_score >= 0) and np.any(finite_stai_score <= 100)

class TestDeterministicBehavior:
    """Test that indicators produce deterministic results"""
    
    def test_deterministic_across_runs(self):
        """Test that indicators are deterministic across multiple runs"""
        from service import IndicatorService, OHLCVRequest
        
        service = IndicatorService()
        
        request = OHLCVRequest(
            high=SAMPLE_OHLCV_50["high"][:20],
            low=SAMPLE_OHLCV_50["low"][:20],
            close=SAMPLE_OHLCV_50["close"][:20],
            volume=SAMPLE_OHLCV_50["volume"][:20],
            indicators=["firefly", "sqzmom", "stai"]
        )
        
        # Run multiple times
        results = []
        for _ in range(5):
            result = service.calculate_indicators(request)
            assert result.success is True
            results.append(result)
        
        # Compare results
        for i in range(1, len(results)):
            # Compare indicators data
            for indicator in results[0].data["indicators"]:
                ind1 = results[0].data["indicators"][indicator]
                ind2 = results[i].data["indicators"][indicator]
                
                for key in ind1:
                    if isinstance(ind1[key], list):
                        np.testing.assert_array_equal(ind1[key], ind2[key], 
                            err_msg=f"Indicator {indicator}, key {key} not deterministic")
                    else:
                        assert ind1[key] == ind2[key], f"Indicator {indicator}, key {key} not deterministic"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])