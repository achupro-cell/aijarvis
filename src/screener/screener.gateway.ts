import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { ScreenerService } from './screener.service';
import { LoggerService } from '../common/logger/logger.service';

@WebSocketGateway({
  cors: {
    origin: '*',
  },
  namespace: '/ws/screener',
})
export class ScreenerGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private watchedSymbols = new Map<string, Set<string>>();

  constructor(
    private screenerService: ScreenerService,
    private logger: LoggerService,
  ) {}

  afterInit(server: Server) {
    this.logger.log('Screener WebSocket gateway initialized');
  }

  handleConnection(client: Socket) {
    this.logger.debug(`Client connected to screener: ${client.id}`);
  }

  handleDisconnect(client: Socket) {
    this.logger.debug(`Client disconnected from screener: ${client.id}`);
    this.watchedSymbols.delete(client.id);
  }

  @SubscribeMessage('subscribe_signal')
  async onSubscribeSignal(
    client: Socket,
    data: { symbol: string },
  ): Promise<void> {
    if (!this.watchedSymbols.has(client.id)) {
      this.watchedSymbols.set(client.id, new Set());
    }
    this.watchedSymbols.get(client.id)!.add(data.symbol);

    this.logger.debug(`Client ${client.id} subscribed to ${data.symbol}`);

    // Send current signal status
    const signal = await this.screenerService.getSignalStatus(data.symbol);
    if (signal) {
      client.emit('signal_update', {
        symbol: data.symbol,
        signal,
      });
    }
  }

  @SubscribeMessage('unsubscribe_signal')
  onUnsubscribeSignal(client: Socket, data: { symbol: string }): void {
    const symbols = this.watchedSymbols.get(client.id);
    if (symbols) {
      symbols.delete(data.symbol);
    }
    this.logger.debug(`Client ${client.id} unsubscribed from ${data.symbol}`);
  }

  async broadcastSignalUpdate(symbol: string, signal: any): Promise<void> {
    this.server.emit('signal_update', {
      symbol,
      signal,
      timestamp: new Date(),
    });

    this.logger.debug(`Broadcasting signal update for ${symbol}`);
  }

  async broadcastTradeUpdate(trade: any): Promise<void> {
    this.server.emit('trade_update', {
      trade,
      timestamp: new Date(),
    });
  }
}
