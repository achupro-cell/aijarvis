import { IsString, IsNumber, IsEnum, IsOptional } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export enum TradeDirection {
  BUY = 'buy',
  SELL = 'sell',
}

export class ExecuteTradeDto {
  @ApiProperty({ example: 'BTCUSDT', description: 'Trading symbol' })
  @IsString()
  symbol: string;

  @ApiProperty({ enum: TradeDirection, description: 'Trade direction' })
  @IsEnum(TradeDirection)
  side: TradeDirection;

  @ApiProperty({ example: 0.5, description: 'Quantity to trade' })
  @IsNumber()
  quantity: number;

  @ApiProperty({ example: 45000, description: 'Entry price' })
  @IsNumber()
  entryPrice: number;

  @ApiProperty({
    example: 'risk-config-uuid',
    description: 'Risk config ID to apply',
    required: false,
  })
  @IsString()
  @IsOptional()
  riskConfigId?: string;

  @ApiProperty({
    example: 'Signal-based trade',
    description: 'Trade notes',
    required: false,
  })
  @IsString()
  @IsOptional()
  notes?: string;
}

export class RiskConfigDto {
  @ApiProperty({ example: 'default', description: 'Config name' })
  @IsString()
  name: string;

  @ApiProperty({ example: 10000, description: 'Max position size in USD' })
  @IsNumber()
  maxPositionSize: number;

  @ApiProperty({ example: 20, description: 'Max drawdown percentage' })
  @IsNumber()
  maxDrawdownPercent: number;

  @ApiProperty({ example: 5, description: 'Stop loss percentage' })
  @IsNumber()
  stopLossPercent: number;

  @ApiProperty({ example: 10, description: 'Take profit percentage' })
  @IsNumber()
  takeProfitPercent: number;

  @ApiProperty({ example: 2, description: 'Risk reward ratio' })
  @IsNumber()
  riskRewardRatio: number;
}

export class TradeExecutionResponseDto {
  @ApiProperty()
  id: string;

  @ApiProperty()
  symbol: string;

  @ApiProperty()
  side: string;

  @ApiProperty()
  quantity: number;

  @ApiProperty()
  entryPrice: number;

  @ApiProperty()
  status: string;

  @ApiProperty()
  binanceOrderId?: string;

  @ApiProperty()
  createdAt: Date;
}

export class ApiKeyDto {
  @ApiProperty({ example: 'binance-api', description: 'Name for this API key' })
  @IsString()
  name: string;

  @ApiProperty({ example: 'binance', description: 'Exchange name' })
  @IsString()
  exchange: string;

  @ApiProperty({ description: 'API Key' })
  @IsString()
  apiKey: string;

  @ApiProperty({ description: 'API Secret' })
  @IsString()
  apiSecret: string;

  @ApiProperty({ example: true, description: 'Use testnet/sandbox' })
  @IsOptional()
  isTestnet?: boolean;
}
