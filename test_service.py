"""
Unit tests for the indicator service
"""
import pytest
import numpy as np
from service import IndicatorService, OHLCVRequest

class TestIndicatorService:
    def test_single_indicator_calculation(self):
        """Test calculating a single indicator"""
        service = IndicatorService()
        
        # Sample data
        np.random.seed(42)
        n = 50
        high = np.random.rand(n) * 10 + 100
        low = high - np.random.rand(n) * 5
        close = low + np.random.rand(n) * 3
        volume = np.random.randint(1000, 10000, n)
        
        request = OHLCVRequest(
            high=high.tolist(),
            low=low.tolist(),
            close=close.tolist(),
            volume=volume.tolist(),
            indicators=["firefly"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is True
        assert "firefly" in result.data["indicators"]
        assert "composite_signals" in result.data
        assert result.data["input_length"] == n
        
        firefly_data = result.data["indicators"]["firefly"]
        assert "oscillator" in firefly_data
        assert "buy_signal" in firefly_data
        assert "sell_signal" in firefly_data
        assert "neutral_signal" in firefly_data
    
    def test_multiple_indicators_calculation(self):
        """Test calculating multiple indicators"""
        service = IndicatorService()
        
        # Sample data
        np.random.seed(42)
        n = 50
        high = np.random.rand(n) * 10 + 100
        low = high - np.random.rand(n) * 5
        close = low + np.random.rand(n) * 3
        volume = np.random.randint(1000, 10000, n)
        
        request = OHLCVRequest(
            high=high.tolist(),
            low=low.tolist(),
            close=close.tolist(),
            volume=volume.tolist(),
            indicators=["firefly", "sqzmom", "stai"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is True
        assert len(result.data["indicators"]) == 3
        assert "firefly" in result.data["indicators"]
        assert "sqzmom" in result.data["indicators"]
        assert "stai" in result.data["indicators"]
        
        # Check composite signals
        composite = result.data["composite_signals"]
        assert "buy_signal" in composite
        assert "sell_signal" in composite
        assert "neutral_signal" in composite
        assert "methodology" in composite
    
    def test_sqzmom_requires_volume(self):
        """Test that SQZMOM requires volume data"""
        service = IndicatorService()
        
        request = OHLCVRequest(
            high=[100, 101, 102],
            low=[99, 100, 101],
            close=[99.5, 100.5, 101.5],
            volume=None,  # Missing volume
            indicators=["sqzmom"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is False
        assert "Volume is required for SQZMOM indicator" in result.data["error"]
    
    def test_invalid_input_lengths(self):
        """Test with mismatched input array lengths"""
        service = IndicatorService()
        
        request = OHLCVRequest(
            high=[100, 101, 102],  # 3 elements
            low=[99, 100],         # 2 elements - mismatch!
            close=[99.5, 100.5, 101.5],  # 3 elements
            indicators=["firefly"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is False
        assert "same length" in result.data["error"]
    
    def test_empty_data(self):
        """Test with empty data"""
        service = IndicatorService()
        
        request = OHLCVRequest(
            high=[],
            low=[],
            close=[],
            indicators=["firefly"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is False
        assert "Empty data" in result.data["error"]
    
    def test_unknown_indicator(self):
        """Test with unknown indicator name"""
        service = IndicatorService()
        
        request = OHLCVRequest(
            high=[100, 101, 102],
            low=[99, 100, 101],
            close=[99.5, 100.5, 101.5],
            indicators=["unknown_indicator"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is False
        assert "Unknown indicator" in result.data["error"]
    
    def test_case_insensitive_indicators(self):
        """Test that indicator names are case insensitive"""
        service = IndicatorService()
        
        # Generate sufficient data for all indicators
        np.random.seed(42)
        n = 50
        high = np.random.rand(n) * 10 + 100
        low = high - np.random.rand(n) * 5
        close = low + np.random.rand(n) * 3
        volume = np.random.randint(1000, 10000, n)
        
        request = OHLCVRequest(
            high=high.tolist(),
            low=low.tolist(),
            close=close.tolist(),
            volume=volume.tolist(),
            indicators=["FIREFLY", "SqZmOm", "STAI_V6"]  # Mixed case
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is True
        assert len(result.data["indicators"]) == 3
    
    def test_caching_functionality(self):
        """Test that caching works correctly"""
        service = IndicatorService()
        
        # First calculation with sufficient data
        np.random.seed(42)
        n = 50
        high = np.random.rand(n) * 10 + 100
        low = high - np.random.rand(n) * 5
        close = low + np.random.rand(n) * 3
        
        request1 = OHLCVRequest(
            high=high.tolist(),
            low=low.tolist(),
            close=close.tolist(),
            indicators=["firefly"]
        )
        
        result1 = service.calculate_indicators(request1)
        assert result1.success is True
        
        # Check cache
        cached = service.get_cached_latest("firefly")
        assert cached is not None
        assert "timestamp" in cached
        assert "data_length" in cached
        assert "last_values" in cached
    
    def test_composite_signal_logic(self):
        """Test composite signal generation logic"""
        service = IndicatorService()
        
        # Generate sufficient data that should produce clear signals
        np.random.seed(42)
        n = 50
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        high = close + np.random.rand(n) * 2
        low = close - np.random.rand(n) * 2
        volume = np.full(n, 1000)
        
        request = OHLCVRequest(
            high=high.tolist(),
            low=low.tolist(),
            close=close.tolist(),
            volume=volume.tolist(),
            indicators=["firefly", "stai"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is True
        composite = result.data["composite_signals"]
        
        # Check that signals are mutually exclusive
        buy = np.array(composite["buy_signal"])
        sell = np.array(composite["sell_signal"])
        neutral = np.array(composite["neutral_signal"])
        
        assert not np.any(buy & sell)  # No overlapping buy/sell
        assert np.all(buy | sell | neutral)  # All positions covered
    
    def test_metadata_structure(self):
        """Test that response metadata is correctly structured"""
        service = IndicatorService()
        
        # Generate sufficient data
        np.random.seed(42)
        n = 50
        high = np.random.rand(n) * 10 + 100
        low = high - np.random.rand(n) * 5
        close = low + np.random.rand(n) * 3
        
        request = OHLCVRequest(
            high=high.tolist(),
            low=low.tolist(),
            close=close.tolist(),
            indicators=["firefly"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is True
        assert "indicators_calculated" in result.metadata
        assert "last_updated" in result.metadata
        assert isinstance(result.metadata["indicators_calculated"], list)
        assert isinstance(result.metadata["last_updated"], str)
    
    def test_error_metadata_structure(self):
        """Test that error responses have correct metadata"""
        service = IndicatorService()
        
        request = OHLCVRequest(
            high=[],
            low=[],
            close=[],
            indicators=["firefly"]
        )
        
        result = service.calculate_indicators(request)
        
        assert result.success is False
        assert result.metadata["error"] is True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])