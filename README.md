# Indicator Computation Service

A high-performance Python service that computes technical indicators (Firefly Oscillator, SQZMOM Combo, and STAI v6) from OHLCV data using NumPy/pandas. Exposes both REST and gRPC interfaces for seamless integration.

## Features

- **Three Technical Indicators**:
  - **Firefly Oscillator** (LazyBear): Bollinger Bands-based oscillator with overbought/oversold signals
  - **SQZMOM Combo**: Squeeze Momentum indicator combining Bollinger Bands and Keltner Channels
  - **STAI v6**: Super Trend Adaptive Indicator combining MACD, RSI, and Stochastic

- **High Performance**:
  - Vectorized NumPy/pandas calculations
  - <100ms response time for 500 candles
  - Caching of latest calculations
  - Composite signal generation

- **Dual Interface**:
  - REST API (FastAPI)
  - gRPC service
  - Comprehensive OpenAPI documentation

## Quick Start

### Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Or for development with live reload
docker-compose --profile dev up
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Generate gRPC files
python -m grpc_tools.protoc --python_out=. --grpc_python_out=. --proto_path=. indicators.proto

# Run REST API
python main.py

# Run gRPC server (in another terminal)
python grpc_server.py
```

## API Usage

### REST API

The service runs on `http://localhost:8000`

#### Health Check
```bash
curl http://localhost:8000/
```

#### Calculate Indicators
```bash
curl -X POST "http://localhost:8000/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "high": [102.5, 103.2, 104.1, 103.8, 105.0],
    "low": [99.5, 100.2, 101.1, 100.8, 102.0],
    "close": [101.0, 101.7, 102.6, 102.3, 103.5],
    "volume": [1500, 1650, 1800, 1750, 1900],
    "indicators": ["firefly", "sqzmom", "stai"]
  }'
```

#### List Available Indicators
```bash
curl http://localhost:8000/indicators
```

### gRPC

The gRPC service runs on `localhost:50051`

```python
import grpc
import indicators_pb2
import indicators_pb2_grpc

# Connect to service
channel = grpc.insecure_channel('localhost:50051')
stub = indicators_pb2_grpc.IndicatorServiceStub(channel)

# Create request
request = indicators_pb2.CalculateRequest(
    high=[102.5, 103.2, 104.1, 103.8, 105.0],
    low=[99.5, 100.2, 101.1, 100.8, 102.0],
    close=[101.0, 101.7, 102.6, 102.3, 103.5],
    volume=[1500, 1650, 1800, 1750, 1900],
    indicators=["firefly", "sqzmom", "stai"]
)

# Call service
response = stub.CalculateIndicators(request)
```

## Indicators

### Firefly Oscillator

Based on LazyBear's Pine Script, this indicator uses Bollinger Bands to create an oscillator that ranges from 0-100.

**Formula**:
```
Typical Price = (High + Low + Close) / 3
SMA = Simple Moving Average(Typical Price, length)
StdDev = Standard Deviation(Typical Price, length)
Upper Band = SMA + (multiplier * StdDev)
Lower Band = SMA - (multiplier * StdDev)
Oscillator = ((Typical Price - Lower Band) / (Upper Band - Lower Band)) * 100
Signal = SMA(Oscillator, 9)
```

**Signals**:
- **Buy**: Oscillator > Signal AND Oscillator < 20
- **Sell**: Oscillator < Signal AND Oscillator > 80
- **Neutral**: All other conditions

### SQZMOM Combo

Combines Bollinger Bands and Keltner Channels to identify squeeze conditions and momentum.

**Formula**:
```
# Bollinger Bands
BB Basis = SMA(Close, bb_length)
BB StdDev = StdDev(Close, bb_length)
BB Upper = BB Basis + (bb_mult * BB StdDev)
BB Lower = BB Basis - (bb_mult * BB StdDev)

# Keltner Channels
TR = True Range(High, Low, Close)
ATR = SMA(TR, kc_length)
KC Basis = SMA(Close, kc_length)
KC Upper = KC Basis + (kc_mult * ATR)
KC Lower = KC Basis - (kc_mult * ATR)

# Squeeze Detection
Squeeze On = BB Lower >= KC Lower AND BB Upper <= KC Upper
Squeeze Off = NOT Squeeze On

# Momentum
Momentum = Linear Regression Slope(Close, 20)
Histogram = Momentum - SMA(Momentum, 6)
```

