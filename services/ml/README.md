# ML Trading Pipeline

A comprehensive machine learning pipeline for cryptocurrency trading prediction with automated data fetching, feature engineering, model training, backtesting, and scheduling.

## Features

- **Data Fetching**: Automated OHLCV data fetching from Binance REST API
- **Storage**: SQLite and Parquet storage formats
- **Feature Engineering**: 40+ technical indicators and convergence features
- **Model Training**: XGBoost and LightGBM with hyperparameter tuning
- **Backtesting**: Comprehensive strategy evaluation with performance metrics
- **Model Registry**: Versioned model artifacts with metadata
- **Scheduler**: Automated daily retraining with APScheduler
- **CLI**: Command-line interface for all operations

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install TA-Lib (required for technical indicators):
```bash
# On Ubuntu/Debian
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
pip install TA-Lib
```

## Quick Start

### 1. Fetch Data
```bash
python main.py fetch-data --symbols BTCUSDT ETHUSDT --timeframes 1h 4h --days 365
```

### 2. Train Models
```bash
python main.py train --symbol BTCUSDT --timeframe 1h --models xgboost lightgbm --target binary
```

### 3. Backtest Strategy
```bash
python main.py backtest --symbol BTCUSDT --timeframe 1h --threshold 0.6 --plot
```

### 4. Setup Scheduler
```bash
python main.py schedule --setup --start
```

## CLI Commands

### Data Fetching

```bash
# Fetch historical data
python main.py fetch-data [OPTIONS]

Options:
  -s, --symbols TEXT     Trading symbols (default: BTCUSDT, ETHUSDT)
  -t, --timeframes TEXT  Timeframes (default: 1h, 4h, 1d)
  -d, --days INTEGER     Days of historical data (default: 365)
  -o, --output CHOICE    Output format: sqlite, parquet, both (default: both)
```

### Model Training

```bash
# Train ML models
python main.py train [OPTIONS]

Options:
  -s, --symbol TEXT        Symbol to train on (default: BTCUSDT)
  -t, --timeframe TEXT     Timeframe (default: 1h)
  -m, --models TEXT        Models: xgboost, lightgbm (default: both)
  --target CHOICE          Target: binary, multiclass, win_rate (default: binary)
  --tune                   Enable hyperparameter tuning
  --register               Register models in registry (default: True)
```

### Backtesting

```bash
# Backtest trading strategies
python main.py backtest [OPTIONS]

Options:
  -s, --symbol TEXT        Symbol to backtest (default: BTCUSDT)
  -t, --timeframe TEXT     Timeframe (default: 1h)
  --model-id TEXT          Specific model ID (uses latest if not provided)
  --threshold FLOAT        Prediction threshold (default: 0.6)
  --position-size FLOAT    Position size fraction (default: 0.1)
  --stop-loss FLOAT        Stop loss percentage (default: 0.02)
  --take-profit FLOAT      Take profit percentage (default: 0.04)
  --plot                   Generate visualization plots
```

### Scheduler Management

```bash
# Manage automated pipeline
python main.py schedule [OPTIONS]

Options:
  --setup                  Setup default schedule
  --start                  Start scheduler
  --stop                   Stop scheduler
  --status                 Show scheduler status
  --list-jobs              List scheduled jobs
  --run-job TEXT           Run specific job immediately
```

### Model Registry

```bash
# List registered models
python main.py list-models [OPTIONS]

Options:
  --model-type TEXT        Filter by model type
  --target-type TEXT       Filter by target type
  --status TEXT            Filter by status (default: active)

# Compare models
python main.py compare-models --model-id MODEL_ID [OTHER_MODEL_IDS...]
```

## Architecture

### Data Flow

1. **Data Fetching** → Binance API → SQLite/Parquet
2. **Feature Engineering** → Technical Indicators → Convergence Features
3. **Model Training** → XGBoost/LightGBM → Model Registry
4. **Backtesting** → Strategy Simulation → Performance Metrics
5. **Scheduler** → Automated Retraining → Model Updates

### Key Components

#### Data Fetcher (`src/data/fetcher.py`)
- Fetches OHLCV data from Binance REST API
- Handles API rate limiting and data validation
- Stores data in SQLite and Parquet formats
- Supports incremental updates

