#!/usr/bin/env python3
"""
Test script for ML Pipeline
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from src.data.fetcher import BinanceDataFetcher
from src.features.engineer import FeatureEngineer
from src.models.trainer import ModelTrainer
from src.registry.registry import ModelRegistry

def test_data_fetching():
    """Test data fetching functionality"""
    print("Testing data fetching...")
    
    try:
        fetcher = BinanceDataFetcher()
        
        # Test fetching a small amount of data
        df = fetcher.get_klines("BTCUSDT", "1h", limit=10)
        
        if not df.empty:
            print(f"✓ Successfully fetched {len(df)} records")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Date range: {df['open_time'].min()} to {df['open_time'].max()}")
            return True
        else:
            print("✗ No data fetched")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_feature_engineering():
    """Test feature engineering"""
    print("\nTesting feature engineering...")
    
    try:
        fetcher = BinanceDataFetcher()
        engineer = FeatureEngineer()
        
        # Get some sample data
        df = fetcher.get_klines("BTCUSDT", "1h", limit=100)
        
        if df.empty:
            print("✗ No data available for feature engineering")
            return False
        
        # Engineer features
        df_features = engineer.engineer_features(df)
        
        if not df_features.empty:
            print(f"✓ Feature engineering completed")
            print(f"  Original shape: {df.shape}")
            print(f"  Features shape: {df_features.shape}")
            print(f"  New features created: {df_features.shape[1] - df.shape[1]}")
            
            # Check for target variables
            target_cols = [col for col in df_features.columns if 'target' in col]
            print(f"  Target variables: {target_cols}")
            
            return True
        else:
            print("✗ Feature engineering failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_model_training():
    """Test model training"""
    print("\nTesting model training...")
    
    try:
        fetcher = BinanceDataFetcher()
        engineer = FeatureEngineer()
        trainer = ModelTrainer()
        
        # Get and process data
        df = fetcher.get_klines("BTCUSDT", "1h", limit=500)
        
        if df.empty:
            print("✗ No data available for training")
            return False
        
        df_features = engineer.engineer_features(df)
        
        if df_features.empty:
            print("✗ Feature engineering failed")
            return False
        
        # Train a simple model
        results = trainer.train_models(
            df_features,
            model_types=['lightgbm'],  # Use lighter model for testing
            target_type='binary',
            tune_hyperparameters=False
        )
        
        if results:
            print("✓ Model training completed")
            for model_key, model_data in results.items():
                metrics = model_data['metrics']
                print(f"  {model_key}:")
                print(f"    Accuracy: {metrics.get('accuracy', 0):.4f}")
                print(f"    F1 Score: {metrics.get('f1', 0):.4f}")
            
            return True
        else:
            print("✗ Model training failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_model_registry():
    """Test model registry"""
    print("\nTesting model registry...")
    
    try:
        registry = ModelRegistry()
        
        # List models
        models = registry.list_models()
        print(f"✓ Found {len(models)} registered models")
        
        if models:
            print("  Latest models:")
            for model in models[:3]:  # Show first 3
                print(f"    {model['model_id']} - {model['model_type']} v{model['version']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("ML Pipeline Test Suite")
    print("=" * 50)
    
    tests = [
        test_data_fetching,
        test_feature_engineering,
        test_model_training,
        test_model_registry
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())