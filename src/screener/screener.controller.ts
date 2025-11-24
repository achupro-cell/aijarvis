import { Controller, Post, Get, Body, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBearerAuth } from '@nestjs/swagger';
import { ScreenerService } from './screener.service';
import { ScreenerQueryDto, ScreenerResponseDto } from './dto/screener.dto';
import { Signal } from '../database/entities/signal.entity';

@ApiTags('screener')
@Controller('api/screener')
export class ScreenerController {
  constructor(private screenerService: ScreenerService) {}

  @Post('query')
  @ApiOperation({
    summary: 'Query crypto screener with technical indicators',
    description: 'Analyze a trading symbol and return signal based on indicators',
  })
  @ApiResponse({
    status: 200,
    description: 'Screener analysis result',
    type: ScreenerResponseDto,
  })
  async queryScreener(@Body() dto: ScreenerQueryDto): Promise<ScreenerResponseDto> {
    return this.screenerService.queryScreener(dto);
  }

  @Get('signals')
  @ApiOperation({
    summary: 'Get recent signals',
    description: 'Retrieve the most recent trading signals',
  })
  @ApiResponse({
    status: 200,
    description: 'List of recent signals',
    type: [Signal],
  })
  async getSignals(@Query('symbol') symbol?: string): Promise<Signal[]> {
    return this.screenerService.getSignals(symbol);
  }

  @Get('signal-status')
  @ApiOperation({
    summary: 'Get current signal status for a symbol',
    description: 'Get the most recent signal for a specific trading symbol',
  })
  @ApiResponse({
    status: 200,
    description: 'Current signal status',
    type: Signal,
  })
  async getSignalStatus(@Query('symbol') symbol: string): Promise<Signal | null> {
    return this.screenerService.getSignalStatus(symbol);
  }
}
