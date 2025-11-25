#!/bin/bash

# ML Pipeline Setup Script

echo "Setting up ML Trading Pipeline..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 first."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check if TA-Lib is installed
if ! python3 -c "import talib" &> /dev/null; then
    echo "TA-Lib is not installed. Attempting to install..."
    
    # Check if we can install system dependencies
    if command -v apt-get &> /dev/null; then
        echo "Installing TA-Lib system dependencies..."
        sudo apt-get update
        sudo apt-get install -y build-essential wget
        
        # Download and compile TA-Lib
        cd /tmp
        if [ ! -f "ta-lib-0.4.0-src.tar.gz" ]; then
            wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        fi
        
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib/
        ./configure --prefix=/usr
        make
        sudo make install
        cd /tmp
        
        # Install Python TA-Lib
        pip3 install TA-Lib
        
        echo "TA-Lib installation completed."
    else
        echo "Could not install TA-Lib automatically. Please install it manually:"
        echo "https://mrjbq7.github.io/ta-lib/install.html"
    fi
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p data models logs

# Copy environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from template. Please edit it as needed."
fi

echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Run the test script: python3 test_pipeline.py"
echo "2. Fetch data: python3 main.py fetch-data"
echo "3. Train models: python3 main.py train"
echo "4. Backtest: python3 main.py backtest"
echo "5. Setup scheduler: python3 main.py schedule --setup --start"