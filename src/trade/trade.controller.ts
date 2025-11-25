import { Controller, Post, Get, Put, Body, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { TradeService } from './trade.service';
import { BinanceService } from './binance.service';
import { RiskService } from './risk.service';
import {
  ExecuteTradeDto,
  TradeExecutionResponseDto,
  RiskConfigDto,
  ApiKeyDto,
} from './dto/trade.dto';
import { Trade, TradeStatus } from '../database/entities/trade.entity';
import { RiskConfig } from '../database/entities/risk-config.entity';

@ApiTags('trade')
@Controller('api/trade')
export class TradeController {
  constructor(
    private tradeService: TradeService,
    private binanceService: BinanceService,
    private riskService: RiskService,
  ) {}

  @Post('execute')
  @ApiOperation({
    summary: 'Execute a trade',
    description: 'Execute a trade with risk controls and Binance integration',
  })
  @ApiResponse({
    status: 200,
    description: 'Trade executed successfully',
    type: TradeExecutionResponseDto,
  })
  async executeTrade(@Body() dto: ExecuteTradeDto): Promise<TradeExecutionResponseDto> {
    return this.tradeService.executeTrade(dto);
  }

  @Put(':id/close')
  @ApiOperation({
    summary: 'Close a trade',
    description: 'Close an open trade at the specified exit price or current market price',
  })
  @ApiResponse({
    status: 200,
    description: 'Trade closed',
    type: Trade,
  })
  async closeTrade(
    @Param('id') id: string,
    @Body('exitPrice') exitPrice?: number,
  ): Promise<Trade> {
    return this.tradeService.closeTrade(id, exitPrice);
  }

  @Get(':id')
  @ApiOperation({
    summary: 'Get trade details',
    description: 'Retrieve details for a specific trade',
  })
  @ApiResponse({
    status: 200,
    description: 'Trade details',
    type: Trade,
  })
  async getTrade(@Param('id') id: string): Promise<Trade | null> {
    return this.tradeService.getTrade(id);
  }

  @Get()
  @ApiOperation({
    summary: 'List trades',
    description: 'Get list of trades with optional filtering',
  })
  @ApiResponse({
    status: 200,
    description: 'List of trades',
    type: [Trade],
  })
  async getTrades(
    @Query('symbol') symbol?: string,
    @Query('status') status?: TradeStatus,
  ): Promise<Trade[]> {
    return this.tradeService.getTrades(symbol, status);
  }

  @Get('open/list')
  @ApiOperation({
    summary: 'Get open trades',
    description: 'Get all currently open trades',
  })
  @ApiResponse({
    status: 200,
    description: 'List of open trades',
    type: [Trade],
  })
  async getOpenTrades(): Promise<Trade[]> {
    return this.tradeService.getOpenTrades();
  }

  @Get('stats/summary')
  @ApiOperation({
    summary: 'Get trade statistics',
    description: 'Get summary statistics for all trades',
  })
  async getTradeStats(): Promise<{
    totalTrades: number;
    openTrades: number;
    closedTrades: number;
    profitableTrades: number;
    totalPnL: number;
  }> {
    return this.tradeService.getTradeStats();
  }

  @Post('risk-config')
  @ApiOperation({
    summary: 'Create risk configuration',
    description: 'Create a new risk configuration for trade execution',
  })
  @ApiResponse({
    status: 201,
    description: 'Risk configuration created',
    type: RiskConfig,
  })
  async createRiskConfig(@Body() dto: RiskConfigDto): Promise<RiskConfig> {
    return this.riskService.createRiskConfig(dto);
  }

  @Get('risk-config/:id')
  @ApiOperation({
    summary: 'Get risk configuration',
    description: 'Retrieve a specific risk configuration',
  })
  @ApiResponse({
    status: 200,
    description: 'Risk configuration',
    type: RiskConfig,
  })
  async getRiskConfig(@Param('id') id: string): Promise<RiskConfig | null> {
    return this.riskService.getRiskConfig(id);
  }

  @Post('api-keys')
  @ApiOperation({
    summary: 'Add Binance API credentials',
    description: 'Save Binance API credentials (encrypted)',
  })
  async addApiKey(@Body() dto: ApiKeyDto): Promise<{ id: string; name: string }> {
    const key = await this.binanceService.saveApiKey(
      dto.name,
      dto.apiKey,
      dto.apiSecret,
      dto.isTestnet ?? true,
    );
    return { id: key.id, name: key.name };
  }

  @Get('binance/balance')
  @ApiOperation({
    summary: 'Get Binance account balance',
    description: 'Get USDT balance from connected Binance account',
  })
  async getBinanceBalance(
    @Query('asset') asset: string = 'USDT',
  ): Promise<{ free: string; locked: string }> {
    return this.binanceService.getBalance(asset);
  }

  @Get('binance/price/:symbol')
  @ApiOperation({
    summary: 'Get current Binance price',
    description: 'Get current market price for a symbol',
  })
  async getBinancePrice(@Param('symbol') symbol: string): Promise<number> {
    return this.binanceService.getCurrentPrice(symbol);
  }
}
