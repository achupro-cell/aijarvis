import { Test, TestingModule } from '@nestjs/testing';
import { TradeController } from '../src/trade/trade.controller';
import { TradeService } from '../src/trade/trade.service';
import { BinanceService } from '../src/trade/binance.service';
import { RiskService } from '../src/trade/risk.service';
import { TradeStatus } from '../src/database/entities/trade.entity';

describe('TradeController', () => {
  let controller: TradeController;
  let tradeService: TradeService;
  let binanceService: BinanceService;
  let riskService: RiskService;

  const mockTradeService = {
    executeTrade: jest.fn(),
    closeTrade: jest.fn(),
    getTrade: jest.fn(),
    getTrades: jest.fn(),
    getOpenTrades: jest.fn(),
    getTradeStats: jest.fn(),
  };

  const mockBinanceService = {
    saveApiKey: jest.fn(),
    getBalance: jest.fn(),
    getCurrentPrice: jest.fn(),
  };

  const mockRiskService = {
    createRiskConfig: jest.fn(),
    getRiskConfig: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [TradeController],
      providers: [
        {
          provide: TradeService,
          useValue: mockTradeService,
        },
        {
          provide: BinanceService,
          useValue: mockBinanceService,
        },
        {
          provide: RiskService,
          useValue: mockRiskService,
        },
      ],
    }).compile();

    controller = module.get<TradeController>(TradeController);
    tradeService = module.get<TradeService>(TradeService);
    binanceService = module.get<BinanceService>(BinanceService);
    riskService = module.get<RiskService>(RiskService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('POST /api/trade/execute', () => {
    it('should execute a trade', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        side: 'buy',
        quantity: 0.5,
        entryPrice: 45000,
      };

      const expectedResponse = {
        id: 'trade-id',
        symbol: 'BTCUSDT',
        side: 'buy',
        quantity: 0.5,
        entryPrice: 45000,
        status: TradeStatus.OPENED,
        createdAt: new Date(),
      };

      mockTradeService.executeTrade.mockResolvedValue(expectedResponse);

      const result = await controller.executeTrade(dto);

      expect(result).toEqual(expectedResponse);
      expect(tradeService.executeTrade).toHaveBeenCalledWith(dto);
    });
  });

  describe('PUT /api/trade/:id/close', () => {
    it('should close a trade', async () => {
      const expectedResponse = {
        id: 'trade-id',
        status: TradeStatus.CLOSED,
        exitPrice: 46000,
        profitLossPercent: 2.22,
      };

      mockTradeService.closeTrade.mockResolvedValue(expectedResponse);

      const result = await controller.closeTrade('trade-id', 46000);

      expect(result).toEqual(expectedResponse);
      expect(tradeService.closeTrade).toHaveBeenCalledWith('trade-id', 46000);
    });
  });

  describe('GET /api/trade/:id', () => {
    it('should get trade details', async () => {
      const mockTrade = {
        id: 'trade-id',
        symbol: 'BTCUSDT',
        status: TradeStatus.OPENED,
      };

      mockTradeService.getTrade.mockResolvedValue(mockTrade);

      const result = await controller.getTrade('trade-id');

      expect(result).toEqual(mockTrade);
      expect(tradeService.getTrade).toHaveBeenCalledWith('trade-id');
    });
  });

  describe('GET /api/trade', () => {
    it('should list trades', async () => {
      const mockTrades = [
        { id: '1', symbol: 'BTCUSDT' },
        { id: '2', symbol: 'ETHUSDT' },
      ];

      mockTradeService.getTrades.mockResolvedValue(mockTrades);

      const result = await controller.getTrades();

      expect(result).toEqual(mockTrades);
      expect(tradeService.getTrades).toHaveBeenCalled();
    });

    it('should filter trades by symbol', async () => {
      const mockTrades = [{ id: '1', symbol: 'BTCUSDT' }];

      mockTradeService.getTrades.mockResolvedValue(mockTrades);

      const result = await controller.getTrades('BTCUSDT');

      expect(result).toEqual(mockTrades);
      expect(tradeService.getTrades).toHaveBeenCalledWith('BTCUSDT', undefined);
    });
  });

  describe('GET /api/trade/open/list', () => {
    it('should get open trades', async () => {
      const mockTrades = [
        { id: '1', status: TradeStatus.OPENED },
        { id: '2', status: TradeStatus.OPENED },
      ];

      mockTradeService.getOpenTrades.mockResolvedValue(mockTrades);

      const result = await controller.getOpenTrades();

      expect(result).toEqual(mockTrades);
      expect(tradeService.getOpenTrades).toHaveBeenCalled();
    });
  });

  describe('GET /api/trade/stats/summary', () => {
    it('should return trade statistics', async () => {
      const mockStats = {
        totalTrades: 10,
        openTrades: 2,
        closedTrades: 8,
        profitableTrades: 6,
        totalPnL: 5000,
      };

      mockTradeService.getTradeStats.mockResolvedValue(mockStats);

      const result = await controller.getTradeStats();

      expect(result).toEqual(mockStats);
      expect(tradeService.getTradeStats).toHaveBeenCalled();
    });
  });

  describe('POST /api/trade/risk-config', () => {
    it('should create risk configuration', async () => {
      const dto = {
        name: 'aggressive',
        maxPositionSize: 20000,
        maxDrawdownPercent: 30,
        stopLossPercent: 3,
        takeProfitPercent: 15,
        riskRewardRatio: 3,
      };

      const expectedResponse = {
        id: 'config-id',
        ...dto,
      };

      mockRiskService.createRiskConfig.mockResolvedValue(expectedResponse);

      const result = await controller.createRiskConfig(dto);

      expect(result).toEqual(expectedResponse);
      expect(riskService.createRiskConfig).toHaveBeenCalledWith(dto);
    });
  });

  describe('GET /api/trade/risk-config/:id', () => {
    it('should get risk configuration', async () => {
      const mockConfig = {
        id: 'config-id',
        name: 'default',
        maxPositionSize: 10000,
      };

      mockRiskService.getRiskConfig.mockResolvedValue(mockConfig);

      const result = await controller.getRiskConfig('config-id');

      expect(result).toEqual(mockConfig);
      expect(riskService.getRiskConfig).toHaveBeenCalledWith('config-id');
    });
  });

  describe('POST /api/trade/api-keys', () => {
    it('should add API credentials', async () => {
      const dto = {
        name: 'binance-main',
        exchange: 'binance',
        apiKey: 'test-key',
        apiSecret: 'test-secret',
        isTestnet: true,
      };

      const expectedResponse = {
        id: 'key-id',
        name: 'binance-main',
      };

      mockBinanceService.saveApiKey.mockResolvedValue(expectedResponse);

      const result = await controller.addApiKey(dto);

      expect(result).toEqual(expectedResponse);
      expect(binanceService.saveApiKey).toHaveBeenCalledWith(
        'binance-main',
        'test-key',
        'test-secret',
        true,
      );
    });
  });

  describe('GET /api/trade/binance/balance', () => {
    it('should get Binance balance', async () => {
      const mockBalance = {
        free: '1.5',
        locked: '0.5',
      };

      mockBinanceService.getBalance.mockResolvedValue(mockBalance);

      const result = await controller.getBinanceBalance('USDT');

      expect(result).toEqual(mockBalance);
      expect(binanceService.getBalance).toHaveBeenCalledWith('USDT');
    });
  });

  describe('GET /api/trade/binance/price/:symbol', () => {
    it('should get current price', async () => {
      mockBinanceService.getCurrentPrice.mockResolvedValue(45000);

      const result = await controller.getBinancePrice('BTCUSDT');

      expect(result).toBe(45000);
      expect(binanceService.getCurrentPrice).toHaveBeenCalledWith('BTCUSDT');
    });
  });
});
