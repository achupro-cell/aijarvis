"""
Main indicator computation service
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from indicators import FireflyOscillator, SQZMOMCombo, STAIV6

class OHLCVRequest(BaseModel):
    high: List[float] = Field(..., description="High prices array")
    low: List[float] = Field(..., description="Low prices array")
    close: List[float] = Field(..., description="Close prices array")
    volume: Optional[List[float]] = Field(None, description="Volume array (required for SQZMOM)")
    indicators: List[str] = Field(..., description="List of indicators to calculate")

class IndicatorResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]

class IndicatorService:
    def __init__(self):
        """Initialize the indicator service"""
        self.firefly = FireflyOscillator()
        self.sqzmom = SQZMOMCombo()
        self.stai = STAIV6()
        self._latest_cache = {}
    
    def calculate_indicators(self, request: OHLCVRequest) -> IndicatorResponse:
        """
        Calculate requested indicators
        
        Args:
            request: OHLCV data and indicator list
            
        Returns:
            IndicatorResponse with calculated values
        """
        try:
            # Convert to numpy arrays
            high = np.array(request.high, dtype=float)
            low = np.array(request.low, dtype=float)
            close = np.array(request.close, dtype=float)
            
            # Validate input lengths
            if not (len(high) == len(low) == len(close)):
                raise ValueError("High, low, and close arrays must have same length")
            
            if len(close) == 0:
                raise ValueError("Empty data provided")
            
            # Check volume for SQZMOM
            volume = None
            if 'sqzmom' in [ind.lower() for ind in request.indicators]:
                if request.volume is None:
                    raise ValueError("Volume is required for SQZMOM indicator")
                volume = np.array(request.volume, dtype=float)
                if len(volume) != len(close):
                    raise ValueError("Volume array must match price arrays length")
            
            results = {}
            
            # Calculate requested indicators
            for indicator_name in request.indicators:
                indicator_lower = indicator_name.lower()
                
                if indicator_lower in ['firefly', 'firefly_oscillator']:
                    result = self.firefly.calculate(high, low, close)
                    # Convert NaN values to None for JSON serialization
                    cleaned_result = self._clean_nan_values(result)
                    results['firefly'] = cleaned_result
                    self._cache_latest('firefly', high, low, close, result)
                    
                elif indicator_lower in ['sqzmom', 'sqzmom_combo']:
                    if volume is None:
                        raise ValueError("Volume is required for SQZMOM indicator")
                    result = self.sqzmom.calculate(high, low, close, volume)
                    cleaned_result = self._clean_nan_values(result)
                    results['sqzmom'] = cleaned_result
                    self._cache_latest('sqzmom', high, low, close, volume, result)
                    
                elif indicator_lower in ['stai', 'stai_v6']:
                    result = self.stai.calculate(high, low, close)
                    cleaned_result = self._clean_nan_values(result)
                    results['stai'] = cleaned_result
                    self._cache_latest('stai', high, low, close, result)
                    
                else:
                    raise ValueError(f"Unknown indicator: {indicator_name}")
            
            # Generate composite signals
            composite_signals = self._generate_composite_signals(results)
            
            return IndicatorResponse(
                success=True,
                data={
                    'indicators': results,
                    'composite_signals': composite_signals,
                    'input_length': len(close)
                },
                metadata={
                    'indicators_calculated': list(results.keys()),
                    'last_updated': pd.Timestamp.now().isoformat()
                }
            )
            
        except Exception as e:
            return IndicatorResponse(
                success=False,
                data={'error': str(e)},
                metadata={'error': True}
            )
    
    def get_cached_latest(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Get cached latest values for an indicator"""
        return self._latest_cache.get(indicator)
    
    def _clean_nan_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert NaN/inf values to None for JSON serialization"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                # Convert each element in the array
                clean_array = []
                for v in value:
                    if np.isnan(v) or np.isinf(v):
                        clean_array.append(None)
                    else:
                        clean_array.append(float(v))
                cleaned[key] = clean_array
            elif isinstance(value, bool):
                cleaned[key] = value
            elif isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    cleaned[key] = None
                else:
                    cleaned[key] = float(value)
            else:
                cleaned[key] = value
        return cleaned
    
    def _cache_latest(self, indicator: str, *args):
        """Cache the latest values for an indicator"""
        if len(args) >= 4:  # At least high, low, close, result
            self._latest_cache[indicator] = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'data_length': len(args[0]),  # high array length
                'last_values': {}
            }
            
            # Cache last few values of each output array
            result = args[-1]
            for key, value in result.items():
                if isinstance(value, np.ndarray):
                    # Convert NaN to None for JSON serialization
                    clean_array = []
                    for v in value[-5:]:
                        if np.isnan(v):
                            clean_array.append(None)
                        elif np.isinf(v):
                            clean_array.append(None)
                        else:
                            clean_array.append(float(v))
                    self._latest_cache[indicator]['last_values'][key] = clean_array
                elif isinstance(value, bool):
                    self._latest_cache[indicator]['last_values'][key] = value
                elif isinstance(value, (int, float)):
                    # Convert NaN/inf to None
                    if np.isnan(value) or np.isinf(value):
                        self._latest_cache[indicator]['last_values'][key] = None
                    else:
                        self._latest_cache[indicator]['last_values'][key] = float(value)
    
    def _generate_composite_signals(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate composite buy/sell/neutral signals from all indicators"""
        if not results:
            return {}
        
        # Initialize composite signals
        n = None
        for indicator_data in results.values():
            if 'buy_signal' in indicator_data:
                n = len(indicator_data['buy_signal'])
                break
        
        if n is None:
            return {}
        
        composite_buy = np.zeros(n, dtype=bool)
        composite_sell = np.zeros(n, dtype=bool)
        composite_neutral = np.ones(n, dtype=bool)
        
        # Aggregate signals from all indicators
        for indicator_name, indicator_data in results.items():
            if 'buy_signal' in indicator_data:
                buy_sig = indicator_data['buy_signal']
                sell_sig = indicator_data['sell_signal']
                neutral_sig = indicator_data['neutral_signal']
                
                # Use majority voting or weighted approach
                composite_buy = composite_buy | buy_sig
                composite_sell = composite_sell | sell_sig
                composite_neutral = composite_neutral & neutral_sig
        
        # Resolve conflicts (if both buy and sell are true, use neutral)
        conflict = composite_buy & composite_sell
        composite_buy[conflict] = False
        composite_sell[conflict] = False
        composite_neutral[conflict] = True
        
        return {
            'buy_signal': composite_buy.tolist(),
            'sell_signal': composite_sell.tolist(),
            'neutral_signal': composite_neutral.tolist(),
            'methodology': 'OR aggregation with conflict resolution to neutral'
        }