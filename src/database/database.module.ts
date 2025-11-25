import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';
import { ApiKey } from './entities/api-key.entity';
import { RiskConfig } from './entities/risk-config.entity';
import { Trade } from './entities/trade.entity';
import { Signal } from './entities/signal.entity';

@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      useFactory: (configService: ConfigService) => ({
        type: (configService.get<string>('DATABASE_TYPE') ||
          'sqlite') as any,
        host: configService.get<string>('DATABASE_HOST'),
        port: configService.get<number>('DATABASE_PORT'),
        username: configService.get<string>('DATABASE_USERNAME'),
        password: configService.get<string>('DATABASE_PASSWORD'),
        database: configService.get<string>('DATABASE_NAME') || 'crypto_screener.db',
        entities: [ApiKey, RiskConfig, Trade, Signal],
        synchronize: configService.get<boolean>('DATABASE_SYNCHRONIZE', true),
        logging: configService.get<boolean>('DATABASE_LOGGING', false),
      }),
      inject: [ConfigService],
    }),
    TypeOrmModule.forFeature([ApiKey, RiskConfig, Trade, Signal]),
  ],
  exports: [TypeOrmModule],
})
export class DatabaseModule {}
