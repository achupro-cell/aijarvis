import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from loguru import logger
from ..config import settings
from ..models.trainer import ModelTrainer
from ..features.engineer import FeatureEngineer


class Backtester:
    """Backtesting framework for trading strategies"""
    
    def __init__(self):
        self.initial_capital = settings.backtest_initial_capital
        self.commission = settings.backtest_commission
        self.trainer = ModelTrainer()
        self.feature_engineer = FeatureEngineer()
    
    def prepare_backtest_data(
        self, 
        df: pd.DataFrame,
        model_key: str,
        prediction_threshold: float = 0.5
    ) -> pd.DataFrame:
        """Prepare data for backtesting with predictions"""
        if df.empty:
            raise ValueError("Empty DataFrame provided")
        
        # Load model
        model_data = self.trainer.load_model(model_key)
        if not model_data:
            raise ValueError(f"Model {model_key} not found")
        
        feature_names = model_data['feature_names']
        
        # Ensure we have all required features
        df_features = self.feature_engineer.engineer_features(df.copy())
        
        # Get predictions
        X = df_features[feature_names].copy()
        predictions = self.trainer.predict(model_key, X, return_proba=True)
        
        # Add predictions to DataFrame
        if predictions.ndim == 2:  # Probabilities
            df_features['prediction_proba'] = predictions[:, 1]  # Probability of positive class
        else:  # Binary predictions
            df_features['prediction_proba'] = predictions
        
        df_features['prediction'] = (df_features['prediction_proba'] > prediction_threshold).astype(int)
        
        # Add actual returns for evaluation
        df_features['actual_return'] = df_features['close'].pct_change()
        
        logger.info(f"Prepared backtest data with {len(df_features)} rows")
        return df_features
    
    def simulate_trading(
        self, 
        df: pd.DataFrame,
        strategy: str = 'prediction_based',
        position_size: float = 0.1,
        stop_loss: float = 0.02,
        take_profit: float = 0.04,
        prediction_threshold: float = 0.6
    ) -> pd.DataFrame:
        """Simulate trading strategy"""
        if df.empty:
            return pd.DataFrame()
        
        # Initialize tracking variables
        capital = self.initial_capital
        position = 0  # Current position (0 = no position, 1 = long, -1 = short)
        position_size_shares = 0
        entry_price = 0
        trades = []
        portfolio_values = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            current_price = row['close']
            
            # Record portfolio value before trade
            portfolio_value = capital + (position_size_shares * current_price if position != 0 else 0)
            portfolio_values.append({
                'timestamp': row['open_time'],
                'portfolio_value': portfolio_value,
                'capital': capital,
                'position': position,
                'price': current_price
            })
            
            # Trading logic based on strategy
            if strategy == 'prediction_based':
                # Entry signals
                if position == 0:  # No position
                    if row['prediction'] == 1 and row['prediction_proba'] > prediction_threshold:
                        # Enter long position
                        position_size_shares = (capital * position_size) / current_price
                        position = 1
                        entry_price = current_price
                        capital -= position_size_shares * current_price * (1 + self.commission)
                        
                        trades.append({
                            'timestamp': row['open_time'],
                            'type': 'BUY',
                            'price': current_price,
                            'shares': position_size_shares,
                            'value': position_size_shares * current_price,
                            'commission': position_size_shares * current_price * self.commission,
                            'prediction': row['prediction'],
                            'prediction_proba': row['prediction_proba']
                        })
                
                # Exit signals
                elif position == 1:  # Long position
                    # Stop loss
                    if current_price <= entry_price * (1 - stop_loss):
                        position_size_shares = 0
                        position = 0
                        capital += current_price * position_size_shares * (1 - self.commission)
                        
                        trades.append({
                            'timestamp': row['open_time'],
                            'type': 'SELL_STOP_LOSS',
                            'price': current_price,
                            'shares': position_size_shares,
                            'value': position_size_shares * current_price,
                            'commission': position_size_shares * current_price * self.commission,
                            'pnl': (current_price - entry_price) / entry_price,
                            'prediction': row['prediction'],
                            'prediction_proba': row['prediction_proba']
                        })
                    
                    # Take profit
                    elif current_price >= entry_price * (1 + take_profit):
                        position_size_shares = 0
                        position = 0
                        capital += current_price * position_size_shares * (1 - self.commission)
                        
                        trades.append({
                            'timestamp': row['open_time'],
                            'type': 'SELL_TAKE_PROFIT',
                            'price': current_price,
                            'shares': position_size_shares,
                            'value': position_size_shares * current_price,
                            'commission': position_size_shares * current_price * self.commission,
                            'pnl': (current_price - entry_price) / entry_price,
                            'prediction': row['prediction'],
                            'prediction_proba': row['prediction_proba']
                        })
                    
                    # Signal reversal
                    elif row['prediction'] == 0 or row['prediction_proba'] < prediction_threshold:
                        position_size_shares = 0
                        position = 0
                        capital += current_price * position_size_shares * (1 - self.commission)
                        
                        trades.append({
                            'timestamp': row['open_time'],
                            'type': 'SELL_SIGNAL',
                            'price': current_price,
                            'shares': position_size_shares,
                            'value': position_size_shares * current_price,
                            'commission': position_size_shares * current_price * self.commission,
                            'pnl': (current_price - entry_price) / entry_price,
                            'prediction': row['prediction'],
                            'prediction_proba': row['prediction_proba']
                        })
        
        # Convert to DataFrames
        trades_df = pd.DataFrame(trades)
        portfolio_df = pd.DataFrame(portfolio_values)
        
        return trades_df, portfolio_df
    
    def calculate_metrics(
        self, 
        trades_df: pd.DataFrame, 
        portfolio_df: pd.DataFrame
    ) -> Dict[str, float]:
        """Calculate backtesting performance metrics"""
        if trades_df.empty or portfolio_df.empty:
            return {}
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
        losing_trades = len(trades_df[trades_df['pnl'] < 0]) if 'pnl' in trades_df.columns else 0
        
        # Win rate
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Returns
        initial_value = self.initial_capital
        final_value = portfolio_df['portfolio_value'].iloc[-1]
        total_return = (final_value - initial_value) / initial_value
        
        # Calculate daily returns
        portfolio_df['daily_return'] = portfolio_df['portfolio_value'].pct_change()
        daily_returns = portfolio_df['daily_return'].dropna()
        
        # Risk metrics
        if len(daily_returns) > 0:
            volatility = daily_returns.std() * np.sqrt(252)  # Annualized
            sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
            
            # Maximum drawdown
            portfolio_df['cumulative_max'] = portfolio_df['portfolio_value'].cummax()
            portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['cumulative_max']) / portfolio_df['cumulative_max']
            max_drawdown = portfolio_df['drawdown'].min()
        else:
            volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0
        
        # Trade-specific metrics
        if 'pnl' in trades_df.columns and not trades_df.empty:
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        else:
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'annualized_volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'initial_capital': initial_value,
            'final_value': final_value
        }
        
        return metrics
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        model_key: str,
        strategy_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run complete backtest"""
        logger.info(f"Starting backtest with model: {model_key}")
        
        # Default strategy parameters
        default_params = {
            'strategy': 'prediction_based',
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'prediction_threshold': 0.6
        }
        
        if strategy_params:
            default_params.update(strategy_params)
        
        try:
            # Prepare data
            df_backtest = self.prepare_backtest_data(df, model_key, default_params['prediction_threshold'])
            
            # Simulate trading
            trades_df, portfolio_df = self.simulate_trading(df_backtest, **default_params)
            
            # Calculate metrics
            metrics = self.calculate_metrics(trades_df, portfolio_df)
            
            # Log results
            logger.info("Backtest completed successfully")
            for metric, value in metrics.items():
                logger.info(f"  {metric}: {value}")
            
            return {
                'trades': trades_df,
                'portfolio': portfolio_df,
                'metrics': metrics,
                'strategy_params': default_params,
                'model_key': model_key
            }
            
        except Exception as e:
            logger.error(f"Error during backtest: {e}")
            return {}
    
    def generate_report(self, backtest_results: Dict[str, Any]) -> str:
        """Generate backtest report"""
        if not backtest_results:
            return "No backtest results available"
        
        metrics = backtest_results.get('metrics', {})
        strategy_params = backtest_results.get('strategy_params', {})
        
        report = f"""
