import click
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.fetcher import BinanceDataFetcher
from src.features.engineer import FeatureEngineer
from src.models.trainer import ModelTrainer
from src.backtesting.evaluator import Backtester
from src.registry.registry import ModelRegistry
from src.scheduler.pipeline import MLPipelineScheduler
from src.config import settings


# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")


@click.group()
def cli():
    """ML Trading Pipeline CLI"""
    pass


@cli.command()
@click.option('--symbols', '-s', multiple=True, default=['BTCUSDT', 'ETHUSDT'], help='Trading symbols to fetch')
@click.option('--timeframes', '-t', multiple=True, default=['1h', '4h', '1d'], help='Timeframes to fetch')
@click.option('--days', '-d', default=365, help='Number of days of historical data to fetch')
@click.option('--output', '-o', type=click.Choice(['sqlite', 'parquet', 'both']), default='both', help='Output format')
def fetch_data(symbols, timeframes, days, output):
    """Fetch historical OHLCV data from Binance"""
    click.echo(f"Fetching data for {list(symbols)} with timeframes {list(timeframes)} for the last {days} days...")
    
    try:
        # Initialize data fetcher
        fetcher = BinanceDataFetcher()
        
        # Fetch data
        data = fetcher.fetch_historical_data(
            symbols=list(symbols),
            timeframes=list(timeframes),
            days_back=days
        )
        
        # Save data
        if output in ['sqlite', 'both']:
            fetcher.save_to_sqlite(data)
            click.echo("✓ Data saved to SQLite database")
        
        if output in ['parquet', 'both']:
            fetcher.save_to_parquet(data)
            click.echo("✓ Data saved to Parquet files")
        
        # Summary
        total_records = sum(
            len(df) for symbol_data in data.values() 
            for df in symbol_data.values() 
            if not df.empty
        )
        click.echo(f"✓ Successfully fetched {total_records} records")
        
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--symbol', '-s', default='BTCUSDT', help='Symbol to train on')
@click.option('--timeframe', '-t', default='1h', help='Timeframe to train on')
@click.option('--models', '-m', multiple=True, default=['xgboost', 'lightgbm'], help='Models to train')
@click.option('--target', default='binary', type=click.Choice(['binary', 'multiclass', 'win_rate']), help='Target type')
@click.option('--tune', is_flag=True, help='Perform hyperparameter tuning')
@click.option('--register', is_flag=True, default=True, help='Register models in registry')
def train(symbol, timeframe, models, target, tune, register):
    """Train ML models on historical data"""
    click.echo(f"Training {list(models)} models for {symbol} {timeframe} with {target} target...")
    
    try:
        # Initialize components
        fetcher = BinanceDataFetcher()
        feature_engineer = FeatureEngineer()
        trainer = ModelTrainer()
        registry = ModelRegistry() if register else None
        
        # Load data
        df = fetcher.load_from_sqlite(symbol, timeframe)
        if df.empty:
            click.echo(f"✗ No data found for {symbol} {timeframe}", err=True)
            raise click.Abort()
        
        click.echo(f"Loaded {len(df)} records")
        
        # Feature engineering
        df_features = feature_engineer.engineer_features(df)
        if df_features.empty:
            click.echo("✗ Feature engineering failed", err=True)
            raise click.Abort()
        
        click.echo(f"Feature engineering completed: {df_features.shape}")
        
        # Train models
        results = trainer.train_models(
            df_features,
            model_types=list(models),
            target_type=target,
            tune_hyperparameters=tune
        )
        
        if not results:
            click.echo("✗ No models were trained successfully", err=True)
            raise click.Abort()
        
        # Display results
        click.echo("\nTraining Results:")
        for model_key, model_data in results.items():
            metrics = model_data['metrics']
            click.echo(f"\n{model_key}:")
            for metric, value in metrics.items():
                click.echo(f"  {metric}: {value:.4f}")
            
            # Register model if requested
            if register and registry:
                model_type = model_key.split('_')[0]
                model_id = registry.register_model(
                    model=model_data['model'],
                    model_type=model_type,
                    target_type=target,
                    metrics=metrics,
                    feature_names=model_data['feature_names'],
                    description=f"Trained model for {symbol} {timeframe}",
                    tags=[symbol, timeframe]
                )
                click.echo(f"  Registered as: {model_id}")
        
        click.echo("\n✓ Training completed successfully")
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--symbol', '-s', default='BTCUSDT', help='Symbol to backtest')
@click.option('--timeframe', '-t', default='1h', help='Timeframe to backtest')
@click.option('--model-id', help='Specific model ID to use (if not provided, uses latest)')
@click.option('--threshold', default=0.6, help='Prediction threshold')
@click.option('--position-size', default=0.1, help='Position size (fraction of capital)')
@click.option('--stop-loss', default=0.02, help='Stop loss percentage')
@click.option('--take-profit', default=0.04, help='Take profit percentage')
@click.option('--plot', is_flag=True, help='Generate plots')
def backtest(symbol, timeframe, model_id, threshold, position_size, stop_loss, take_profit, plot):
    """Backtest trading strategies"""
    click.echo(f"Backtesting strategy for {symbol} {timeframe}...")
    
    try:
        # Initialize components
        fetcher = BinanceDataFetcher()
        backtester = Backtester()
        registry = ModelRegistry()
        
        # Load data
        df = fetcher.load_from_sqlite(symbol, timeframe)
        if df.empty:
            click.echo(f"✗ No data found for {symbol} {timeframe}", err=True)
            raise click.Abort()
        
        click.echo(f"Loaded {len(df)} records")
        
        # Determine model to use
        if model_id:
            model_data = registry.get_model(model_id)
            if not model_data:
                click.echo(f"✗ Model {model_id} not found", err=True)
                raise click.Abort()
            model_key = f"{model_data['metadata']['model_type']}_{model_data['metadata']['target_type']}"
        else:
            # Get latest model
            model_data = registry.get_latest_model('xgboost', 'binary')
            if not model_data:
                click.echo("✗ No suitable model found in registry", err=True)
                raise click.Abort()
            model_key = f"{model_data['metadata']['model_type']}_{model_data['metadata']['target_type']}"
        
        click.echo(f"Using model: {model_key}")
        
        # Run backtest
        strategy_params = {
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'prediction_threshold': threshold
        }
        
        results = backtester.run_backtest(df, model_key, strategy_params)
        
        if not results:
            click.echo("✗ Backtest failed", err=True)
            raise click.Abort()
        
        # Display results
        metrics = results['metrics']
        click.echo("\nBacktest Results:")
        click.echo(f"Total Trades: {metrics.get('total_trades', 0)}")
        click.echo(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
        click.echo(f"Total Return: {metrics.get('total_return', 0):.2%}")
        click.echo(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        click.echo(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
        click.echo(f"Final Value: ${metrics.get('final_value', 0):,.2f}")
        
        # Generate report
        report = backtester.generate_report(results)
        
        # Save report
        report_file = f"backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        click.echo(f"\n✓ Report saved to: {report_file}")
        
        # Generate plots if requested
        if plot:
            plot_file = backtester.plot_results(results)
            if plot_file:
                click.echo(f"✓ Plot saved to: {plot_file}")
        
    except Exception as e:
        logger.error(f"Error during backtest: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--setup', is_flag=True, help='Setup default schedule')
@click.option('--start', is_flag=True, help='Start the scheduler')
@click.option('--stop', is_flag=True, help='Stop the scheduler')
@click.option('--status', is_flag=True, help='Show scheduler status')
@click.option('--list-jobs', is_flag=True, help='List scheduled jobs')
@click.option('--run-job', help='Run a specific job immediately')
def schedule(setup, start, stop, status, list_jobs, run_job):
    """Manage ML pipeline scheduler"""
    scheduler = MLPipelineScheduler()
    
    try:
        if setup:
            click.echo("Setting up default ML pipeline schedule...")
            scheduler.setup_default_schedule()
            click.echo("✓ Default schedule configured")
        
        if start:
            click.echo("Starting scheduler...")
            scheduler.start()
            click.echo("✓ Scheduler started")
        
        if stop:
            click.echo("Stopping scheduler...")
            scheduler.stop()
            click.echo("✓ Scheduler stopped")
        
        if status:
            if scheduler.is_running:
                click.echo("✓ Scheduler is running")
            else:
                click.echo("✗ Scheduler is stopped")
        
        if list_jobs:
            jobs = scheduler.list_jobs()
            if jobs:
                click.echo("\nScheduled Jobs:")
                for job in jobs:
                    click.echo(f"  {job['id']}: {job['name']}")
                    click.echo(f"    Next run: {job['next_run_time']}")
                    click.echo(f"    Trigger: {job['trigger']}")
            else:
                click.echo("No jobs scheduled")
        
        if run_job:
            click.echo(f"Running job: {run_job}")
            success = scheduler.run_job_now(run_job)
            if success:
                click.echo("✓ Job executed successfully")
            else:
                click.echo("✗ Job execution failed")
        
    except Exception as e:
        logger.error(f"Error with scheduler: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--model-type', help='Filter by model type')
@click.option('--target-type', help='Filter by target type')
@click.option('--status', default='active', help='Filter by status')
def list_models(model_type, target_type, status):
    """List registered models"""
    try:
        registry = ModelRegistry()
        models = registry.list_models(model_type, target_type, status)
        
        if models:
            click.echo("\nRegistered Models:")
            for model in models:
                click.echo(f"ID: {model['model_id']}")
                click.echo(f"  Type: {model['model_type']}")
                click.echo(f"  Target: {model['target_type']}")
                click.echo(f"  Version: {model['version']}")
                click.echo(f"  Created: {model['created_at']}")
                
                metrics = model.get('metrics', {})
                if metrics:
                    click.echo("  Metrics:")
                    for metric, value in metrics.items():
                        click.echo(f"    {metric}: {value:.4f}")
                
                click.echo()
        else:
            click.echo("No models found")
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--model-id', required=True, help='Model ID to compare')
@click.argument('other_model_ids', nargs=-1)
def compare_models(model_id, other_model_ids):
    """Compare multiple models"""
    try:
        registry = ModelRegistry()
        all_model_ids = [model_id] + list(other_model_ids)
        
        comparison_df = registry.compare_models(all_model_ids)
        
        if not comparison_df.empty:
            click.echo("\nModel Comparison:")
            click.echo(comparison_df.to_string(index=False))
        else:
            click.echo("No models to compare")
    
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()