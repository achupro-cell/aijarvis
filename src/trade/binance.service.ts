import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { LoggerService } from '../common/logger/logger.service';
import { EncryptionService } from '../common/encryption/encryption.service';
import { ApiKey } from '../database/entities/api-key.entity';

// Using dynamic require for binance SDK to handle ESM/CJS compatibility
let Binance: any;

async function loadBinance() {
  if (!Binance) {
    Binance = await import('binance');
  }
  return Binance;
}

@Injectable()
export class BinanceService {
  private client: any = null;

  constructor(
    private configService: ConfigService,
    @InjectRepository(ApiKey)
    private apiKeyRepository: Repository<ApiKey>,
    private encryptionService: EncryptionService,
    private logger: LoggerService,
  ) {}

  async initializeClient(apiKeyId?: string): Promise<void> {
    try {
      const apiKey = apiKeyId
        ? await this.apiKeyRepository.findOne({ where: { id: apiKeyId } })
        : await this.apiKeyRepository.findOne({
            where: { exchange: 'binance', isTestnet: true },
          });

      if (!apiKey) {
        this.logger.warn('No API key found for Binance, using public client');
        const BinanceModule = await loadBinance();
        this.client = new BinanceModule.default();
        return;
      }

      const decryptedKey = await this.encryptionService.decrypt(apiKey.apiKey);
      const decryptedSecret = await this.encryptionService.decrypt(
        apiKey.apiSecret,
      );

      const BinanceModule = await loadBinance();

      const baseUrl = apiKey.isTestnet
        ? 'https://testnet.binance.vision'
        : 'https://api.binance.com';

      this.client = new BinanceModule.default({
        apiKey: decryptedKey,
        apiSecret: decryptedSecret,
        baseURL: baseUrl,
        baseUrlWs:
          apiKey.isTestnet
            ? 'wss://stream.testnet.binance.vision:9443/ws'
            : 'wss://stream.binance.com:9443/ws',
      });

      this.logger.log('Binance client initialized', {
        testnet: apiKey.isTestnet,
      });
    } catch (error) {
      this.logger.error(
        `Failed to initialize Binance client: ${error.message}`,
        error.stack,
      );
      throw error;
    }
  }

  async getBalance(asset: string = 'USDT'): Promise<{ free: string; locked: string }> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      const account = await this.client.accountStatus();
      return account.balances.find(
        (b: any) => b.asset === asset,
      ) || { free: '0', locked: '0' };
    } catch (error) {
      this.logger.error(`Failed to get balance: ${error.message}`);
      throw error;
    }
  }

  async placeLimitOrder(
    symbol: string,
    side: 'BUY' | 'SELL',
    quantity: number,
    price: number,
  ): Promise<any> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      const order = await this.client.newOrder({
        symbol,
        side,
        type: 'LIMIT',
        quantity,
        price,
        timeInForce: 'GTC',
      });

      this.logger.log(`Order placed on Binance: ${order.orderId}`, {
        symbol,
        side,
        quantity,
        price,
      });

      return order;
    } catch (error) {
      this.logger.error(`Failed to place order: ${error.message}`);
      throw error;
    }
  }

  async placeMarketOrder(
    symbol: string,
    side: 'BUY' | 'SELL',
    quantity: number,
  ): Promise<any> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      const order = await this.client.newOrder({
        symbol,
        side,
        type: 'MARKET',
        quantity,
      });

      this.logger.log(`Market order placed on Binance: ${order.orderId}`, {
        symbol,
        side,
        quantity,
      });

      return order;
    } catch (error) {
      this.logger.error(`Failed to place market order: ${error.message}`);
      throw error;
    }
  }

  async cancelOrder(symbol: string, orderId: number): Promise<any> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      const result = await this.client.cancelOrder({
        symbol,
        orderId,
      });

      this.logger.log(`Order cancelled on Binance: ${orderId}`, { symbol });

      return result;
    } catch (error) {
      this.logger.error(`Failed to cancel order: ${error.message}`);
      throw error;
    }
  }

  async getOrderStatus(symbol: string, orderId: number): Promise<any> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      return await this.client.getOrder({
        symbol,
        orderId,
      });
    } catch (error) {
      this.logger.error(`Failed to get order status: ${error.message}`);
      throw error;
    }
  }

  async getCurrentPrice(symbol: string): Promise<number> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      const ticker = await this.client.tickerPrice({ symbol });
      return parseFloat(ticker.price);
    } catch (error) {
      this.logger.error(`Failed to get price for ${symbol}: ${error.message}`);
      throw error;
    }
  }

  async getKlines(
    symbol: string,
    interval: string,
    limit: number = 100,
  ): Promise<any[]> {
    if (!this.client) {
      await this.initializeClient();
    }

    try {
      return await this.client.klines({
        symbol,
        interval,
        limit,
      });
    } catch (error) {
      this.logger.error(`Failed to get klines: ${error.message}`);
      throw error;
    }
  }

  async saveApiKey(
    name: string,
    apiKey: string,
    apiSecret: string,
    isTestnet: boolean = true,
  ): Promise<ApiKey> {
    const encryptedKey = await this.encryptionService.encrypt(apiKey);
    const encryptedSecret = await this.encryptionService.encrypt(apiSecret);

    const key = this.apiKeyRepository.create({
      name,
      exchange: 'binance',
      apiKey: encryptedKey,
      apiSecret: encryptedSecret,
      isTestnet,
    });

    return this.apiKeyRepository.save(key);
  }
}
