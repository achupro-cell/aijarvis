"""
REST API for indicator service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import List
from service import IndicatorService, OHLCVRequest, IndicatorResponse

app = FastAPI(
    title="Indicator Computation Service",
    description="REST/gRPC service for Firefly Oscillator, SQZMOM Combo, and STAI v6 indicators",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
indicator_service = IndicatorService()

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time header for performance monitoring"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Indicator Computation Service",
        "status": "healthy",
        "version": "1.0.0",
        "indicators": ["firefly", "sqzmom", "stai"]
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "indicator-computation",
        "indicators_available": {
            "firefly": "Firefly Oscillator (LazyBear)",
            "sqzmom": "SQZMOM Combo",
            "stai": "STAI v6"
        }
    }

@app.post("/calculate", response_model=IndicatorResponse)
async def calculate_indicators(request: OHLCVRequest):
    """
    Calculate indicators from OHLCV data
    
    - **high**: Array of high prices
    - **low**: Array of low prices  
    - **close**: Array of close prices
    - **volume**: Array of volumes (required for SQZMOM)
    - **indicators**: List of indicators to calculate ["firefly", "sqzmom", "stai"]
    """
    try:
        # Validate request
        if not request.indicators:
            raise HTTPException(status_code=400, detail="At least one indicator must be specified")
        
        # Validate indicator names
        valid_indicators = {"firefly", "sqzmom", "stai"}
        invalid_indicators = set(ind.lower() for ind in request.indicators) - valid_indicators
        if invalid_indicators:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid indicators: {list(invalid_indicators)}. Valid: {list(valid_indicators)}"
            )
        
        # Calculate indicators
        result = indicator_service.calculate_indicators(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.data.get('error', 'Calculation failed'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/cache/{indicator}")
async def get_cached_indicator(indicator: str):
    """Get cached latest values for an indicator"""
    try:
        cached_data = indicator_service.get_cached_latest(indicator.lower())
        if cached_data is None:
            raise HTTPException(status_code=404, detail=f"No cached data found for indicator: {indicator}")
        
        return {
            "success": True,
            "data": cached_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/indicators")
async def list_indicators():
    """List available indicators and their parameters"""
    return {
        "indicators": {
            "firefly": {
                "name": "Firefly Oscillator",
                "description": "LazyBear's Firefly Oscillator based on Bollinger Bands",
                "parameters": {
                    "length": {"default": 20, "type": "int", "description": "Period for calculations"},
                    "mult": {"default": 2.0, "type": "float", "description": "Multiplier for bands"}
                },
                "inputs": ["high", "low", "close"],
                "outputs": ["oscillator", "signal", "buy_signal", "sell_signal", "neutral_signal"]
            },
            "sqzmom": {
                "name": "SQZMOM Combo",
                "description": "Squeeze Momentum indicator combining Bollinger Bands and Keltner Channels",
                "parameters": {
                    "bb_length": {"default": 20, "type": "int", "description": "Bollinger Bands period"},
                    "bb_mult": {"default": 2.0, "type": "float", "description": "Bollinger Bands multiplier"},
                    "kc_length": {"default": 20, "type": "int", "description": "Keltner Channels period"},
                    "kc_mult": {"default": 1.5, "type": "float", "description": "Keltner Channels multiplier"}
                },
                "inputs": ["high", "low", "close", "volume"],
                "outputs": ["momentum", "histogram", "squeeze_on", "buy_signal", "sell_signal", "neutral_signal"]
            },
            "stai": {
                "name": "STAI v6",
                "description": "Super Trend Adaptive Indicator v6 combining MACD, RSI, and Stochastic",
                "parameters": {
                    "fast_length": {"default": 12, "type": "int", "description": "Fast EMA period"},
                    "slow_length": {"default": 26, "type": "int", "description": "Slow EMA period"},
                    "signal_length": {"default": 9, "type": "int", "description": "Signal line period"},
                    "rsi_length": {"default": 14, "type": "int", "description": "RSI period"}
                },
                "inputs": ["high", "low", "close"],
                "outputs": ["stai_score", "macd", "rsi", "buy_signal", "sell_signal", "neutral_signal"]
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)