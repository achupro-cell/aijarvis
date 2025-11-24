import { Test, TestingModule } from '@nestjs/testing';
import { ScreenerController } from '../src/screener/screener.controller';
import { ScreenerService } from '../src/screener/screener.service';
import { SignalType } from '../src/database/entities/signal.entity';

describe('ScreenerController', () => {
  let controller: ScreenerController;
  let service: ScreenerService;

  const mockScreenerService = {
    queryScreener: jest.fn(),
    getSignals: jest.fn(),
    getSignalStatus: jest.fn(),
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [ScreenerController],
      providers: [
        {
          provide: ScreenerService,
          useValue: mockScreenerService,
        },
      ],
    }).compile();

    controller = module.get<ScreenerController>(ScreenerController);
    service = module.get<ScreenerService>(ScreenerService);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('POST /api/screener/query', () => {
    it('should query screener and return analysis', async () => {
      const dto = {
        symbol: 'BTCUSDT',
        interval: '1h',
        limit: 100,
      };

      const expectedResponse = {
        symbol: 'BTCUSDT',
        interval: '1h',
        currentPrice: 45000,
        indicators: {
          rsi: 45,
          macd: { macd: 100, signal: 95, histogram: 5 },
        },
        signal: {
          type: SignalType.BUY,
          confidence: 65,
          reasoning: 'RSI oversold',
        },
        timestamp: new Date(),
      };

      mockScreenerService.queryScreener.mockResolvedValue(expectedResponse);

      const result = await controller.queryScreener(dto);

      expect(result).toEqual(expectedResponse);
      expect(service.queryScreener).toHaveBeenCalledWith(dto);
    });
  });

  describe('GET /api/screener/signals', () => {
    it('should return recent signals', async () => {
      const mockSignals = [
        { id: '1', symbol: 'BTCUSDT', signalType: SignalType.BUY },
        { id: '2', symbol: 'ETHUSDT', signalType: SignalType.SELL },
      ];

      mockScreenerService.getSignals.mockResolvedValue(mockSignals);

      const result = await controller.getSignals();

      expect(result).toEqual(mockSignals);
      expect(service.getSignals).toHaveBeenCalledWith(undefined);
    });

    it('should filter signals by symbol', async () => {
      const mockSignals = [
        { id: '1', symbol: 'BTCUSDT', signalType: SignalType.BUY },
      ];

      mockScreenerService.getSignals.mockResolvedValue(mockSignals);

      const result = await controller.getSignals('BTCUSDT');

      expect(result).toEqual(mockSignals);
      expect(service.getSignals).toHaveBeenCalledWith('BTCUSDT');
    });
  });

  describe('GET /api/screener/signal-status', () => {
    it('should return current signal status for symbol', async () => {
      const mockSignal = {
        id: '1',
        symbol: 'BTCUSDT',
        signalType: SignalType.BUY,
        confidence: 75,
      };

      mockScreenerService.getSignalStatus.mockResolvedValue(mockSignal);

      const result = await controller.getSignalStatus('BTCUSDT');

      expect(result).toEqual(mockSignal);
      expect(service.getSignalStatus).toHaveBeenCalledWith('BTCUSDT');
    });

    it('should return null if no signal found', async () => {
      mockScreenerService.getSignalStatus.mockResolvedValue(null);

      const result = await controller.getSignalStatus('NONEXISTENT');

      expect(result).toBeNull();
    });
  });
});
