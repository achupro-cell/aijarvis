import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';
import { LoggerService } from '../common/logger/logger.service';
import { ScreenerQueryDto } from './dto/screener.dto';

@Injectable()
export class IndicatorService {
  private indicatorEngineUrl: string;
  private indicatorEngineType: string;

  constructor(
    private configService: ConfigService,
    private logger: LoggerService,
  ) {
    this.indicatorEngineUrl = this.configService.get<string>(
      'INDICATOR_ENGINE_URL',
      'http://localhost:3001',
    );
    this.indicatorEngineType = this.configService.get<string>(
      'INDICATOR_ENGINE_TYPE',
      'http',
    );
  }

  async calculateIndicators(
    dto: ScreenerQueryDto,
  ): Promise<Record<string, any>> {
    this.logger.debug(
      `Calculating indicators for ${dto.symbol} via ${this.indicatorEngineType}`,
    );

    if (this.indicatorEngineType === 'http') {
      return this.calculateViaHttp(dto);
    } else if (this.indicatorEngineType === 'grpc') {
      return this.calculateViaGrpc(dto);
    } else {
      return this.calculateLocally(dto);
    }
  }

  private async calculateViaHttp(
    dto: ScreenerQueryDto,
  ): Promise<Record<string, any>> {
    try {
      const response = await axios.post(
        `${this.indicatorEngineUrl}/calculate`,
        {
          symbol: dto.symbol,
          interval: dto.interval,
          limit: dto.limit,
          indicators: dto.indicators || ['RSI', 'MACD', 'BB', 'MA'],
        },
        { timeout: 10000 },
      );

      return response.data;
    } catch (error) {
      this.logger.warn(
        `Indicator engine HTTP call failed: ${error.message}. Using local calculation.`,
      );
      return this.calculateLocally(dto);
    }
  }

  private async calculateViaGrpc(
    dto: ScreenerQueryDto,
  ): Promise<Record<string, any>> {
    // gRPC implementation would go here
    // For now, fallback to local calculation
    this.logger.debug('gRPC not yet implemented, using local calculation');
    return this.calculateLocally(dto);
  }

  private calculateLocally(dto: ScreenerQueryDto): Record<string, any> {
    // Mock calculation with synthetic data
    const mockPrice = 45000 + Math.random() * 1000;

    return {
      symbol: dto.symbol,
      interval: dto.interval,
      current_price: mockPrice,
      rsi: 30 + Math.random() * 40, // Mock RSI between 30-70
      macd: {
        macd: 100 + Math.random() * 50,
        signal: 100 + Math.random() * 50,
        histogram: (Math.random() - 0.5) * 20,
      },
      bb: {
        upper: mockPrice * 1.02,
        middle: mockPrice,
        lower: mockPrice * 0.98,
      },
      ma: {
        ma20: mockPrice * 0.99,
        ma50: mockPrice * 0.98,
        ma200: mockPrice * 0.97,
      },
      volume: 1000000 + Math.random() * 500000,
      timestamp: new Date(),
    };
  }
}
