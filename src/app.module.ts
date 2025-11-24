import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { DatabaseModule } from './database/database.module';
import { CommonModule } from './common/common.module';
import { ScreenerModule } from './screener/screener.module';
import { TradeModule } from './trade/trade.module';
import { ConfigService } from '@nestjs/config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    DatabaseModule,
    CommonModule,
    ScreenerModule,
    TradeModule,
  ],
})
export class AppModule {}
