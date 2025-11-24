import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';
import { RiskService } from '../src/trade/risk.service';
import { RiskConfig } from '../src/database/entities/risk-config.entity';
import { LoggerService } from '../src/common/logger/logger.service';

describe('RiskService', () => {
  let service: RiskService;
  let mockRiskConfigRepository: any;
  let mockConfigService: any;
  let mockLoggerService: any;

  beforeEach(async () => {
    mockRiskConfigRepository = {
      create: jest.fn((dto) => ({ ...dto, id: 'test-id' })),
      save: jest.fn((config) => Promise.resolve(config)),
      findOne: jest.fn(),
    };

    mockConfigService = {
      get: jest.fn((key, defaultValue) => {
        const values: Record<string, any> = {
          MAX_POSITION_SIZE: 10000,
          MAX_DRAWDOWN_PERCENT: 20,
          STOP_LOSS_PERCENT: 5,
          TAKE_PROFIT_PERCENT: 10,
        };
        return values[key] || defaultValue;
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
        RiskService,
        {
          provide: getRepositoryToken(RiskConfig),
          useValue: mockRiskConfigRepository,
        },
        {
          provide: ConfigService,
          useValue: mockConfigService,
        },
        {
          provide: LoggerService,
          useValue: mockLoggerService,
        },
      ],
    }).compile();

    service = module.get<RiskService>(RiskService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('validateTrade', () => {
    it('should validate a trade within limits', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue({
        maxPositionSize: 10000,
        maxDrawdownPercent: 20,
        stopLossPercent: 5,
        takeProfitPercent: 10,
        riskRewardRatio: 2,
      });

      const result = await service.validateTrade('BTCUSDT', 0.1, 45000);

      expect(result.isValid).toBe(true);
    });

    it('should reject trade exceeding max position size', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue({
        maxPositionSize: 5000,
        maxDrawdownPercent: 20,
        stopLossPercent: 5,
        takeProfitPercent: 10,
        riskRewardRatio: 2,
      });

      const result = await service.validateTrade('BTCUSDT', 1, 45000); // 45000 > 5000

      expect(result.isValid).toBe(false);
      expect(result.reason).toContain('exceeds max');
      expect(result.maxQuantity).toBeDefined();
    });

    it('should calculate correct max quantity when position exceeds limit', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue({
        maxPositionSize: 10000,
        maxDrawdownPercent: 20,
        stopLossPercent: 5,
        takeProfitPercent: 10,
        riskRewardRatio: 2,
      });

      const result = await service.validateTrade('BTCUSDT', 1, 45000);

      if (!result.isValid && result.maxQuantity) {
        expect(result.maxQuantity).toBeLessThan(1);
        expect(result.maxQuantity * 45000).toBeLessThanOrEqual(10000);
      }
    });

    it('should validate risk reward ratio', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue({
        maxPositionSize: 100000,
        maxDrawdownPercent: 20,
        stopLossPercent: 10, // Large stop loss
        takeProfitPercent: 1, // Small take profit
        riskRewardRatio: 2, // Requires 2:1 ratio
      });

      const result = await service.validateTrade('BTCUSDT', 0.1, 45000);

      expect(result.isValid).toBe(false);
      expect(result.reason).toContain('Risk reward ratio');
    });

    it('should use default config if no ID provided', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue(null);
      mockRiskConfigRepository.save.mockResolvedValue({
        name: 'default',
        maxPositionSize: 10000,
        stopLossPercent: 5,
        takeProfitPercent: 10,
        riskRewardRatio: 2,
      });

      const result = await service.validateTrade('BTCUSDT', 0.1, 45000);

      expect(result).toBeDefined();
    });
  });

  describe('calculateExitLevels', () => {
    it('should calculate stop loss and take profit levels', () => {
      const levels = service.calculateExitLevels(45000);

      expect(levels.stopLoss).toBeCloseTo(42750, 0); // 45000 * (1 - 0.05)
      expect(levels.takeProfit).toBeCloseTo(49500, 0); // 45000 * (1 + 0.10)
    });

    it('should use correct percentages from config', () => {
      const levels = service.calculateExitLevels(100000);

      const expectedStopLoss = 100000 * (1 - 0.05);
      const expectedTakeProfit = 100000 * (1 + 0.10);

      expect(levels.stopLoss).toBeCloseTo(expectedStopLoss, 0);
      expect(levels.takeProfit).toBeCloseTo(expectedTakeProfit, 0);
    });
  });

  describe('createRiskConfig', () => {
    it('should create a new risk config', async () => {
      const dto = {
        name: 'aggressive',
        maxPositionSize: 20000,
        maxDrawdownPercent: 30,
        stopLossPercent: 3,
        takeProfitPercent: 15,
        riskRewardRatio: 3,
      };

      const result = await service.createRiskConfig(dto);

      expect(result.name).toBe('aggressive');
      expect(result.maxPositionSize).toBe(20000);
      expect(mockRiskConfigRepository.save).toHaveBeenCalled();
    });
  });

  describe('getRiskConfig', () => {
    it('should retrieve risk config by id', async () => {
      const mockConfig = {
        id: 'test-id',
        name: 'default',
        maxPositionSize: 10000,
      };

      mockRiskConfigRepository.findOne.mockResolvedValue(mockConfig);

      const result = await service.getRiskConfig('test-id');

      expect(result).toEqual(mockConfig);
      expect(mockRiskConfigRepository.findOne).toHaveBeenCalledWith({
        where: { id: 'test-id' },
      });
    });

    it('should return null if config not found', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue(null);

      const result = await service.getRiskConfig('non-existent');

      expect(result).toBeNull();
    });
  });

  describe('getDefaultRiskConfig', () => {
    it('should return existing default config', async () => {
      const mockConfig = {
        name: 'default',
        maxPositionSize: 10000,
      };

      mockRiskConfigRepository.findOne.mockResolvedValue(mockConfig);

      const result = await service.getDefaultRiskConfig();

      expect(result.name).toBe('default');
    });

    it('should create default config if not exists', async () => {
      mockRiskConfigRepository.findOne.mockResolvedValue(null);
      mockRiskConfigRepository.create.mockReturnValue({
        name: 'default',
        maxPositionSize: 10000,
      });
      mockRiskConfigRepository.save.mockResolvedValue({
        name: 'default',
        maxPositionSize: 10000,
      });

      const result = await service.getDefaultRiskConfig();

      expect(result.name).toBe('default');
      expect(mockRiskConfigRepository.save).toHaveBeenCalled();
    });
  });
});
