import { Injectable, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { RiskConfig } from '../database/entities/risk-config.entity';
import { LoggerService } from '../common/logger/logger.service';
import { ConfigService } from '@nestjs/config';
import { RiskConfigDto } from './dto/trade.dto';

export interface RiskValidationResult {
  isValid: boolean;
  reason?: string;
  maxQuantity?: number;
}

@Injectable()
export class RiskService {
  constructor(
    @InjectRepository(RiskConfig)
    private riskConfigRepository: Repository<RiskConfig>,
    private configService: ConfigService,
    private logger: LoggerService,
  ) {}

  async createRiskConfig(dto: RiskConfigDto): Promise<RiskConfig> {
    const config = this.riskConfigRepository.create(dto);
    return this.riskConfigRepository.save(config);
  }

  async getRiskConfig(id: string): Promise<RiskConfig | null> {
    return this.riskConfigRepository.findOne({ where: { id } });
  }

  async getDefaultRiskConfig(): Promise<RiskConfig> {
    let config = await this.riskConfigRepository.findOne({
      where: { name: 'default' },
    });

    if (!config) {
      config = this.riskConfigRepository.create({
        name: 'default',
        maxPositionSize: this.configService.get<number>('MAX_POSITION_SIZE', 10000),
        maxDrawdownPercent: this.configService.get<number>(
          'MAX_DRAWDOWN_PERCENT',
          20,
        ),
        stopLossPercent: this.configService.get<number>('STOP_LOSS_PERCENT', 5),
        takeProfitPercent: this.configService.get<number>(
          'TAKE_PROFIT_PERCENT',
          10,
        ),
        riskRewardRatio: 2,
      });
      config = await this.riskConfigRepository.save(config);
    }

    return config;
  }

  async validateTrade(
    symbol: string,
    quantity: number,
    entryPrice: number,
    riskConfigId?: string,
  ): Promise<RiskValidationResult> {
    const config = riskConfigId
      ? await this.getRiskConfig(riskConfigId)
      : await this.getDefaultRiskConfig();

    if (!config) {
      return {
        isValid: false,
        reason: 'Risk config not found',
      };
    }

    const positionValue = quantity * entryPrice;

    // Check max position size
    if (positionValue > config.maxPositionSize) {
      const maxQuantity = Math.floor(config.maxPositionSize / entryPrice);
      return {
        isValid: false,
        reason: `Position size ${positionValue} exceeds max ${config.maxPositionSize}`,
        maxQuantity,
      };
    }

    // Check risk reward ratio
    const stopLossPrice = entryPrice * (1 - config.stopLossPercent / 100);
    const riskAmount = (entryPrice - stopLossPrice) * quantity;

    const takeProfitPrice = entryPrice * (1 + config.takeProfitPercent / 100);
    const rewardAmount = (takeProfitPrice - entryPrice) * quantity;

    if (rewardAmount / riskAmount < config.riskRewardRatio) {
      return {
        isValid: false,
        reason: `Risk reward ratio ${rewardAmount / riskAmount} is below threshold ${config.riskRewardRatio}`,
      };
    }

    this.logger.debug(`Trade validation passed for ${symbol}`, {
      positionValue,
      maxSize: config.maxPositionSize,
      riskRewardRatio: rewardAmount / riskAmount,
    });

    return {
      isValid: true,
    };
  }

  calculateExitLevels(
    entryPrice: number,
    riskConfigId?: string,
  ): {
    stopLoss: number;
    takeProfit: number;
  } {
    const config = this.riskConfigRepository.create({
      maxPositionSize: this.configService.get<number>('MAX_POSITION_SIZE', 10000),
      maxDrawdownPercent: this.configService.get<number>(
        'MAX_DRAWDOWN_PERCENT',
        20,
      ),
      stopLossPercent: this.configService.get<number>('STOP_LOSS_PERCENT', 5),
      takeProfitPercent: this.configService.get<number>(
        'TAKE_PROFIT_PERCENT',
        10,
      ),
      riskRewardRatio: 2,
    });

    return {
      stopLoss: entryPrice * (1 - config.stopLossPercent / 100),
      takeProfit: entryPrice * (1 + config.takeProfitPercent / 100),
    };
  }
}
