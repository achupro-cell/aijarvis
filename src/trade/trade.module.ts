import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TradeController } from './trade.controller';
import { TradeService } from './trade.service';
import { BinanceService } from './binance.service';
import { RiskService } from './risk.service';
import { Trade } from '../database/entities/trade.entity';
import { RiskConfig } from '../database/entities/risk-config.entity';
import { ApiKey } from '../database/entities/api-key.entity';
import { CommonModule } from '../common/common.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Trade, RiskConfig, ApiKey]),
    CommonModule,
  ],
  controllers: [TradeController],
  providers: [TradeService, BinanceService, RiskService],
  exports: [TradeService, BinanceService, RiskService],
})
export class TradeModule {}
