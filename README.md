# Crypto Screener Backend

A comprehensive Node.js/NestJS backend for crypto trading screener with Binance integration, technical indicator analysis, trade execution with risk controls, and LLM-based market summaries.

## Features

### 1. REST & WebSocket APIs
- **REST Endpoints** for screener queries, signal status, trade execution, and risk management
- **WebSocket support** for real-time signal updates and trade notifications
- **OpenAPI/Swagger** documentation

### 2. Crypto Screener
- Technical indicator calculations (RSI, MACD, Bollinger Bands, Moving Averages)
- Signal aggregation with confidence scoring
- Integration with external indicator engines (HTTP/gRPC)
- Rule-based logic for buy/sell/neutral signals

### 3. Binance Integration
- Support for Binance Spot Trading (testnet and production)
- Market and limit order placement
- Order status tracking and cancellation
- Real-time price feeds
- Encrypted API key storage

### 4. Trade Execution & Risk Controls
- Position sizing validation
- Risk/reward ratio validation
- Stop loss and take profit calculation
- Maximum position limits
- Maximum drawdown tracking
- Open trade monitoring

### 5. Database
- Encrypted storage for API credentials (libsodium)
- Persistent storage of signals, trades, and configurations
- Support for SQLite (default) and PostgreSQL
- TypeORM for database abstraction

### 6. Logging & Monitoring
- Structured logging with Winston
- Console and file output
- Error tracking and debugging

## Project Structure

```
├── src/
│   ├── main.ts                    # Application entry point
│   ├── app.module.ts              # Root module
│   ├── common/                    # Shared utilities
│   │   ├── logger/                # Logging service
│   │   ├── encryption/            # libsodium encryption
│   │   └── validation/            # Joi/Zod validators
│   ├── database/                  # Database setup
│   │   ├── entities/              # TypeORM entities
│   │   └── database.module.ts
│   ├── screener/                  # Screener module
│   │   ├── screener.controller.ts
│   │   ├── screener.service.ts
│   │   ├── screener.gateway.ts    # WebSocket gateway
│   │   ├── indicator.service.ts
│   │   └── dto/
│   └── trade/                     # Trade module
│       ├── trade.controller.ts
│       ├── trade.service.ts
│       ├── binance.service.ts
│       ├── risk.service.ts
│       └── dto/
├── test/                          # Unit tests
├── package.json
├── tsconfig.json
└── jest.config.js
```

## Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

## Configuration

Edit `.env` file with your settings:

```env
# Server
NODE_ENV=development
PORT=3000
LOG_LEVEL=debug

# Database
DATABASE_TYPE=sqlite
DATABASE_NAME=crypto_screener.db

# Binance API (get from https://testnet.binance.vision)
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
BINANCE_USE_TESTNET=true

# Encryption key (32 bytes minimum)
ENCRYPTION_KEY=your-32-byte-encryption-key

# Risk Configuration
MAX_POSITION_SIZE=10000
MAX_DRAWDOWN_PERCENT=20
STOP_LOSS_PERCENT=5
TAKE_PROFIT_PERCENT=10

# Indicator Engine
INDICATOR_ENGINE_URL=http://localhost:3001
INDICATOR_ENGINE_TYPE=http
```

## Running the Application

```bash
# Development with auto-reload
npm run start:dev

# Production build
npm run build
npm run start

# Debug mode
npm run start:debug
```

## API Endpoints

### Screener Endpoints

#### Query Screener
```
POST /api/screener/query
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "limit": 100,
  "indicators": ["RSI", "MACD", "BB", "MA"]
}
```

