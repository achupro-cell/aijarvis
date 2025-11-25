import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { BadRequestException } from '@nestjs/common';
import { TradeService } from '../src/trade/trade.service';
import { BinanceService } from '../src/trade/binance.service';
import { RiskService } from '../src/trade/risk.service';
import { Trade, TradeStatus } from '../src/database/entities/trade.entity';
import { LoggerService } from '../src/common/logger/logger.service';

describe('TradeService', () => {
  let service: TradeService;
  let mockTradeRepository: any;
  let mockBinanceService: any;
  let mockRiskService: any;
  let mockLoggerService: any;

  beforeEach(async () => {
    mockTradeRepository = {
      create: jest.fn((dto) => ({ ...dto, id: 'test-id' })),
      save: jest.fn((trade) => Promise.resolve(trade)),
      findOne: jest.fn(),
      createQueryBuilder: jest.fn(),
      find: jest.fn(),
    };

    mockBinanceService = {
      initializeClient: jest.fn().mockResolvedValue(undefined),
      getCurrentPrice: jest.fn().mockResolvedValue(45000),
      placeMarketOrder: jest.fn().mockResolvedValue({
        orderId: 123456,
        symbol: 'BTCUSDT',
        side: 'BUY',
      }),
      getBalance: jest.fn().mockResolvedValue({
        free: '1.5',
        locked: '0',
      }),
    };

    mockRiskService = {
      validateTrade: jest.fn().mockResolvedValue({
        isValid: true,
      }),
    };

    mockLoggerService = {
      debug: jest.fn(),
      log: jest.fn(),
      error: jest.fn(),
      warn: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        TradeService,
        {
          provide: getRepositoryToken(Trade),
          useValue: mockTradeRepository,
        },
        {
          provide: BinanceService,
          useValue: mockBinanceService,
        },
        {
          provide: RiskService,
          useValue: mockRiskService,
        },
        {
          provide: LoggerService,
          useValue: mockLoggerService,
        },
      ],
    }).compile();

    service = module.get<TradeService>(TradeService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('executeTrade', () => {
    it('should execute a trade successfully', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        side: 'buy',
        quantity: 0.5,
        entryPrice: 45000,
      };

      const result = await service.executeTrade(dto);

      expect(result).toHaveProperty('id');
      expect(result.symbol).toBe('BTCUSDT');
      expect(result.side).toBe('buy');
      expect(result.quantity).toBe(0.5);
      expect(result.status).toBe(TradeStatus.OPENED);
    });

    it('should validate trade before execution', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        side: 'buy',
        quantity: 0.5,
        entryPrice: 45000,
      };

      await service.executeTrade(dto);

      expect(mockRiskService.validateTrade).toHaveBeenCalledWith(
        'BTCUSDT',
        0.5,
        45000,
        undefined,
      );
    });

    it('should throw error if risk validation fails', async () => {
      mockRiskService.validateTrade.mockResolvedValue({
        isValid: false,
        reason: 'Position size exceeds maximum',
      });

      const dto = {
        symbol: 'BTCUSDT',
        side: 'buy',
        quantity: 100, // Very large position
        entryPrice: 45000,
      };

      await expect(service.executeTrade(dto)).rejects.toThrow(BadRequestException);
    });

    it('should place order on Binance', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        side: 'buy',
        quantity: 0.5,
        entryPrice: 45000,
      };

      await service.executeTrade(dto);

      expect(mockBinanceService.placeMarketOrder).toHaveBeenCalledWith(
        'BTCUSDT',
        'BUY',
        0.5,
      );
    });
  });

  describe('closeTrade', () => {
    it('should close an open trade', async () => {
      const mockTrade = {
        id: 'test-id',
        symbol: 'BTCUSDT',
        entryPrice: 45000,
        status: TradeStatus.OPENED,
        quantity: 0.5,
      };

      mockTradeRepository.findOne.mockResolvedValue(mockTrade);

      const result = await service.closeTrade('test-id', 46000);

      expect(result.status).toBe(TradeStatus.CLOSED);
      expect(result.exitPrice).toBe(46000);
      expect(result.profitLossPercent).toBeCloseTo(2.22, 1);
    });

    it('should throw error if trade not found', async () => {
      mockTradeRepository.findOne.mockResolvedValue(null);

      await expect(service.closeTrade('non-existent')).rejects.toThrow(
        BadRequestException,
      );
    });

    it('should throw error if trade already closed', async () => {
      const mockTrade = {
        id: 'test-id',
        status: TradeStatus.CLOSED,
      };

      mockTradeRepository.findOne.mockResolvedValue(mockTrade);

      await expect(service.closeTrade('test-id')).rejects.toThrow(
        BadRequestException,
      );
    });

    it('should use current price if exitPrice not provided', async () => {
      const mockTrade = {
        id: 'test-id',
        symbol: 'BTCUSDT',
        entryPrice: 45000,
        status: TradeStatus.OPENED,
        quantity: 0.5,
      };

      mockTradeRepository.findOne.mockResolvedValue(mockTrade);

      await service.closeTrade('test-id');

      expect(mockBinanceService.getCurrentPrice).toHaveBeenCalledWith('BTCUSDT');
    });
  });

  describe('getTrade', () => {
    it('should return trade by id', async () => {
      const mockTrade = { id: 'test-id', symbol: 'BTCUSDT' };

      mockTradeRepository.findOne.mockResolvedValue(mockTrade);

      const result = await service.getTrade('test-id');

      expect(result).toEqual(mockTrade);
    });
  });

  describe('getTrades', () => {
    it('should return all trades', async () => {
      const mockTrades = [
        { id: '1', symbol: 'BTCUSDT' },
        { id: '2', symbol: 'ETHUSDT' },
      ];

      const mockQuery = {
        where: jest.fn().mockReturnThis(),
        andWhere: jest.fn().mockReturnThis(),
        orderBy: jest.fn().mockReturnThis(),
        take: jest.fn().mockReturnThis(),
        getMany: jest.fn().mockResolvedValue(mockTrades),
      };

      mockTradeRepository.createQueryBuilder.mockReturnValue(mockQuery);

      const result = await service.getTrades();

      expect(result).toEqual(mockTrades);
    });

    it('should filter trades by symbol', async () => {
      const mockTrades = [{ id: '1', symbol: 'BTCUSDT' }];

      const mockQuery = {
        where: jest.fn().mockReturnThis(),
        andWhere: jest.fn().mockReturnThis(),
        orderBy: jest.fn().mockReturnThis(),
        take: jest.fn().mockReturnThis(),
        getMany: jest.fn().mockResolvedValue(mockTrades),
      };

      mockTradeRepository.createQueryBuilder.mockReturnValue(mockQuery);

      const result = await service.getTrades('BTCUSDT');

      expect(result).toEqual(mockTrades);
      expect(mockQuery.where).toHaveBeenCalled();
    });
  });

  describe('getTradeStats', () => {
    it('should return trade statistics', async () => {
      const mockTrades = [
        {
          id: '1',
          status: TradeStatus.CLOSED,
          profitLossPercent: 5,
          entryPrice: 45000,
          exitPrice: 47250,
          quantity: 0.5,
        },
        {
          id: '2',
          status: TradeStatus.CLOSED,
          profitLossPercent: -2,
          entryPrice: 46000,
          exitPrice: 45080,
          quantity: 0.5,
        },
        {
          id: '3',
          status: TradeStatus.OPENED,
          profitLossPercent: null,
          entryPrice: 45500,
          quantity: 0.5,
        },
      ];

      mockTradeRepository.find.mockResolvedValue(mockTrades);

      const result = await service.getTradeStats();

      expect(result.totalTrades).toBe(3);
      expect(result.openTrades).toBe(1);
      expect(result.closedTrades).toBe(2);
      expect(result.profitableTrades).toBe(1);
      expect(result.totalPnL).toBeGreaterThan(0);
    });
  });
});
