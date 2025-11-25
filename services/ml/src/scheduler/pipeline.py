import os
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Optional, Callable, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from ..config import settings
from ..data.fetcher import BinanceDataFetcher
from ..features.engineer import FeatureEngineer
from ..models.trainer import ModelTrainer
from ..registry.registry import ModelRegistry


class MLPipelineScheduler:
    """Scheduler for automated ML pipeline operations"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=settings.schedule_timezone)
        self.data_fetcher = BinanceDataFetcher()
        self.feature_engineer = FeatureEngineer()
        self.trainer = ModelTrainer()
        self.registry = ModelRegistry()
        
        self.jobs = {}
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("ML Pipeline Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("ML Pipeline Scheduler stopped")
    
    def add_daily_data_fetch(
        self, 
        job_id: str = "daily_data_fetch",
        schedule_time: str = None
    ) -> str:
        """Add daily data fetching job"""
        schedule_time = schedule_time or settings.daily_schedule_time
        
        try:
            # Parse schedule time
            hour, minute = map(int, schedule_time.split(':'))
            
            # Create job
            job = self.scheduler.add_job(
                func=self._fetch_latest_data,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=job_id,
                name="Daily Data Fetch",
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            logger.info(f"Added daily data fetch job: {job_id} at {schedule_time}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error adding daily data fetch job: {e}")
            raise
    
    def add_daily_training(
        self, 
        job_id: str = "daily_training",
        schedule_time: str = None,
        model_types: List[str] = None,
        target_types: List[str] = None
    ) -> str:
        """Add daily model training job"""
        schedule_time = schedule_time or settings.daily_schedule_time
        model_types = model_types or ['xgboost', 'lightgbm']
        target_types = target_types or ['binary', 'win_rate']
        
        try:
            # Parse schedule time
            hour, minute = map(int, schedule_time.split(':'))
            
            # Create job with parameters
            job = self.scheduler.add_job(
                func=self._train_models,
                trigger=CronTrigger(hour=hour, minute=minute),
                args=[model_types, target_types],
                id=job_id,
                name="Daily Model Training",
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            logger.info(f"Added daily training job: {job_id} at {schedule_time}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error adding daily training job: {e}")
            raise
    
    def add_hourly_data_update(
        self, 
        job_id: str = "hourly_data_update"
    ) -> str:
        """Add hourly data update job"""
        try:
            job = self.scheduler.add_job(
                func=self._update_data_hourly,
                trigger=IntervalTrigger(hours=1),
                id=job_id,
                name="Hourly Data Update",
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            logger.info(f"Added hourly data update job: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error adding hourly data update job: {e}")
            raise
    
    def add_custom_job(
        self, 
        func: Callable,
        trigger,
        job_id: str,
        name: str = None,
        args: List = None,
        kwargs: Dict = None
    ) -> str:
        """Add custom job"""
        try:
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=name or job_id,
                args=args or [],
                kwargs=kwargs or {},
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            logger.info(f"Added custom job: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error adding custom job: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs"""
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jobs_info
    
    def run_job_now(self, job_id: str) -> bool:
        """Run a job immediately"""
        try:
            self.scheduler.run_job(job_id)
            logger.info(f"Executed job immediately: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            return False
    
    # Job functions
    def _fetch_latest_data(self):
        """Fetch latest data for all configured symbols"""
        logger.info("Starting scheduled data fetch...")
        
        try:
            # Get latest timestamps for each symbol/timeframe
            for symbol in settings.symbols:
                for timeframe in settings.timeframes:
                    latest_timestamp = self.data_fetcher.get_latest_timestamp(symbol, timeframe)
                    
                    if latest_timestamp:
                        # Fetch data since last update
                        start_time = latest_timestamp + pd.Timedelta(hours=1)  # Get next candle
                        end_time = datetime.now()
                        
                        df = self.data_fetcher.get_klines(
                            symbol=symbol,
                            interval=timeframe,
                            start_time=start_time.strftime('%Y-%m-%d'),
                            end_time=end_time.strftime('%Y-%m-%d')
                        )
                        
                        if not df.empty:
                            # Save to database
                            existing_data = self.data_fetcher.load_from_sqlite(symbol, timeframe)
                            updated_data = pd.concat([existing_data, df], ignore_index=True)
                            updated_data = updated_data.drop_duplicates(subset=['open_time'], keep='last')
                            
                            self.data_fetcher.save_to_sqlite({symbol: {timeframe: updated_data}})
                            logger.info(f"Updated {symbol} {timeframe} with {len(df)} new records")
                    else:
                        # No existing data, fetch historical
                        logger.info(f"No existing data for {symbol} {timeframe}, fetching historical...")
                        
            logger.info("Scheduled data fetch completed")
            
        except Exception as e:
            logger.error(f"Error in scheduled data fetch: {e}")
    
    def _update_data_hourly(self):
        """Update data with latest candles"""
        logger.info("Starting hourly data update...")
        
        try:
            # Similar to _fetch_latest_data but focused on recent data
            for symbol in settings.symbols:
                for timeframe in ['1h']:  # Focus on hourly for frequent updates
                    df = self.data_fetcher.get_klines(
                        symbol=symbol,
                        interval=timeframe,
                        limit=10  # Get last 10 candles
                    )
                    
                    if not df.empty:
                        # Save to database
                        existing_data = self.data_fetcher.load_from_sqlite(symbol, timeframe)
                        updated_data = pd.concat([existing_data, df], ignore_index=True)
                        updated_data = updated_data.drop_duplicates(subset=['open_time'], keep='last').sort_values('open_time')
                        
                        self.data_fetcher.save_to_sqlite({symbol: {timeframe: updated_data}})
                        logger.info(f"Hourly update: {symbol} {timeframe} - {len(df)} records")
            
            logger.info("Hourly data update completed")
            
        except Exception as e:
            logger.error(f"Error in hourly data update: {e}")
    
    def _train_models(self, model_types: List[str], target_types: List[str]):
        """Train models with latest data"""
        logger.info("Starting scheduled model training...")
        
        try:
            # Load latest data for training
            all_data = {}
            
            for symbol in settings.symbols:
                symbol_data = {}
                for timeframe in settings.timeframes:
                    df = self.data_fetcher.load_from_sqlite(symbol, timeframe)
                    if not df.empty:
                        symbol_data[timeframe] = df
                
                if symbol_data:
                    all_data[symbol] = symbol_data
            
            if not all_data:
                logger.warning("No data available for training")
                return
            
            # Train models for each symbol/timeframe combination
            for symbol, timeframes in all_data.items():
                for timeframe, df in timeframes.items():
                    if df.empty:
                        continue
                    
                    logger.info(f"Training models for {symbol} {timeframe}")
                    
                    # Feature engineering
                    df_features = self.feature_engineer.engineer_features(df)
                    
                    if df_features.empty:
                        logger.warning(f"No features generated for {symbol} {timeframe}")
                        continue
                    
                    # Train models
                    for target_type in target_types:
                        try:
                            results = self.trainer.train_models(
                                df_features,
                                model_types=model_types,
                                target_type=target_type,
                                tune_hyperparameters=False  # Keep it fast for scheduled runs
                            )
                            
                            # Register models in registry
                            for model_key, model_data in results.items():
                                model_type = model_key.split('_')[0]
                                
                                model_id = self.registry.register_model(
                                    model=model_data['model'],
                                    model_type=model_type,
                                    target_type=target_type,
                                    metrics=model_data['metrics'],
                                    feature_names=model_data['feature_names'],
                                    description=f"Auto-trained model for {symbol} {timeframe}",
                                    tags=["scheduled", symbol, timeframe]
                                )
                                
                                logger.info(f"Registered model: {model_id}")
                        
                        except Exception as e:
                            logger.error(f"Error training {target_type} model for {symbol} {timeframe}: {e}")
                            continue
            
            logger.info("Scheduled model training completed")
            
        except Exception as e:
            logger.error(f"Error in scheduled model training: {e}")
    
    def setup_default_schedule(self):
        """Setup default schedule for the ML pipeline"""
        logger.info("Setting up default ML pipeline schedule...")
        
        try:
            # Add daily data fetch at 1 AM
            self.add_daily_data_fetch("daily_data_fetch", "01:00")
            
            # Add daily training at 2 AM
            self.add_daily_training("daily_training", "02:00")
            
            # Add hourly data updates
            self.add_hourly_data_update("hourly_data_update")
            
            logger.info("Default schedule setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up default schedule: {e}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False