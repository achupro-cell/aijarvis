import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Signal, SignalType } from '../database/entities/signal.entity';
import { IndicatorService } from './indicator.service';
import { LoggerService } from '../common/logger/logger.service';
import { ScreenerQueryDto, ScreenerResponseDto } from './dto/screener.dto';

@Injectable()
export class ScreenerService {
  constructor(
    @InjectRepository(Signal)
    private signalRepository: Repository<Signal>,
    private indicatorService: IndicatorService,
    private logger: LoggerService,
  ) {}

  async queryScreener(dto: ScreenerQueryDto): Promise<ScreenerResponseDto> {
    this.logger.debug(`Querying screener for ${dto.symbol} with interval ${dto.interval}`);

    try {
      // Get indicators data
      const indicatorsData = await this.indicatorService.calculateIndicators(dto);
      const currentPrice = indicatorsData.current_price || 0;

      // Aggregate signals from indicators
      const signal = this.aggregateSignals(indicatorsData);

      // Store signal in database
      await this.storeSignal({
        symbol: dto.symbol,
        signalType: signal.type as SignalType,
        confidence: signal.confidence,
        indicators: JSON.stringify(indicatorsData),
        reasoning: signal.reasoning,
      });

      return {
        symbol: dto.symbol,
        interval: dto.interval,
        currentPrice,
        indicators: indicatorsData,
        signal,
        timestamp: new Date(),
      };
    } catch (error) {
      this.logger.error(
        `Error querying screener for ${dto.symbol}: ${error.message}`,
        error.stack,
        'ScreenerService',
      );
      throw error;
    }
  }

  async getSignals(symbol?: string): Promise<Signal[]> {
    const query = this.signalRepository.createQueryBuilder('signal');

    if (symbol) {
      query.where('signal.symbol = :symbol', { symbol });
    }

    query.orderBy('signal.createdAt', 'DESC').take(100);

    return query.getMany();
  }

  async getSignalStatus(symbol: string): Promise<Signal | null> {
    return this.signalRepository.findOne({
      where: { symbol },
      order: { createdAt: 'DESC' },
    });
  }

  private aggregateSignals(
    indicatorsData: Record<string, any>,
  ): {
    type: SignalType;
    confidence: number;
    reasoning: string;
  } {
    const signals: { score: number; reasoning: string[] }[] = [];
    let totalScore = 0;
    const reasoning: string[] = [];

    // RSI signal
    if (indicatorsData.rsi) {
      const rsi = indicatorsData.rsi;
      if (rsi < 30) {
        totalScore += 2;
        reasoning.push('RSI oversold (< 30)');
      } else if (rsi > 70) {
        totalScore -= 2;
        reasoning.push('RSI overbought (> 70)');
      }
    }

    // MACD signal
    if (indicatorsData.macd) {
      const macd = indicatorsData.macd;
      if (macd.histogram > 0 && macd.macd > macd.signal) {
        totalScore += 1.5;
        reasoning.push('MACD bullish crossover');
      } else if (macd.histogram < 0 && macd.macd < macd.signal) {
        totalScore -= 1.5;
        reasoning.push('MACD bearish crossover');
      }
    }

    // Bollinger Bands signal
    if (indicatorsData.bb) {
      const price = indicatorsData.current_price;
      const bb = indicatorsData.bb;
      if (price < bb.lower) {
        totalScore += 1;
        reasoning.push('Price below lower Bollinger Band');
      } else if (price > bb.upper) {
        totalScore -= 1;
        reasoning.push('Price above upper Bollinger Band');
      }
    }

    // Moving Average signal
    if (indicatorsData.ma && indicatorsData.current_price) {
      const price = indicatorsData.current_price;
      const ma = indicatorsData.ma;
      if (price > ma.ma20 && ma.ma20 > ma.ma50) {
        totalScore += 1;
        reasoning.push('Price above MA20, MA20 above MA50 (uptrend)');
      } else if (price < ma.ma20 && ma.ma20 < ma.ma50) {
        totalScore -= 1;
        reasoning.push('Price below MA20, MA20 below MA50 (downtrend)');
      }
    }

    // Determine signal type and confidence
    const confidence = Math.min(100, Math.max(0, 50 + totalScore * 10));
    let signalType: SignalType;

    if (totalScore >= 4) {
      signalType = SignalType.STRONG_BUY;
    } else if (totalScore > 0) {
      signalType = SignalType.BUY;
    } else if (totalScore <= -4) {
      signalType = SignalType.STRONG_SELL;
    } else if (totalScore < 0) {
      signalType = SignalType.SELL;
    } else {
      signalType = SignalType.NEUTRAL;
    }

    return {
      type: signalType,
      confidence,
      reasoning: reasoning.join('; '),
    };
  }

  private async storeSignal(data: {
    symbol: string;
    signalType: SignalType;
    confidence: number;
    indicators: string;
    reasoning: string;
  }): Promise<Signal> {
    const signal = this.signalRepository.create(data);
    return this.signalRepository.save(signal);
  }
}