**Signals**:
- **Buy**: Squeeze Off AND Histogram > 0 AND Histogram previous ≤ 0
- **Sell**: Squeeze Off AND Histogram < 0 AND Histogram previous ≥ 0
- **Neutral**: All other conditions

### STAI v6

Super Trend Adaptive Indicator v6 combines multiple indicators for robust signal generation.

**Formula**:
```
# MACD
EMA Fast = EMA(Close, fast_length)
EMA Slow = EMA(Close, slow_length)
MACD = EMA Fast - EMA Slow
Signal = EMA(MACD, signal_length)
Histogram = MACD - Signal

# RSI
RSI = Relative Strength Index(Close, rsi_length)

# Stochastic
Stoch K = 100 * (Close - Lowest(Low, 14)) / (Highest(High, 14) - Lowest(Low, 14))
Stoch D = SMA(Stoch K, 3)

# ATR
ATR = Average True Range(High, Low, Close, 14)

# STAI Composite Score
MACD Norm = Normalize(Histogram, 0, 100)
RSI Norm = RSI  # Already 0-100
Stoch Norm = Stoch K  # Already 0-100
STAI Score = 0.4 * MACD Norm + 0.3 * RSI Norm + 0.3 * Stoch Norm
```

**Signals**:
- **Overbought**: STAI Score > 70
- **Oversold**: STAI Score < 30
- **Buy**: Oversold AND MACD > Signal AND STAI Score rising
- **Sell**: Overbought AND MACD < Signal AND STAI Score falling
- **Neutral**: All other conditions

## Performance

- **Response Time**: <100ms for 500 candles (all indicators)
- **Memory Usage**: Efficient vectorized operations
- **Caching**: Latest values cached for quick retrieval
- **Concurrency**: Supports multiple simultaneous requests

## Testing

```bash
# Run all tests
pytest -v

# Run specific test files
pytest test_indicators.py -v
pytest test_service.py -v
pytest test_integration.py -v

# Run performance tests
pytest test_integration.py::TestRestAPI::test_performance_500_candles -v

# Run with coverage
pytest --cov=indicators --cov=service --cov-report=html
```

## Configuration

### Environment Variables

- `PYTHONUNBUFFERED`: Set to 1 for immediate log output
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Indicator Parameters

Each indicator can be configured with different parameters:

```python
# Firefly Oscillator
firefly = FireflyOscillator(length=20, mult=2.0)

# SQZMOM Combo
sqzmom = SQZMOMCombo(bb_length=20, bb_mult=2.0, kc_length=20, kc_mult=1.5)

# STAI v6
stai = STAIV6(fast_length=12, slow_length=26, signal_length=9, rsi_length=14)
```

## Monitoring

### Health Checks

- **REST**: `GET /health`
- **Docker**: Built-in health check every 30s

### Performance Metrics

- Processing time included in response headers (`X-Process-Time`)
- Cache hit rates available via `/cache/{indicator}` endpoint

## Error Handling

The service provides comprehensive error handling:

- **Input Validation**: Mismatched array lengths, missing required data
- **Indicator Errors**: Insufficient data for calculations
- **Service Errors**: Internal processing failures

All errors include descriptive messages and appropriate HTTP status codes.

## Development

### Project Structure

```
.
├── indicators/           # Indicator implementations
│   ├── __init__.py
│   ├── firefly.py       # Firefly Oscillator
│   ├── sqzmom.py        # SQZMOM Combo
│   └── stai_v6.py       # STAI v6
├── main.py              # REST API server
├── grpc_server.py       # gRPC server
├── service.py           # Core service logic
├── indicators.proto     # gRPC protocol definition
├── test_indicators.py   # Unit tests for indicators
├── test_service.py      # Unit tests for service
├── test_integration.py  # Integration tests
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
└── README.md           # This file
```

### Adding New Indicators

1. Create new indicator class in `indicators/` directory
2. Implement `calculate()` method returning standardized format
3. Add to `indicators/__init__.py`
4. Update service logic to handle new indicator
5. Add tests and documentation

### Code Style

- Follow PEP 8
- Use type hints
- Write comprehensive docstrings
- Include unit tests with >90% coverage

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Create an issue in the project repository
- Check the test suite for usage examples
- Review the API documentation at `http://localhost:8000/docs`