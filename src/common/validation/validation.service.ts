import { Injectable, BadRequestException } from '@nestjs/common';
import * as Joi from 'joi';
import { z, ZodSchema } from 'zod';

@Injectable()
export class ValidationService {
  validateJoi<T>(data: any, schema: Joi.ObjectSchema): T {
    const { error, value } = schema.validate(data, {
      abortEarly: false,
      stripUnknown: true,
    });

    if (error) {
      const messages = error.details.map((detail) => detail.message).join(', ');
      throw new BadRequestException(`Validation error: ${messages}`);
    }

    return value as T;
  }

  validateZod<T>(data: any, schema: ZodSchema): T {
    try {
      return schema.parse(data) as T;
    } catch (error: any) {
      const messages = error.errors.map((e: any) => e.message).join(', ');
      throw new BadRequestException(`Validation error: ${messages}`);
    }
  }
}
