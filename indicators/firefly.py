"""
Firefly Oscillator implementation based on LazyBear's Pine Script
"""
import numpy as np
import pandas as pd

class FireflyOscillator:
    def __init__(self, length=20, mult=2.0):
        """
        Initialize Firefly Oscillator
        
        Args:
            length: Period for calculations (default: 20)
            mult: Multiplier for bands (default: 2.0)
        """
        self.length = length
        self.mult = mult
        self._cache = {}
    
    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict:
        """
        Calculate Firefly Oscillator
        
        Args:
            high: Array of high prices
            low: Array of low prices  
            close: Array of close prices
            
        Returns:
            dict with oscillator values and signals
        """
        n = len(close)
        if n < self.length:
            raise ValueError(f"Need at least {self.length} periods for calculation")
        
        # Calculate typical price and moving averages
        typical = (high + low + close) / 3
        sma_typical = self._sma(typical, self.length)
        
        # Calculate standard deviation
        std_typical = self._rolling_std(typical, self.length)
        
        # Calculate upper and lower bands
        upper_band = sma_typical + (self.mult * std_typical)
        lower_band = sma_typical - (self.mult * std_typical)
        
        # Calculate oscillator
        oscillator = (typical - lower_band) / (upper_band - lower_band) * 100
        oscillator = np.clip(oscillator, 0, 100)
        
        # Calculate signal line (SMA of oscillator)
        signal = self._sma(oscillator, 9)
        
        # Generate signals
        buy_signal = (oscillator > signal) & (oscillator < 20)
        sell_signal = (oscillator < signal) & (oscillator > 80)
        neutral_signal = ~(buy_signal | sell_signal)
        
        return {
            'oscillator': oscillator,
            'signal': signal,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'neutral_signal': neutral_signal,
            'metadata': {
                'indicator': 'Firefly Oscillator',
                'length': self.length,
                'multiplier': self.mult
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