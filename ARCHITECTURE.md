# Crypto Screener Backend - Architecture

## Overview

The Crypto Screener Backend is built using NestJS with Fastify as the underlying HTTP server. It provides a complete solution for crypto trading analysis, signal generation, and trade execution with risk management.

## Architecture Layers

### 1. Presentation Layer (Controllers)
- **ScreenerController**: Handles screener queries and signal retrieval
- **TradeController**: Manages trade execution, monitoring, and risk configuration
- REST endpoints with OpenAPI documentation
- WebSocket gateways for real-time updates

### 2. Application Layer (Services)
- **ScreenerService**: Orchestrates screener queries and signal aggregation
- **TradeService**: Manages trade lifecycle and execution
- **IndicatorService**: Interfaces with indicator calculation engines
- **BinanceService**: Binance API integration and operations
- **RiskService**: Risk validation and management

### 3. Data Layer (Database & Repositories)
- **TypeORM** for ORM abstraction
- **Entities**: API Keys, Risk Configs, Trades, Signals
- Support for SQLite (default) and PostgreSQL
- Encrypted storage for sensitive data

### 4. Cross-Cutting Concerns
- **LoggerService**: Structured logging with Winston
- **EncryptionService**: libsodium-based encryption
- **ValidationService**: Joi and Zod schema validation

## Data Flow

### Screener Query Flow
```
Client
  ↓
ScreenerController.queryScreener()
  ↓
ScreenerService.queryScreener()
  ├─→ IndicatorService.calculateIndicators()
  │    ├─→ HTTP call to indicator engine
  │    └─→ Local fallback calculation
  ├─→ aggregateSignals()
  └─→ Signal saved to database
  ↓
Response with analysis
```

### Trade Execution Flow
```
Client
  ↓
TradeController.executeTrade()
  ↓
TradeService.executeTrade()
  ├─→ RiskService.validateTrade()
  │    ├─→ Check position size
  │    ├─→ Check risk/reward ratio
  │    └─→ Return validation result
  ├─→ BinanceService.placeMarketOrder()
  │    └─→ Execute on Binance testnet/production
  ├─→ Trade record created in database
  └─→ WebSocket notification sent
  ↓
Response with trade details
```

### Signal Broadcasting Flow
```
New Signal Generated
  ↓
ScreenerGateway.broadcastSignalUpdate()
  ├─→ Emit to all subscribed WebSocket clients
  └─→ Update sent in real-time
```

## Module Structure

### ScreenerModule
Responsibilities:
- Screener queries with technical analysis
- Indicator calculation and aggregation
- Signal storage and retrieval
- WebSocket updates for signals

Components:
- ScreenerController
- ScreenerService
- IndicatorService
- ScreenerGateway
- Signal Entity

### TradeModule
Responsibilities:
- Trade execution and management
- Risk validation and controls
- Binance API integration
- Risk configuration management

Components:
- TradeController
- TradeService
- BinanceService
- RiskService
- Trade, RiskConfig, ApiKey Entities

### CommonModule
Responsibilities:
- Cross-cutting concerns
- Logging infrastructure
- Encryption utilities
- Input validation

Components:
- LoggerService
- EncryptionService
- ValidationService

### DatabaseModule
Responsibilities:
- Database connection setup
- Entity registration
- Migration management

Components:
- TypeORM Configuration
- Entity Definitions

## Key Design Patterns

### 1. Service Layer Pattern
All business logic is encapsulated in services, making it testable and reusable.

### 2. Dependency Injection
NestJS dependency injection container manages all services and their dependencies.

### 3. Repository Pattern
TypeORM repositories provide data access abstraction.

### 4. Gateway Pattern
WebSocket gateways handle real-time communication.

### 5. Strategy Pattern
Indicator calculation supports multiple backends (HTTP, gRPC, local).

### 6. Decorator Pattern
TypeORM decorators for entity definition and database constraints.

## Security Architecture

### 1. Encryption
- **Algorithm**: XChaCha20-Poly1305 (via libsodium.js)
- **Key Size**: 32 bytes minimum
- **Application**: API keys, secrets stored encrypted in database
- **Nonce**: Randomly generated for each encryption operation

### 2. Input Validation
- Joi schemas for request DTOs
- Zod for runtime type checking
- BadRequestException for validation errors

