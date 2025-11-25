import { Injectable, Logger as NestLogger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as winston from 'winston';

@Injectable()
export class LoggerService extends NestLogger {
  private logger: winston.Logger;

  constructor(private configService: ConfigService) {
    super();
    const logLevel = this.configService.get<string>('LOG_LEVEL', 'debug');

    this.logger = winston.createLogger({
      level: logLevel,
      format: winston.format.combine(
        winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        winston.format.errors({ stack: true }),
        winston.format.json(),
      ),
      defaultMeta: { service: 'crypto-screener' },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.printf(({ level, message, timestamp, ...meta }) => {
              const metaStr =
                Object.keys(meta).length > 0 ? JSON.stringify(meta) : '';
              return `${timestamp} [${level}]: ${message} ${metaStr}`;
            }),
          ),
        }),
        new winston.transports.File({
          filename: 'logs/error.log',
          level: 'error',
        }),
        new winston.transports.File({
          filename: 'logs/combined.log',
        }),
      ],
    });
  }

  log(message: string, context?: string, meta?: any) {
    this.logger.info(message, { context, ...meta });
    super.log(message, context);
  }

  error(message: string, trace?: string, context?: string) {
    this.logger.error(message, { trace, context });
    super.error(message, trace, context);
  }

  warn(message: string, context?: string) {
    this.logger.warn(message, { context });
    super.warn(message, context);
  }

  debug(message: string, context?: string, meta?: any) {
    this.logger.debug(message, { context, ...meta });
    super.debug(message, context);
  }

  verbose(message: string, context?: string) {
    this.logger.verbose(message, { context });
    super.verbose(message, context);
  }
}
