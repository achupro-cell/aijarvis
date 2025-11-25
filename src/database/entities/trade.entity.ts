import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

export enum TradeStatus {
  PENDING = 'pending',
  OPENED = 'opened',
  PARTIALLY_CLOSED = 'partially_closed',
  CLOSED = 'closed',
  CANCELLED = 'cancelled',
}

@Entity('trades')
export class Trade {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  symbol: string;

  @Column()
  side: 'buy' | 'sell';

  @Column({ type: 'decimal', precision: 18, scale: 8 })
  quantity: number;

  @Column({ type: 'decimal', precision: 18, scale: 8 })
  entryPrice: number;

  @Column({ type: 'decimal', precision: 18, scale: 8, nullable: true })
  exitPrice: number;

  @Column({ type: 'decimal', precision: 5, scale: 2, nullable: true })
  profitLossPercent: number;

  @Column({ default: TradeStatus.PENDING })
  status: TradeStatus;

  @Column({ type: 'uuid', nullable: true })
  riskConfigId: string;

  @Column({ type: 'text', nullable: true })
  binanceOrderId: string;

  @Column({ type: 'text', nullable: true })
  notes: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @Column({ nullable: true })
  closedAt: Date;
}
