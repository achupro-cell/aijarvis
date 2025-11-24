import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';

@Entity('api_keys')
export class ApiKey {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column()
  exchange: string; // e.g., 'binance'

  @Column()
  apiKey: string; // encrypted

  @Column()
  apiSecret: string; // encrypted

  @Column({ default: false })
  isTestnet: boolean;

  @Column({ type: 'text', nullable: true })
  passphrase: string; // for exchanges that require it, encrypted

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
