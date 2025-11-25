import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

export enum SignalType {
  BUY = 'buy',
  SELL = 'sell',
  STRONG_BUY = 'strong_buy',
  STRONG_SELL = 'strong_sell',
  NEUTRAL = 'neutral',
}

@Entity('signals')
export class Signal {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  symbol: string;

  @Column()
  signalType: SignalType;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  confidence: number;

  @Column({ type: 'text', nullable: true })
  indicators: string; // JSON string of indicator results

  @Column({ type: 'text', nullable: true })
  reasoning: string;

  @Column({ default: false })
  actioned: boolean;

  @Column({ nullable: true })
  actionedAt: Date;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
