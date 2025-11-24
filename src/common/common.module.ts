import { Module } from '@nestjs/common';
import { LoggerService } from './logger/logger.service';
import { EncryptionService } from './encryption/encryption.service';
import { ValidationService } from './validation/validation.service';

@Module({
  providers: [LoggerService, EncryptionService, ValidationService],
  exports: [LoggerService, EncryptionService, ValidationService],
})
export class CommonModule {}
