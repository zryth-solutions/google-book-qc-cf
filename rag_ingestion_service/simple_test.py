#!/usr/bin/env python3
"""
Simple test script to verify basic functionality
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic functionality without API calls"""
    try:
        print("Testing basic functionality...")
        
        # Test environment variables
        print(f"PROJECT_ID: {os.getenv('PROJECT_ID', 'NOT_SET')}")
        print(f"BUCKET_NAME: {os.getenv('BUCKET_NAME', 'NOT_SET')}")
        print(f"REGION: {os.getenv('REGION', 'NOT_SET')}")
        
        # Test imports
        print("Testing imports...")
        from semantic_chunker import SemanticChunker
        print("✅ SemanticChunker imported")
        
        from embedding_generator import EmbeddingGenerator
        print("✅ EmbeddingGenerator imported")
        
        from vector_store import VectorStore
        print("✅ VectorStore imported")
        
        from pdf_to_markdown import PDFToMarkdownConverter
        print("✅ PDFToMarkdownConverter imported")
        
        # Test basic initialization
        print("Testing basic initialization...")
        chunker = SemanticChunker()
        print("✅ SemanticChunker initialized")
        
        # Test CLI import
        print("Testing CLI import...")
        from cli_main import process_pdf_to_vector, process_folder_to_vector
        print("✅ CLI functions imported")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Simple RAG Ingestion Test")
    print("=" * 50)
    
    success = test_basic_functionality()
    
    print("\n" + "=" * 50)
    print(f"Test {'PASSED' if success else 'FAILED'}")
    print("=" * 50)
    
    sys.exit(0 if success else 1)
