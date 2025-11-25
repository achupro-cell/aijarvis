import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { ScreenerService } from '../src/screener/screener.service';
import { IndicatorService } from '../src/screener/indicator.service';
import { Signal, SignalType } from '../src/database/entities/signal.entity';
import { LoggerService } from '../src/common/logger/logger.service';

describe('ScreenerService', () => {
  let service: ScreenerService;
  let mockSignalRepository: any;
  let mockIndicatorService: any;
  let mockLoggerService: any;

  beforeEach(async () => {
    mockSignalRepository = {
      create: jest.fn((dto) => dto),
      save: jest.fn((signal) => Promise.resolve(signal)),
      findOne: jest.fn(),
      createQueryBuilder: jest.fn(),
    };

    mockIndicatorService = {
      calculateIndicators: jest.fn().mockResolvedValue({
        symbol: 'BTCUSDT',
        current_price: 45000,
        rsi: 45,
        macd: {
          macd: 100,
          signal: 95,
          histogram: 5,
        },
        bb: {
          upper: 46000,
          middle: 45000,
          lower: 44000,
        },
        ma: {
          ma20: 44500,
          ma50: 43000,
          ma200: 40000,
        },
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
        ScreenerService,
        {
          provide: getRepositoryToken(Signal),
          useValue: mockSignalRepository,
        },
        {
          provide: IndicatorService,
          useValue: mockIndicatorService,
        },
        {
          provide: LoggerService,
          useValue: mockLoggerService,
        },
      ],
    }).compile();

    service = module.get<ScreenerService>(ScreenerService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('queryScreener', () => {
    it('should return screener analysis with signal', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        interval: '1h',
        limit: 100,
        indicators: ['RSI', 'MACD', 'BB', 'MA'],
      };

      const result = await service.queryScreener(dto);

      expect(result).toHaveProperty('symbol', 'BTCUSDT');
      expect(result).toHaveProperty('currentPrice', 45000);
      expect(result).toHaveProperty('signal');
      expect(result.signal).toHaveProperty('type');
      expect(result.signal).toHaveProperty('confidence');
      expect(result.signal).toHaveProperty('reasoning');
    });

    it('should create a signal record', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        interval: '1h',
        limit: 100,
      };

      await service.queryScreener(dto);

      expect(mockSignalRepository.save).toHaveBeenCalled();
      const savedSignal = mockSignalRepository.save.mock.calls[0][0];
      expect(savedSignal.symbol).toBe('BTCUSDT');
      expect(savedSignal).toHaveProperty('signalType');
      expect(savedSignal).toHaveProperty('confidence');
    });

    it('should aggregate bullish signals correctly', async () => {
      mockIndicatorService.calculateIndicators.mockResolvedValueOnce({
        symbol: 'BTCUSDT',
        current_price: 45000,
        rsi: 25, // Oversold - bullish
        macd: {
          macd: 110,
          signal: 100,
          histogram: 10, // Positive - bullish
        },
        bb: {
          upper: 46000,
          middle: 45000,
          lower: 44000,
        },
        ma: {
          ma20: 44500,
          ma50: 43000,
          ma200: 40000,
        },
      });

      const dto = {
        symbol: 'BTCUSDT',
        interval: '1h',
        limit: 100,
      };

      const result = await service.queryScreener(dto);

      expect(result.signal.type).toBe(SignalType.STRONG_BUY);
      expect(result.signal.confidence).toBeGreaterThan(50);
    });

    it('should aggregate bearish signals correctly', async () => {
      mockIndicatorService.calculateIndicators.mockResolvedValueOnce({
        symbol: 'BTCUSDT',
        current_price: 45000,
        rsi: 75, // Overbought - bearish
        macd: {
          macd: 90,
          signal: 100,
          histogram: -10, // Negative - bearish
        },
        bb: {
          upper: 46000,
          middle: 45000,
          lower: 44000,
        },
        ma: {
          ma20: 45500,
          ma50: 46000,
          ma200: 47000,
        },
      });

      const dto = {
        symbol: 'BTCUSDT',
        interval: '1h',
        limit: 100,
      };

      const result = await service.queryScreener(dto);

      expect(result.signal.type).toBe(SignalType.STRONG_SELL);
      expect(result.signal.confidence).toBeGreaterThan(50);
    });
  });

  describe('getSignals', () => {
    it('should return signals without filter', async () => {
      const mockSignals = [
        { id: '1', symbol: 'BTCUSDT' },
        { id: '2', symbol: 'ETHUSDT' },
      ];

      mockSignalRepository.createQueryBuilder.mockReturnValue({
        where: jest.fn().mockReturnThis(),
        orderBy: jest.fn().mockReturnThis(),
        take: jest.fn().mockReturnThis(),
        getMany: jest.fn().mockResolvedValue(mockSignals),
      });

      const result = await service.getSignals();

      expect(result).toEqual(mockSignals);
    });

    it('should filter signals by symbol', async () => {
      const mockSignals = [{ id: '1', symbol: 'BTCUSDT' }];

      mockSignalRepository.createQueryBuilder.mockReturnValue({
        where: jest.fn().mockReturnThis(),
        orderBy: jest.fn().mockReturnThis(),
        take: jest.fn().mockReturnThis(),
        getMany: jest.fn().mockResolvedValue(mockSignals),
      });

      const result = await service.getSignals('BTCUSDT');

      expect(result).toEqual(mockSignals);
    });
  });

  describe('getSignalStatus', () => {
    it('should return most recent signal for symbol', async () => {
      const mockSignal = {
        id: '1',
        symbol: 'BTCUSDT',
        signalType: SignalType.BUY,
      };

      mockSignalRepository.findOne.mockResolvedValue(mockSignal);

      const result = await service.getSignalStatus('BTCUSDT');

      expect(result).toEqual(mockSignal);
      expect(mockSignalRepository.findOne).toHaveBeenCalledWith({
        where: { symbol: 'BTCUSDT' },
        order: { createdAt: 'DESC' },
      });
    });
  });
});
