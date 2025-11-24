import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as sodium from 'libsodium.js';

@Injectable()
export class EncryptionService {
  private encryptionKey: Buffer;

  constructor(private configService: ConfigService) {
    this.initializeKey();
  }

  private initializeKey() {
    const keyString = this.configService.get<string>('ENCRYPTION_KEY');

    if (!keyString) {
      throw new Error('ENCRYPTION_KEY environment variable is not set');
    }

    // Ensure the key is 32 bytes for libsodium
    this.encryptionKey = Buffer.alloc(32);
    Buffer.from(keyString).copy(this.encryptionKey);
  }

  async encrypt(data: string): Promise<string> {
    return new Promise((resolve, reject) => {
      sodium.ready.then(() => {
        try {
          const nonce = sodium.randombytes_buf(
            sodium.crypto_secretbox_NONCEBYTES,
          );
          const encrypted = sodium.crypto_secretbox_easy(
            data,
            nonce,
            this.encryptionKey,
          );
          const combined = Buffer.concat([
            Buffer.from(nonce),
            Buffer.from(encrypted),
          ]);
          resolve(combined.toString('base64'));
        } catch (error) {
          reject(error);
        }
      });
    });
  }

  async decrypt(encryptedData: string): Promise<string> {
    return new Promise((resolve, reject) => {
      sodium.ready.then(() => {
        try {
          const combined = Buffer.from(encryptedData, 'base64');
          const nonce = combined.slice(0, sodium.crypto_secretbox_NONCEBYTES);
          const encrypted = combined.slice(sodium.crypto_secretbox_NONCEBYTES);
          const decrypted = sodium.crypto_secretbox_open_easy(
            encrypted,
            nonce,
            this.encryptionKey,
          );
          resolve(Buffer.from(decrypted).toString());
        } catch (error) {
          reject(error);
        }
      });
    });
  }
}