### 3. Risk Controls
- Position size limits enforced before trade execution
- Risk/reward ratio validation
- Stop loss and take profit calculations
- Maximum drawdown tracking

### 4. API Security
- Bearer token authentication (JWT ready)
- CORS headers
- Helmet.js for security headers
- Environment-based configuration

## Performance Considerations

### 1. Database
- Connection pooling via TypeORM
- Indexes on frequently queried fields (symbol, status, timestamp)
- Soft deletes for historical data preservation

### 2. Caching
- Indicator results cached locally before storage
- Signal status queries filtered by date range

### 3. Async Operations
- Non-blocking I/O for all external API calls
- Timeouts configured for indicator engine calls (10s)
- Graceful fallback to local calculations on timeout

### 4. WebSocket
- Connection pooling
- Selective broadcast based on subscriptions
- Ping/pong for connection health

## Scalability

### Horizontal Scaling
- Stateless API design
- External database (PostgreSQL) for multi-instance deployment
- WebSocket room-based subscriptions

### Vertical Scaling
- Async/await for concurrency
- Worker threads for CPU-intensive operations (if needed)
- Memory-efficient data structures

## Error Handling

### Strategy
1. **Validation Errors**: Return 400 with detailed messages
2. **Business Logic Errors**: Return 400-500 with reason
3. **External API Errors**: Log and fallback gracefully
4. **Unhandled Errors**: Return 500 with error tracking

### Fallback Mechanisms
- Indicator engine unavailable: Use local calculation
- Binance connection error: Queue trade for retry
- Database error: Return appropriate HTTP status

## Integration Points

### 1. Indicator Engine
- **Type**: HTTP/gRPC
- **Endpoint**: Configurable via INDICATOR_ENGINE_URL
- **Fallback**: Local synthetic calculation

### 2. Binance API
- **Type**: REST with WebSocket data feeds
- **Authentication**: API key/secret (encrypted)
- **Testnet**: Configurable via BINANCE_USE_TESTNET

### 3. LLM Service (Future)
- **Provider**: OpenAI API (configurable)
- **Purpose**: Market summary generation
- **Status**: Placeholder for future implementation

## Testing Strategy

### Unit Tests
- Service logic tested with mocked dependencies
- Repository operations tested with mock repositories
- 80%+ code coverage target

### Integration Tests
- Controller and service interaction
- Database operations with test database
- Binance API mocked for testnet compatibility

### Test Utilities
- Mock repositories
- Mock HTTP clients
- Fixture data generators

## Monitoring & Observability

### Logging
- Winston logger with multiple transports
- Console output for development
- File output for production (error.log, combined.log)
- Structured logging with context

### Metrics (Future)
- Prometheus metrics integration
- Request latency tracking
- Database query performance
- WebSocket connection statistics

### Alerting (Future)
- Email notifications for trade errors
- Webhook notifications for significant trades
- Slack integration for alerts

## Configuration Management

### Environment Variables
All configuration via `.env` file:
- Server settings (port, log level)
- Database connection
- API credentials
- Risk limits
- Feature flags

### Configuration Service
NestJS ConfigService provides typed access to environment variables.

## Deployment

### Docker
- Multi-stage Dockerfile for optimized image size
- Docker Compose for local development with PostgreSQL

### Environment-Specific
- Development: SQLite, debug logging
- Staging: PostgreSQL, standard logging
- Production: PostgreSQL, minimal logging, HTTPS

## Future Enhancements

### Short Term
- [ ] gRPC support for indicator engine
- [ ] Advanced signal confidence scoring
- [ ] Trade performance analytics dashboard

### Medium Term
- [ ] LLM market summary integration
- [ ] Automated signal execution
- [ ] Multi-exchange support
- [ ] Portfolio analytics

### Long Term
- [ ] Distributed system architecture
- [ ] Machine learning integration
- [ ] Mobile app backend
- [ ] Real-time market data streams

## Compliance & Best Practices

### Code Quality
- TypeScript strict mode
- ESLint for code standards
- Prettier for formatting
- Unit test coverage requirements

### Security
- OWASP Top 10 compliance
- Regular dependency updates
- Secret management best practices
- Encryption for sensitive data

### Documentation
- API documentation via Swagger/OpenAPI
- Code comments for complex logic
- Architecture documentation
- Setup and deployment guides
