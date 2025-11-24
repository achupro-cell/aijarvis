import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger
from ..config import settings


class FeatureEngineer:
    """Feature engineering for trading data (simplified version without TA-Lib)"""
    
    def __init__(self):
        self.lookback_period = settings.lookback_period
        self.prediction_horizon = settings.prediction_horizon
    
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators from OHLCV data (simplified version)"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Simple moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential moving averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI (simplified)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Stochastic Oscillator
        low_min = df['low'].rolling(window=14).min()
        high_max = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # ADX (simplified)
        df['adx'] = abs(df['high'] - df['low']).rolling(window=14).mean()
        
        # Commodity Channel Index (simplified)
        tp = (df['high'] + df['low'] + df['close']) / 3
        df['cci'] = (tp - tp.rolling(window=20).mean()) / (0.015 * tp.rolling(window=20).std())
        
        # Williams %R
        df['williams_r'] = -100 * (high_max - df['close']) / (high_max - low_min)
        
        # Momentum indicators
        df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        # Volatility
        df['volatility_20'] = df['close'].rolling(20).std()
        df['volatility_ratio'] = df['volatility_20'] / df['volatility_20'].rolling(50).mean()
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['vwap'] = (df['close'] * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
        
        # Price patterns
        df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        
        # Support/Resistance levels (simplified)
        df['resistance_20'] = df['high'].rolling(20).max()
        df['support_20'] = df['low'].rolling(20).min()
        df['price_position'] = (df['close'] - df['support_20']) / (df['resistance_20'] - df['support_20'])
        
        logger.info(f"Created {len([col for col in df.columns if col not in ['open_time', 'open', 'high', 'low', 'close', 'volume']])} technical indicators")
        return df
    
    def create_convergence_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create convergence/divergence features"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Price-Indicator convergence
        df['price_sma_convergence'] = df['close'] / df['sma_20'] - 1
        df['price_ema_convergence'] = df['close'] / df['ema_12'] - 1
        
        # MACD convergence
        df['macd_price_divergence'] = np.where(
            (df['macd'] > df['macd_signal']) & (df['close'] > df['sma_20']), 1,
            np.where((df['macd'] < df['macd_signal']) & (df['close'] < df['sma_20']), -1, 0)
        )
        
        # RSI divergence
        df['rsi_price_divergence'] = np.where(
            (df['rsi'] > 50) & (df['close'] > df['sma_20']), 1,
            np.where((df['rsi'] < 50) & (df['close'] < df['sma_20']), -1, 0)
        )
        
        # Volume-Price convergence
        df['volume_price_trend'] = np.where(
            (df['volume'] > df['volume_sma_20']) & (df['close'] > df['sma_20']), 1,
            np.where((df['volume'] < df['volume_sma_20']) & (df['close'] < df['sma_20']), -1, 0)
        )
        
        # Multi-timeframe convergence (if multiple timeframes available)
        if 'sma_20' in df.columns:
            df['trend_strength'] = (
                (df['close'] > df['sma_20']).astype(int) +
                (df['close'] > df['sma_50']).astype(int) +
                (df['close'] > df['sma_200']).astype(int)
            ) / 3
        
        return df
    
    def create_sentiment_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create sentiment features (placeholder for future integration)"""
        if df.empty or not settings.use_sentiment_features:
            return df
        
        df = df.copy()
        
        # Placeholder sentiment features
        # In a real implementation, these would come from news APIs, social media, etc.
        df['sentiment_score'] = np.random.normal(0, 0.1, len(df))  # Random placeholder
        df['sentiment_momentum'] = df['sentiment_score'].rolling(5).mean()
        df['sentiment_volatility'] = df['sentiment_score'].rolling(20).std()
        
        # Fear & Greed Index placeholder
        df['fear_greed_index'] = 50 + np.random.normal(0, 10, len(df))
        df['fear_greed_extreme'] = np.where(
            df['fear_greed_index'] > 80, 1,
            np.where(df['fear_greed_index'] < 20, -1, 0)
        )
        
        logger.info("Created placeholder sentiment features")
        return df
    
    def create_target_variable(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variable for win-rate prediction"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Future returns
        for horizon in [1, 3, 5, 10]:
            df[f'future_return_{horizon}'] = df['close'].shift(-horizon) / df['close'] - 1
        
        # Binary target: 1 if positive return, 0 otherwise
        df['target_binary'] = (df[f'future_return_{self.prediction_horizon}'] > 0).astype(int)
        
        # Multi-class target: Strong Buy (2), Buy (1), Hold (0), Sell (-1), Strong Sell (-2)
        future_return = df[f'future_return_{self.prediction_horizon}']
        df['target_multiclass'] = np.where(
            future_return > 0.02, 2,  # Strong Buy (>2%)
            np.where(future_return > 0.005, 1,  # Buy (>0.5%)
            np.where(future_return < -0.02, -2,  # Strong Sell (<-2%)
            np.where(future_return < -0.005, -1, 0)  # Sell (<-0.5%), Hold
        )))
        
        # Win rate target (binary with threshold)
        win_threshold = 0.01  # 1% threshold for win
        df['target_win_rate'] = (future_return > win_threshold).astype(int)
        
        logger.info(f"Created target variables: binary, multiclass, and win-rate")
        return df
    
    def create_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5, 10]) -> pd.DataFrame:
        """Create lagged features"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Price lags
        for lag in lags:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'return_lag_{lag}'] = df['close'].pct_change(lag)
        
        # Volume lags
        for lag in [1, 2, 5]:
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        # Indicator lags
        if 'rsi' in df.columns:
            for lag in [1, 2]:
                df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)
        
        return df
    
    def create_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create rolling window features"""
        if df.empty:
            return df
        
        df = df.copy()
        
        # Rolling statistics for price
        for window in [5, 10, 20]:
            df[f'close_mean_{window}'] = df['close'].rolling(window).mean()
            df[f'close_std_{window}'] = df['close'].rolling(window).std()
            df[f'close_max_{window}'] = df['close'].rolling(window).max()
            df[f'close_min_{window}'] = df['close'].rolling(window).min()
            
            # Z-score
            df[f'close_zscore_{window}'] = (df['close'] - df[f'close_mean_{window}']) / df[f'close_std_{window}']
        
        # Rolling volume statistics
        df['volume_mean_20'] = df['volume'].rolling(20).mean()
        df['volume_std_20'] = df['volume'].rolling(20).std()
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main feature engineering pipeline"""
        logger.info("Starting feature engineering...")
        
        # Create all feature types
        if settings.use_technical_indicators:
            df = self.create_technical_indicators(df)
        
        df = self.create_convergence_features(df)
        df = self.create_rolling_features(df)
        df = self.create_lag_features(df)
        df = self.create_sentiment_features(df)
        df = self.create_target_variable(df)
        
        # Remove rows with NaN values (from indicators and lags)
        initial_length = len(df)
        df = df.dropna()
        final_length = len(df)
        
        logger.info(f"Feature engineering complete. Removed {initial_length - final_length} rows with NaN values. Final shape: {df.shape}")
        
        return df
    
    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns (excluding targets and original OHLCV)"""
        exclude_columns = {
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore',
            'target_binary', 'target_multiclass', 'target_win_rate',
            'future_return_1', 'future_return_3', 'future_return_5', 'future_return_10'
        }
        
        feature_columns = [col for col in df.columns if col not in exclude_columns]
        return feature_columns