from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Data settings
    data_dir: str = "data"
    symbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    timeframes: List[str] = ["1h", "4h", "1d"]
    
    # Binance API settings
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    
    # Database settings
    db_path: str = "data/trading_data.db"
    
    # Model settings
    model_dir: str = "models"
    default_model: str = "xgboost"
    
    # Training settings
    lookback_period: int = 100
    prediction_horizon: int = 1
    train_test_split: float = 0.8
    
    # Scheduler settings
    schedule_enabled: bool = True
    schedule_timezone: str = "UTC"
    daily_schedule_time: str = "02:00"
    
    # Feature engineering
    use_technical_indicators: bool = True
    use_sentiment_features: bool = False
    
    # Backtesting
    backtest_initial_capital: float = 10000.0
    backtest_commission: float = 0.001
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()