import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('risk_configs')
export class RiskConfig {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column({ type: 'decimal', precision: 18, scale: 8 })
  maxPositionSize: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  maxDrawdownPercent: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  stopLossPercent: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  takeProfitPercent: number;

  @Column({ type: 'decimal', precision: 5, scale: 2 })
  riskRewardRatio: number;

  @Column({ default: true })
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
