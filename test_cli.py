#!/usr/bin/env python3
"""
Test script to check CLI functionality
"""

import sys
import os

# Add the rag_ingestion_service directory to path
sys.path.append('rag_ingestion_service')

try:
    print("Testing CLI imports...")
    
    # Test CLI import
    from rag_ingestion_service.cli_main import process_folder_to_vector
    print("✅ CLI functions imported successfully")
    
    # Test basic functionality without API keys
    print("\nTesting basic functionality...")
    
    # This should fail gracefully due to missing API keys
    try:
        result = process_folder_to_vector("test_folder", "test_book")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error (missing API keys): {e}")
    
    print("\n🎉 CLI test completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
