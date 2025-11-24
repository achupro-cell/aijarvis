"""
SQZMOM Combo indicator implementation
"""
import numpy as np
import pandas as pd

class SQZMOMCombo:
    def __init__(self, bb_length=20, bb_mult=2.0, kc_length=20, kc_mult=1.5):
        """
        Initialize SQZMOM Combo
        
        Args:
            bb_length: Bollinger Bands period
            bb_mult: Bollinger Bands multiplier
            kc_length: Keltner Channels period  
            kc_mult: Keltner Channels multiplier
        """
        self.bb_length = bb_length
        self.bb_mult = bb_mult
        self.kc_length = kc_length
        self.kc_mult = kc_mult
        self._cache = {}
    
    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> dict:
        """
        Calculate SQZMOM Combo
        
        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of close prices
            volume: Array of volumes
            
        Returns:
            dict with SQZMOM values and signals
        """
        n = len(close)
        if n < max(self.bb_length, self.kc_length):
            raise ValueError(f"Need at least {max(self.bb_length, self.kc_length)} periods for calculation")
        
        # Calculate Bollinger Bands
        bb_basis = self._sma(close, self.bb_length)
        bb_std = self._rolling_std(close, self.bb_length)
        bb_upper = bb_basis + (self.bb_mult * bb_std)
        bb_lower = bb_basis - (self.bb_mult * bb_std)
        
        # Calculate Keltner Channels
        tr = self._true_range(high, low, close)
        atr = self._sma(tr, self.kc_length)
        kc_basis = self._sma(close, self.kc_length)
        kc_upper = kc_basis + (self.kc_mult * atr)
        kc_lower = kc_basis - (self.kc_mult * atr)
        
        # Calculate Momentum Squeeze
        squeeze_on = (bb_lower >= kc_lower) & (bb_upper <= kc_upper)
        squeeze_off = ~squeeze_on
        
        # Calculate Momentum (linear regression of close prices)
        momentum = self._linear_regression_slope(close, 20)
        
        # Calculate histogram
        histogram = momentum - self._sma(momentum, 6)
        
        # Generate signals
        histogram_prev = np.concatenate([[histogram[0]], histogram[:-1]])
        buy_signal = squeeze_off & (histogram > 0) & (histogram_prev <= 0)
        sell_signal = squeeze_off & (histogram < 0) & (histogram_prev >= 0)
        neutral_signal = ~(buy_signal | sell_signal)
        
        return {
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_basis': bb_basis,
            'kc_upper': kc_upper,
            'kc_lower': kc_lower,
            'kc_basis': kc_basis,
            'momentum': momentum,
            'histogram': histogram,
            'squeeze_on': squeeze_on,
            'squeeze_off': squeeze_off,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'neutral_signal': neutral_signal,
            'metadata': {
                'indicator': 'SQZMOM Combo',
                'bb_length': self.bb_length,
                'bb_mult': self.bb_mult,
                'kc_length': self.kc_length,
                'kc_mult': self.kc_mult
            }
        }
    
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        result = np.full_like(data, np.nan, dtype=float)
        if len(data) >= period:
            cumsum = np.cumsum(np.insert(data, 0, 0)) 
            result[period-1:] = (cumsum[period:] - cumsum[:-period]) / period
        return result
    
    def _rolling_std(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate rolling standard deviation"""
        result = np.full_like(data, np.nan, dtype=float)
        if len(data) >= period:
            for i in range(period-1, len(data)):
                result[i] = np.std(data[i-period+1:i+1], ddof=0)
        return result
    
    def _true_range(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Calculate True Range"""
        tr1 = high - low
        tr2 = np.abs(high - np.concatenate([[close[0]], close[:-1]]))
        tr3 = np.abs(low - np.concatenate([[close[0]], close[:-1]]))
        return np.maximum(tr1, np.maximum(tr2, tr3))
    
    def _linear_regression_slope(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate linear regression slope over given period"""
        result = np.full_like(data, np.nan, dtype=float)
        if len(data) >= period:
            x = np.arange(period)
            x_mean = np.mean(x)
            x_sum_sq = np.sum((x - x_mean) ** 2)
            
            for i in range(period-1, len(data)):
                y = data[i-period+1:i+1]
                y_mean = np.mean(y)
                result[i] = np.sum((x - x_mean) * (y - y_mean)) / x_sum_sq
        return result