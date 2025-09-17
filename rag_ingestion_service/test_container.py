#!/usr/bin/env python3
"""
Test script to debug container issues
"""

import sys
import os
import traceback

def test_imports():
    """Test all imports to see what's failing"""
    print("Testing imports...")
    
    try:
        print("1. Testing basic imports...")
        import logging
        import json
        import argparse
        import tempfile
        print("   ✅ Basic imports successful")
        
        print("2. Testing Google Cloud imports...")
        from google.cloud import storage
        print("   ✅ Google Cloud Storage imported")
        
        import vertexai
        print("   ✅ Vertex AI imported")
        
        print("3. Testing Qdrant imports...")
        from qdrant_client import QdrantClient
        print("   ✅ Qdrant client imported")
        
        print("4. Testing other dependencies...")
        import requests
        import numpy as np
        import tiktoken
        import markdown
        import bs4
        print("   ✅ Other dependencies imported")
        
        print("5. Testing our modules...")
        from pdf_to_markdown import PDFToMarkdownConverter
        print("   ✅ PDFToMarkdownConverter imported")
        
        from semantic_chunker import SemanticChunker
        print("   ✅ SemanticChunker imported")
        
        from embedding_generator import EmbeddingGenerator
        print("   ✅ EmbeddingGenerator imported")
        
        from vector_store import VectorStore
        print("   ✅ VectorStore imported")
        
        print("6. Testing utils import...")
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.gcp.bucket_manager import BucketManager
        print("   ✅ BucketManager imported")
        
        print("7. Testing CLI functions...")
        from cli_main import process_folder_to_vector
        print("   ✅ CLI functions imported")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_basic_functionality():
    """Test basic functionality without API keys"""
    print("\nTesting basic functionality...")
    
    try:
        # Test environment variables
        print(f"PROJECT_ID: {os.getenv('PROJECT_ID', 'NOT_SET')}")
        print(f"BUCKET_NAME: {os.getenv('BUCKET_NAME', 'NOT_SET')}")
        print(f"REGION: {os.getenv('REGION', 'NOT_SET')}")
        print(f"MARKER_API_KEY: {'SET' if os.getenv('MARKER_API_KEY') else 'NOT_SET'}")
        print(f"QDRANT_API_KEY: {'SET' if os.getenv('QDRANT_API_KEY') else 'NOT_SET'}")
        
        # Test basic classes
        from semantic_chunker import SemanticChunker
        chunker = SemanticChunker()
        print("   ✅ SemanticChunker initialized")
        
        print("\n🎉 Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic functionality test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("RAG Ingestion Container Debug Test")
    print("=" * 50)
    
    success = test_imports()
    if success:
        test_basic_functionality()
    
    print("\n" + "=" * 50)
    print("Test completed")
    print("=" * 50)
