"""
gRPC server for indicator service
"""
import grpc
import time
from concurrent import futures
import indicators_pb2
import indicators_pb2_grpc
from service import IndicatorService, OHLCVRequest

class IndicatorServiceImpl(indicators_pb2_grpc.IndicatorServiceServicer):
    def __init__(self):
        self.indicator_service = IndicatorService()
    
    def CalculateIndicators(self, request, context):
        """Calculate indicators via gRPC"""
        try:
            # Convert gRPC request to internal format
            ohlcv_request = OHLCVRequest(
                high=list(request.high),
                low=list(request.low),
                close=list(request.close),
                volume=list(request.volume) if request.volume else None,
                indicators=list(request.indicators)
            )
            
            # Calculate indicators
            result = self.indicator_service.calculate_indicators(ohlcv_request)
            
            # Convert to gRPC response
            response = indicators_pb2.CalculateResponse()
            response.success = result.success
            
            if result.success:
                # Convert indicator data
                for indicator_name, indicator_data in result.data['indicators'].items():
                    indicator_result = indicators_pb2.IndicatorResult()
                    
                    # Convert arrays
                    for key, value in indicator_data.items():
                        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], bool):
                            # Boolean array
                            if key == 'buy_signal':
                                indicator_result.buy_signal.extend(value)
                            elif key == 'sell_signal':
                                indicator_result.sell_signal.extend(value)
                            elif key == 'neutral_signal':
                                indicator_result.neutral_signal.extend(value)
                            elif key == 'squeeze_on':
                                indicator_result.squeeze_on.extend(value)
                            elif key == 'squeeze_off':
                                indicator_result.squeeze_off.extend(value)
                        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], (int, float)):
                            # Double array
                            if key == 'oscillator':
                                indicator_result.oscillator.extend(value)
                            elif key == 'signal':
                                indicator_result.signal.extend(value)
                            elif key == 'upper_band':
                                indicator_result.upper_band.extend(value)
                            elif key == 'lower_band':
                                indicator_result.lower_band.extend(value)
                            elif key == 'momentum':
                                indicator_result.momentum.extend(value)
                            elif key == 'histogram':
                                indicator_result.histogram.extend(value)
                            elif key == 'bb_upper':
                                indicator_result.bb_upper.extend(value)
                            elif key == 'bb_lower':
                                indicator_result.bb_lower.extend(value)
                            elif key == 'kc_upper':
                                indicator_result.kc_upper.extend(value)
                            elif key == 'kc_lower':
                                indicator_result.kc_lower.extend(value)
                            elif key == 'stai_score':
                                indicator_result.stai_score.extend(value)
                            elif key == 'macd':
                                indicator_result.macd.extend(value)
                            elif key == 'rsi':
                                indicator_result.rsi.extend(value)
                            elif key == 'stoch_k':
                                indicator_result.stoch_k.extend(value)
                            elif key == 'stoch_d':
                                indicator_result.stoch_d.extend(value)
                    
                    # Add metadata
                    if 'metadata' in indicator_data:
                        metadata = indicator_data['metadata']
                        indicator_result.metadata.indicator = metadata.get('indicator', '')
                        for key, value in metadata.items():
                            if key != 'indicator':
                                indicator_result.metadata.parameters[key] = str(value)
                    
                    response.data.indicators[indicator_name].CopyFrom(indicator_result)
                
                # Add composite signals
                if 'composite_signals' in result.data:
                    comp_signals = result.data['composite_signals']
                    response.data.composite_signals.buy_signal.extend(comp_signals['buy_signal'])
                    response.data.composite_signals.sell_signal.extend(comp_signals['sell_signal'])
                    response.data.composite_signals.neutral_signal.extend(comp_signals['neutral_signal'])
                    response.data.composite_signals.methodology = comp_signals['methodology']
                
                response.data.input_length = result.data['input_length']
                
                # Add metadata
                response.metadata.indicators_calculated.extend(result.metadata['indicators_calculated'])
                response.metadata.last_updated = result.metadata['last_updated']
            
            else:
                response.metadata.error = True
                response.metadata.error_message = result.data.get('error', 'Unknown error')
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return indicators_pb2.CalculateResponse()
    
    def GetCachedIndicator(self, request, context):
        """Get cached indicator data"""
        try:
            cached_data = self.indicator_service.get_cached_latest(request.indicator.lower())
            
            response = indicators_pb2.CacheResponse()
            response.success = cached_data is not None
            
            if cached_data:
                response.data.timestamp = cached_data['timestamp']
                response.data.data_length = cached_data['data_length']
                
                for key, value in cached_data['last_values'].items():
                    cached_values = indicators_pb2.CachedValues()
                    
                    if isinstance(value, list):
                        if len(value) > 0 and isinstance(value[0], bool):
                            cached_values.bool_array.values.extend(value)
                        elif len(value) > 0 and isinstance(value[0], (int, float)):
                            cached_values.double_array.values.extend(value)
                    elif isinstance(value, bool):
                        cached_values.single_bool = value
                    elif isinstance(value, (int, float)):
                        cached_values.single_double = value
                    
                    response.data.last_values[key].CopyFrom(cached_values)
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return indicators_pb2.CacheResponse()
    
    def ListIndicators(self, request, context):
        """List available indicators"""
        try:
            response = indicators_pb2.ListResponse()
            
            # Firefly Oscillator
            firefly_info = indicators_pb2.IndicatorInfo()
            firefly_info.name = "Firefly Oscillator"
            firefly_info.description = "LazyBear's Firefly Oscillator based on Bollinger Bands"
            
            firefly_info.parameters["length"].default_value = "20"
            firefly_info.parameters["length"].type = "int"
            firefly_info.parameters["length"].description = "Period for calculations"
            
            firefly_info.parameters["mult"].default_value = "2.0"
            firefly_info.parameters["mult"].type = "float"
            firefly_info.parameters["mult"].description = "Multiplier for bands"
            
            firefly_info.inputs.extend(["high", "low", "close"])
            firefly_info.outputs.extend(["oscillator", "signal", "buy_signal", "sell_signal", "neutral_signal"])
            
            response.indicators["firefly"].CopyFrom(firefly_info)
            
            # SQZMOM Combo
            sqzmom_info = indicators_pb2.IndicatorInfo()
            sqzmom_info.name = "SQZMOM Combo"
            sqzmom_info.description = "Squeeze Momentum indicator combining Bollinger Bands and Keltner Channels"
            
            sqzmom_info.parameters["bb_length"].default_value = "20"
            sqzmom_info.parameters["bb_length"].type = "int"
            sqzmom_info.parameters["bb_length"].description = "Bollinger Bands period"
            
            sqzmom_info.parameters["bb_mult"].default_value = "2.0"
            sqzmom_info.parameters["bb_mult"].type = "float"
            sqzmom_info.parameters["bb_mult"].description = "Bollinger Bands multiplier"
            
            sqzmom_info.parameters["kc_length"].default_value = "20"
            sqzmom_info.parameters["kc_length"].type = "int"
            sqzmom_info.parameters["kc_length"].description = "Keltner Channels period"
            
            sqzmom_info.parameters["kc_mult"].default_value = "1.5"
            sqzmom_info.parameters["kc_mult"].type = "float"
            sqzmom_info.parameters["kc_mult"].description = "Keltner Channels multiplier"
            
            sqzmom_info.inputs.extend(["high", "low", "close", "volume"])
            sqzmom_info.outputs.extend(["momentum", "histogram", "squeeze_on", "buy_signal", "sell_signal", "neutral_signal"])
            
            response.indicators["sqzmom"].CopyFrom(sqzmom_info)
            
            # STAI v6
            stai_info = indicators_pb2.IndicatorInfo()
            stai_info.name = "STAI v6"
            stai_info.description = "Super Trend Adaptive Indicator v6 combining MACD, RSI, and Stochastic"
            
            stai_info.parameters["fast_length"].default_value = "12"
            stai_info.parameters["fast_length"].type = "int"
            stai_info.parameters["fast_length"].description = "Fast EMA period"
            
            stai_info.parameters["slow_length"].default_value = "26"
            stai_info.parameters["slow_length"].type = "int"
            stai_info.parameters["slow_length"].description = "Slow EMA period"
            
            stai_info.parameters["signal_length"].default_value = "9"
            stai_info.parameters["signal_length"].type = "int"
            stai_info.parameters["signal_length"].description = "Signal line period"
            
            stai_info.parameters["rsi_length"].default_value = "14"
            stai_info.parameters["rsi_length"].type = "int"
            stai_info.parameters["rsi_length"].description = "RSI period"
            
            stai_info.inputs.extend(["high", "low", "close"])
            stai_info.outputs.extend(["stai_score", "macd", "rsi", "buy_signal", "sell_signal", "neutral_signal"])
            
            response.indicators["stai"].CopyFrom(stai_info)
            
            return response
            
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return indicators_pb2.ListResponse()

def serve():
    """Start gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    indicators_pb2_grpc.add_IndicatorServiceServicer_to_server(
        IndicatorServiceImpl(), server
    )
    
    server.add_insecure_port('[::]:50051')
    print("Starting gRPC server on port 50051...")
    server.start()
    
    try:
        while True:
            time.sleep(86400)  # One day
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()