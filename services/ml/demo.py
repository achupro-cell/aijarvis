#!/usr/bin/env python3
"""
ML Pipeline Demo Script
Demonstrates the complete ML trading pipeline functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import subprocess
import time

def run_command(cmd, description):
    """Run a CLI command and display results"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    # Run command directly without shell=True to avoid sourcing issues
    if cmd.startswith("source venv/bin/activate && "):
        # Extract the actual python command
        python_cmd = cmd.replace("source venv/bin/activate && ", "")
        cmd_list = ["./venv/bin/python3"] + python_cmd.split()[1:]
    else:
        cmd_list = cmd.split()
    
    result = subprocess.run(cmd_list, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SUCCESS")
        print(result.stdout)
    else:
        print("❌ FAILED")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Run demo of ML pipeline"""
    print("🎯 ML Trading Pipeline Demo")
    print("This demo will showcase all major functionality:")
    
    # Activate virtual environment
    venv_prefix = "source venv/bin/activate && "
    
    commands = [
        (venv_prefix + "python3 main.py fetch-data --symbols BTCUSDT --timeframes 1h --days 7", 
         "1. Fetching Historical Data"),
        
        (venv_prefix + "python3 main.py train --symbol BTCUSDT --timeframe 1h --models lightgbm --target binary", 
         "2. Training ML Model"),
        
        (venv_prefix + "python3 main.py list-models", 
         "3. Listing Registered Models"),
        
        (venv_prefix + "python3 main.py schedule --setup", 
         "4. Setting Up Automated Scheduler"),
    ]
    
    success_count = 0
    
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
        time.sleep(2)  # Pause between commands
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 DEMO SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful operations: {success_count}/{len(commands)}")
    
    if success_count == len(commands):
        print("🎉 All components working perfectly!")
        print("\n📋 Next Steps:")
        print("1. Start the scheduler: python3 main.py schedule --start")
        print("2. Run backtests: python3 main.py backtest --symbol BTCUSDT")
        print("3. Add more models: python3 main.py train --models xgboost")
        print("4. Check documentation: README.md")
    else:
        print("⚠️  Some operations failed. Check the error messages above.")
    
    print(f"\n📁 Generated Files:")
    print("- data/: SQLite database and Parquet files")
    print("- models/: Trained model artifacts and registry")
    print("- logs/: Application logs (if any)")
    
    print(f"\n🔧 Configuration:")
    print("- Edit .env file for custom settings")
    print("- Modify src/config.py for default parameters")

if __name__ == "__main__":
    main()