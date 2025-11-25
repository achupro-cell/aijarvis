import { IsString, IsNumber, IsArray, IsOptional, Min, Max } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class ScreenerQueryDto {
  @ApiProperty({ example: 'BTCUSDT', description: 'Trading symbol' })
  @IsString()
  symbol: string;

  @ApiProperty({ example: '1h', description: 'Candle interval' })
  @IsString()
  interval: string;

  @ApiProperty({ example: 100, description: 'Number of candles to analyze' })
  @IsNumber()
  @Min(10)
  @Max(500)
  limit: number;

  @ApiProperty({ example: ['RSI', 'MACD', 'BB'], description: 'Indicators to calculate' })
  @IsArray()
  @IsOptional()
  indicators?: string[];
}

export class ScreenerResponseDto {
  @ApiProperty()
  symbol: string;

  @ApiProperty()
  interval: string;

  @ApiProperty()
  currentPrice: number;

  @ApiProperty()
  indicators: Record<string, any>;

  @ApiProperty()
  signal: {
    type: 'buy' | 'sell' | 'neutral';
    confidence: number;
    reasoning: string;
  };

  @ApiProperty()
  timestamp: Date;
}

export class SignalUpdateDto {
  @ApiProperty()
  symbol: string;

  @ApiProperty()
  signalType: 'buy' | 'sell' | 'strong_buy' | 'strong_sell' | 'neutral';

  @ApiProperty()
  confidence: number;

  @ApiProperty({ required: false })
  reasoning?: string;
}
