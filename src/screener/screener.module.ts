import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ScreenerController } from './screener.controller';
import { ScreenerService } from './screener.service';
import { IndicatorService } from './indicator.service';
import { Signal } from '../database/entities/signal.entity';
import { CommonModule } from '../common/common.module';
import { ScreenerGateway } from './screener.gateway';

@Module({
  imports: [TypeOrmModule.forFeature([Signal]), CommonModule],
  controllers: [ScreenerController],
  providers: [ScreenerService, IndicatorService, ScreenerGateway],
  exports: [ScreenerService, IndicatorService],
})
export class ScreenerModule {}
