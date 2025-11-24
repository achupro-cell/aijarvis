#!/usr/bin/env python3
"""
Generate gRPC Python files from protobuf definition
"""
import subprocess
import sys
import os

def generate_grpc_files():
    """Generate gRPC Python files from .proto file"""
    try:
        # Check if protobuf file exists
        if not os.path.exists('indicators.proto'):
            print("Error: indicators.proto not found")
            return False
        
        # Generate gRPC files
        cmd = [
            'python', '-m', 'grpc_tools.protoc',
            '--python_out=.',
            '--grpc_python_out=.',
            '--proto_path=.',
            'indicators.proto'
        ]
        
        print("Generating gRPC files...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error generating gRPC files: {result.stderr}")
            return False
        
        print("✓ gRPC files generated successfully")
        
        # Check if files were created
        expected_files = ['indicators_pb2.py', 'indicators_pb2_grpc.py']
        for file in expected_files:
            if os.path.exists(file):
                print(f"✓ {file} created")
            else:
                print(f"✗ {file} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    success = generate_grpc_files()
    sys.exit(0 if success else 1)