#### Feature Engineer (`src/features/engineer.py`)
- 40+ technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
- Convergence/divergence features
- Rolling window statistics
- Lagged features
- Sentiment feature placeholders

#### Model Trainer (`src/models/trainer.py`)
- XGBoost and LightGBM implementation
- Hyperparameter tuning with GridSearchCV
- Cross-validation and performance metrics
- Model serialization with joblib

#### Backtester (`src/backtesting/evaluator.py`)
- Strategy simulation with realistic trading costs
- Performance metrics (Sharpe ratio, max drawdown, win rate)
- Visualization with Plotly
- Trade analysis and reporting

#### Model Registry (`src/registry/registry.py`)
- Versioned model storage
- Metadata tracking
- Model comparison and retrieval
- Import/export functionality

#### Scheduler (`src/scheduler/pipeline.py`)
- APScheduler-based automation
- Daily data fetching and model retraining
- Hourly data updates
- Custom job scheduling

## Configuration

Configuration is managed through `src/config.py` using Pydantic settings:

```python
# Environment variables or .env file
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# Or modify settings directly
symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
timeframes = ["1h", "4h", "1d"]
daily_schedule_time = "02:00"
```

## Adding New Models

### 1. Implement Model Class

Create a new model class in `src/models/trainer.py`:

```python
def create_custom_model(self, X_train, y_train, target_type='binary'):
    """Create and train custom model"""
    from sklearn.ensemble import RandomForestClassifier
    
    params = {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    }
    
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    
    return model
```

### 2. Update Training Pipeline

Modify `train_models` method to include your model:

```python
def train_models(self, df, model_types=['xgboost', 'lightgbm', 'custom'], target_type='binary'):
    # ... existing code ...
    
    for model_type in model_types:
        if model_type == 'custom':
            model = self.create_custom_model(X_train, y_train, target_type)
        # ... rest of the code ...
```

### 3. Update CLI

Add your model to CLI options in `main.py`:

```python
@click.option('--models', '-m', multiple=True, 
              default=['xgboost', 'lightgbm', 'custom'], 
              help='Models to train')
```

### 4. Register and Test

```bash
# Train with new model
python main.py train --models custom --symbol BTCUSDT

# Test in backtest
python main.py backtest --model-id custom_binary_YYYYMMDD_HHMMSS
```

## Performance Metrics

### Model Evaluation
- **Accuracy**: Overall prediction accuracy
- **Precision**: True positive rate
- **Recall**: Sensitivity
- **F1-Score**: Harmonic mean of precision and recall
- **AUC-ROC**: Area under ROC curve
- **Cross-Validation**: 5-fold CV scores

### Backtesting Metrics
- **Total Return**: Overall portfolio return
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss
- **Average Win/Loss**: Mean trade performance

## Best Practices

### Data Management
- Fetch data during off-peak hours to avoid API limits
- Use both SQLite (fast access) and Parquet (archival) formats
- Implement data validation and cleaning
- Regularly backup your databases

### Model Training
- Use cross-validation to avoid overfitting
- Perform hyperparameter tuning for better performance
- Monitor model drift and performance degradation
- Keep track of model versions and metadata

### Backtesting
- Use realistic transaction costs and slippage
- Test on out-of-sample data
- Consider multiple market conditions
- Validate with walk-forward analysis

### Production Deployment
- Set up automated monitoring and alerting
- Implement model versioning and rollback
- Use A/B testing for new models
- Monitor prediction quality and data drift

## Troubleshooting

### Common Issues

**TA-Lib Installation Error**
```bash
# Install system dependencies first
sudo apt-get install build-essential
# Then install TA-Lib
pip install TA-Lib
```

**Memory Issues with Large Datasets**
```python
# Process data in chunks
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process_chunk(chunk)
```

**API Rate Limiting**
```python
# Add delays between requests
import time
time.sleep(0.1)  # 100ms delay
```

**Model Performance Degradation**
```python
# Check for data drift
recent_data = df.tail(1000)
old_data = df.head(1000)
compare_distributions(recent_data, old_data)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.