Response:
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "currentPrice": 45000,
  "indicators": {
    "rsi": 45,
    "macd": { "macd": 100, "signal": 95, "histogram": 5 },
    "bb": { "upper": 46000, "middle": 45000, "lower": 44000 }
  },
  "signal": {
    "type": "buy",
    "confidence": 65.5,
    "reasoning": "RSI oversold; MACD bullish crossover"
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### Get Signals
```
GET /api/screener/signals?symbol=BTCUSDT
```

#### Signal Status
```
GET /api/screener/signal-status?symbol=BTCUSDT
```

### Trade Endpoints

#### Execute Trade
```
POST /api/trade/execute
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "side": "buy",
  "quantity": 0.5,
  "entryPrice": 45000,
  "riskConfigId": "uuid"
}
```

#### Close Trade
```
PUT /api/trade/:id/close
Content-Type: application/json

{
  "exitPrice": 46500
}
```

#### Get Trade
```
GET /api/trade/:id
```

#### List Trades
```
GET /api/trade?symbol=BTCUSDT&status=opened
```

#### Open Trades
```
GET /api/trade/open/list
```

#### Trade Statistics
```
GET /api/trade/stats/summary
```

### Risk Configuration Endpoints

#### Create Risk Config
```
POST /api/trade/risk-config
Content-Type: application/json

{
  "name": "aggressive",
  "maxPositionSize": 20000,
  "maxDrawdownPercent": 30,
  "stopLossPercent": 3,
  "takeProfitPercent": 15,
  "riskRewardRatio": 3
}
```

#### Get Risk Config
```
GET /api/trade/risk-config/:id
```

### API Credentials Endpoints

#### Add API Key
```
POST /api/trade/api-keys
Content-Type: application/json

{
  "name": "binance-main",
  "exchange": "binance",
  "apiKey": "your_key",
  "apiSecret": "your_secret",
  "isTestnet": true
}
```

#### Get Balance
```
GET /api/trade/binance/balance?asset=USDT
```

#### Get Price
```
GET /api/trade/binance/price/:symbol
```

## WebSocket Events

### Screener WebSocket
Connect to: `ws://localhost:3000/ws/screener`

#### Subscribe to Signal Updates
```json
{
  "event": "subscribe_signal",
  "data": { "symbol": "BTCUSDT" }
}
```

#### Signal Update Event
```json
{
  "event": "signal_update",
  "data": {
    "symbol": "BTCUSDT",
    "signal": {
      "type": "buy",
      "confidence": 65.5,
      "reasoning": "..."
    },
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

#### Trade Update Event
```json
{
  "event": "trade_update",
  "data": {
    "trade": {
      "id": "uuid",
      "symbol": "BTCUSDT",
      "status": "opened",
      ...
    },
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

## Testing

```bash
# Run tests
npm test

# Watch mode
npm test:watch

# Coverage
npm test:cov
```

### Test Coverage
- **ScreenerService**: Signal aggregation, indicator calculation, signal storage
- **TradeService**: Trade execution, validation, closure, statistics
- **RiskService**: Risk validation, exit level calculation, configuration management
- **BinanceService**: Order placement, price feeds, balance retrieval

## Database Schema

### api_keys
```sql
- id (UUID)
- name (string)
- exchange (string)
- apiKey (encrypted)
- apiSecret (encrypted)
- isTestnet (boolean)
- passphrase (encrypted, optional)
- createdAt (timestamp)
- updatedAt (timestamp)
```

### risk_configs
```sql
- id (UUID)
- name (string)
- maxPositionSize (decimal)
- maxDrawdownPercent (decimal)
- stopLossPercent (decimal)
- takeProfitPercent (decimal)
- riskRewardRatio (decimal)
- isActive (boolean)
- createdAt (timestamp)
- updatedAt (timestamp)
```

### trades
```sql
- id (UUID)
- symbol (string)
- side (enum: buy/sell)
- quantity (decimal)
- entryPrice (decimal)
- exitPrice (decimal, nullable)
- profitLossPercent (decimal, nullable)
- status (enum: pending/opened/partially_closed/closed/cancelled)
- riskConfigId (UUID, nullable)
- binanceOrderId (string, nullable)
- notes (text, nullable)
- createdAt (timestamp)
- updatedAt (timestamp)
- closedAt (timestamp, nullable)
```

### signals
```sql
- id (UUID)
- symbol (string)
- signalType (enum: buy/sell/strong_buy/strong_sell/neutral)
- confidence (decimal)
- indicators (JSON)
- reasoning (text)
- actioned (boolean)
- actionedAt (timestamp, nullable)
- createdAt (timestamp)
- updatedAt (timestamp)
```

## Binance Integration

### Testnet Setup
1. Create account at https://testnet.binance.vision
2. Generate API key and secret
3. Set `BINANCE_USE_TESTNET=true` in .env
4. Save credentials via `/api/trade/api-keys` endpoint

### Production Setup
1. Create account at https://www.binance.com
2. Enable 2FA
3. Generate API key with appropriate permissions
4. Set `BINANCE_USE_TESTNET=false` in .env
5. Store securely via encrypted storage

## Error Handling

The API uses standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation errors, risk violations)
- `404`: Not Found
- `500`: Internal Server Error

## Encryption

API keys and secrets are encrypted using:
- **Algorithm**: libsodium (XChaCha20-Poly1305)
- **Key Size**: 32 bytes
- **Nonce**: 24 bytes (randomized per encryption)

## Logging

Logs are written to:
- **Console**: Debug level (development)
- **logs/combined.log**: All messages
- **logs/error.log**: Error level and above

## Development

### Code Style
- TypeScript strict mode enabled
- ESLint for linting
- Prettier for formatting
- Consistent naming conventions (camelCase)

### Linting & Formatting
```bash
npm run lint        # Lint and fix
npm run format      # Format code
```

## Security Considerations

1. **API Keys**: Always use environment variables, never commit to git
2. **Encryption**: Use strong encryption keys (32+ bytes)
3. **HTTPS**: Use HTTPS in production
4. **CORS**: Configure CORS appropriately
5. **Rate Limiting**: Consider adding rate limiting for production
6. **Input Validation**: All inputs are validated with Joi/Zod

## Future Enhancements

- [ ] gRPC support for indicator engine
- [ ] LLM-based market summaries (OpenAI integration)
- [ ] Advanced chart analysis with technical patterns
- [ ] Portfolio analytics and performance tracking
- [ ] Automated trading signals
- [ ] Mobile app integration
- [ ] Alert notifications (email, Telegram, Discord)
- [ ] Multi-exchange support (Kraken, Coinbase, etc.)
- [ ] Advanced backtesting engine

## License

MIT

## Support

For issues and questions, please create an issue in the repository.
