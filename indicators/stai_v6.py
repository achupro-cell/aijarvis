"""
STAI v6 indicator implementation
"""
import numpy as np
import pandas as pd

class STAIV6:
    def __init__(self, fast_length=12, slow_length=26, signal_length=9, rsi_length=14):
        """
        Initialize STAI v6
        
        Args:
            fast_length: Fast EMA period
            slow_length: Slow EMA period
            signal_length: Signal line period
            rsi_length: RSI period
        """
        self.fast_length = fast_length
        self.slow_length = slow_length
        self.signal_length = signal_length
        self.rsi_length = rsi_length
        self._cache = {}
    
    def calculate(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict:
        """
        Calculate STAI v6
        
        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of close prices
            
        Returns:
            dict with STAI v6 values and signals
        """
        n = len(close)
        if n < max(self.slow_length, self.rsi_length):
            raise ValueError(f"Need at least {max(self.slow_length, self.rsi_length)} periods for calculation")
        
        # Calculate MACD
        ema_fast = self._ema(close, self.fast_length)
        ema_slow = self._ema(close, self.slow_length)
        macd = ema_fast - ema_slow
        signal = self._ema(macd, self.signal_length)
        histogram = macd - signal
        
        # Calculate RSI
        rsi = self._rsi(close, self.rsi_length)
        
        # Calculate Stochastic
        stoch_k, stoch_d = self._stochastic(high, low, close, 14, 3)
        
        # Calculate ATR for volatility
        atr = self._atr(high, low, close, 14)
        
        # Calculate STAI composite score
        # Normalize components to 0-100 range
        macd_norm = self._normalize_to_100(histogram)
        rsi_norm = rsi  # RSI is already 0-100
        stoch_norm = stoch_k  # Stochastic is already 0-100
        
        # Weighted composite (adjustable weights)
        stai_score = (0.4 * macd_norm + 0.3 * rsi_norm + 0.3 * stoch_norm)
        
        # Generate signals based on STAI score and confirmation
        overbought = stai_score > 70
        oversold = stai_score < 30
        
        # Signal generation with trend confirmation
        uptrend = macd > signal
        downtrend = macd < signal
        
        stai_score_prev = np.concatenate([[stai_score[0]], stai_score[:-1]])
        buy_signal = oversold & uptrend & (stai_score > stai_score_prev)
        sell_signal = overbought & downtrend & (stai_score < stai_score_prev)
        neutral_signal = ~(buy_signal | sell_signal)
        
        return {
            'macd': macd,
            'signal': signal,
            'histogram': histogram,
            'rsi': rsi,
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'atr': atr,
            'stai_score': stai_score,
            'overbought': overbought,
            'oversold': oversold,
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'neutral_signal': neutral_signal,
            'metadata': {
                'indicator': 'STAI v6',
                'fast_length': self.fast_length,
                'slow_length': self.slow_length,
                'signal_length': self.signal_length,
                'rsi_length': self.rsi_length
            }
        }
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        alpha = 2.0 / (period + 1)
        result = np.full_like(data, np.nan, dtype=float)
        if len(data) > 0:
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
        return result
    
    def _rsi(self, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Relative Strength Index"""
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = self._sma(np.concatenate([[0], gain]), period)
        avg_loss = self._sma(np.concatenate([[0], loss]), period)
        
        rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int, d_period: int) -> tuple:
        """Calculate Stochastic Oscillator"""
        n = len(close)
        k = np.full(n, np.nan, dtype=float)
        
        for i in range(k_period - 1, n):
            highest_high = np.max(high[i-k_period+1:i+1])
            lowest_low = np.min(low[i-k_period+1:i+1])
            k[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low + 1e-10)
        
        d = self._sma(k, d_period)
        return k, d
    
    def _atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Average True Range"""
        tr = self._true_range(high, low, close)
        return self._sma(tr, period)
    
    def _true_range(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Calculate True Range"""
        tr1 = high - low
        tr2 = np.abs(high - np.concatenate([[close[0]], close[:-1]]))
        tr3 = np.abs(low - np.concatenate([[close[0]], close[:-1]]))
        return np.maximum(tr1, np.maximum(tr2, tr3))
    
    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        result = np.full_like(data, np.nan, dtype=float)
        if len(data) >= period:
            for i in range(period-1, len(data)):
                window = data[i-period+1:i+1]
                finite_window = window[~np.isnan(window)]
                if len(finite_window) > 0:
                    result[i] = np.mean(finite_window)
        return result
    
    def _normalize_to_100(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-100 range"""
        min_val = np.nanmin(data)
        max_val = np.nanmax(data)
        if max_val == min_val:
            return np.full_like(data, 50.0, dtype=float)
        return 100 * (data - min_val) / (max_val - min_val)