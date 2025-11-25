import { Injectable, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Trade, TradeStatus } from '../database/entities/trade.entity';
import { BinanceService } from './binance.service';
import { RiskService } from './risk.service';
import { LoggerService } from '../common/logger/logger.service';
import { ExecuteTradeDto, TradeExecutionResponseDto } from './dto/trade.dto';

@Injectable()
export class TradeService {
  constructor(
    @InjectRepository(Trade)
    private tradeRepository: Repository<Trade>,
    private binanceService: BinanceService,
    private riskService: RiskService,
    private logger: LoggerService,
  ) {}

  async executeTrade(dto: ExecuteTradeDto): Promise<TradeExecutionResponseDto> {
    this.logger.debug(`Executing trade: ${dto.symbol} ${dto.side}`, {
      quantity: dto.quantity,
      entryPrice: dto.entryPrice,
    });

    // Validate trade with risk controls
    const validation = await this.riskService.validateTrade(
      dto.symbol,
      dto.quantity,
      dto.entryPrice,
      dto.riskConfigId,
    );

    if (!validation.isValid) {
      throw new BadRequestException(validation.reason);
    }

    try {
      // Initialize Binance client
      await this.binanceService.initializeClient();

      // Get current price
      const currentPrice = await this.binanceService.getCurrentPrice(dto.symbol);

      // Place order on Binance
      const binanceOrder = await this.binanceService.placeMarketOrder(
        dto.symbol,
        dto.side.toUpperCase() as 'BUY' | 'SELL',
        dto.quantity,
      );

      // Create trade record
      const trade = this.tradeRepository.create({
        symbol: dto.symbol,
        side: dto.side,
        quantity: dto.quantity,
        entryPrice: currentPrice,
        status: TradeStatus.OPENED,
        riskConfigId: dto.riskConfigId,
        binanceOrderId: binanceOrder.orderId?.toString(),
        notes: dto.notes,
      });

      const savedTrade = await this.tradeRepository.save(trade);

      this.logger.log(`Trade executed successfully: ${savedTrade.id}`, {
        symbol: dto.symbol,
        binanceOrderId: binanceOrder.orderId,
      });

      return {
        id: savedTrade.id,
        symbol: savedTrade.symbol,
        side: savedTrade.side,
        quantity: savedTrade.quantity,
        entryPrice: savedTrade.entryPrice,
        status: savedTrade.status,
        binanceOrderId: savedTrade.binanceOrderId,
        createdAt: savedTrade.createdAt,
      };
    } catch (error) {
      this.logger.error(`Trade execution failed: ${error.message}`, error.stack);
      throw error;
    }
  }

  async closeTrade(
    tradeId: string,
    exitPrice?: number,
  ): Promise<Trade> {
    const trade = await this.tradeRepository.findOne({ where: { id: tradeId } });

    if (!trade) {
      throw new BadRequestException('Trade not found');
    }

    if (trade.status === TradeStatus.CLOSED) {
      throw new BadRequestException('Trade is already closed');
    }

    try {
      const exitPriceToUse = exitPrice || await this.binanceService.getCurrentPrice(trade.symbol);

      const profitLossPercent =
        ((exitPriceToUse - trade.entryPrice) / trade.entryPrice) * 100;

      trade.exitPrice = exitPriceToUse;
      trade.profitLossPercent = profitLossPercent;
      trade.status = TradeStatus.CLOSED;
      trade.closedAt = new Date();

      const closedTrade = await this.tradeRepository.save(trade);

      this.logger.log(`Trade closed: ${tradeId}`, {
        profitLoss: profitLossPercent,
        exitPrice: exitPriceToUse,
      });

      return closedTrade;
    } catch (error) {
      this.logger.error(`Failed to close trade: ${error.message}`, error.stack);
      throw error;
    }
  }

  async getTrade(id: string): Promise<Trade | null> {
    return this.tradeRepository.findOne({ where: { id } });
  }

  async getTrades(symbol?: string, status?: TradeStatus): Promise<Trade[]> {
    const query = this.tradeRepository.createQueryBuilder('trade');

    if (symbol) {
      query.where('trade.symbol = :symbol', { symbol });
    }

    if (status) {
      query.andWhere('trade.status = :status', { status });
    }

    query.orderBy('trade.createdAt', 'DESC').take(100);

    return query.getMany();
  }

  async getOpenTrades(): Promise<Trade[]> {
    return this.getTrades(undefined, TradeStatus.OPENED);
  }

  async getTradeStats(): Promise<{
    totalTrades: number;
    openTrades: number;
    closedTrades: number;
    profitableTrades: number;
    totalPnL: number;
  }> {
    const allTrades = await this.tradeRepository.find();
    const openTrades = allTrades.filter(
      (t) => t.status === TradeStatus.OPENED,
    );
    const closedTrades = allTrades.filter(
      (t) => t.status === TradeStatus.CLOSED,
    );
    const profitableTrades = closedTrades.filter(
      (t) => (t.profitLossPercent || 0) > 0,
    );

    const totalPnL = closedTrades.reduce((sum, trade) => {
      if (trade.exitPrice && trade.entryPrice) {
        return sum + (trade.exitPrice - trade.entryPrice) * trade.quantity;
      }
      return sum;
    }, 0);

    return {
      totalTrades: allTrades.length,
      openTrades: openTrades.length,
      closedTrades: closedTrades.length,
      profitableTrades: profitableTrades.length,
      totalPnL,
    };
  }
}