# Backtest Report

## Strategy Parameters
- Strategy: {strategy_params.get('strategy', 'N/A')}
- Position Size: {strategy_params.get('position_size', 'N/A')}
- Stop Loss: {strategy_params.get('stop_loss', 'N/A')}
- Take Profit: {strategy_params.get('take_profit', 'N/A')}
- Prediction Threshold: {strategy_params.get('prediction_threshold', 'N/A')}

## Performance Metrics
- Total Trades: {metrics.get('total_trades', 0)}
- Win Rate: {metrics.get('win_rate', 0):.2%}
- Total Return: {metrics.get('total_return', 0):.2%}
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
- Maximum Drawdown: {metrics.get('max_drawdown', 0):.2%}
- Average Win: {metrics.get('avg_win', 0):.2%}
- Average Loss: {metrics.get('avg_loss', 0):.2%}
- Profit Factor: {metrics.get('profit_factor', 0):.2f}

## Capital Analysis
- Initial Capital: ${metrics.get('initial_capital', 0):,.2f}
- Final Value: ${metrics.get('final_value', 0):,.2f}
- Net Profit: ${metrics.get('final_value', 0) - metrics.get('initial_capital', 0):,.2f}
"""
        
        return report
    
    def plot_results(self, backtest_results: Dict[str, Any]) -> Optional[str]:
        """Create visualization plots"""
        if not backtest_results:
            return None
        
        try:
            portfolio_df = backtest_results.get('portfolio')
            trades_df = backtest_results.get('trades')
            
            if portfolio_df is None or portfolio_df.empty:
                return None
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Portfolio Value', 'Drawdown', 'Trade Distribution'),
                vertical_spacing=0.08
            )
            
            # Portfolio value
            fig.add_trace(
                go.Scatter(
                    x=portfolio_df['timestamp'],
                    y=portfolio_df['portfolio_value'],
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            
            # Drawdown
            if 'drawdown' in portfolio_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=portfolio_df['timestamp'],
                        y=portfolio_df['drawdown'] * 100,
                        mode='lines',
                        name='Drawdown (%)',
                        line=dict(color='red'),
                        fill='tonexty'
                    ),
                    row=2, col=1
                )
            
            # Trade P&L distribution
            if trades_df is not None and 'pnl' in trades_df.columns and not trades_df.empty:
                fig.add_trace(
                    go.Histogram(
                        x=trades_df['pnl'] * 100,
                        name='Trade P&L (%)',
                        nbinsx=30,
                        marker_color='green'
                    ),
                    row=3, col=1
                )
            
            fig.update_layout(
                title='Backtest Results',
                height=800,
                showlegend=True
            )
            
            # Save plot
            plot_path = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            fig.write_html(plot_path)
            
            logger.info(f"Plot saved to {plot_path}")
            return plot_path
            
        except Exception as e:
            logger.error(f"Error creating plots: {e}")
            return None