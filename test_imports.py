#!/usr/bin/env python3
"""
Test script to check imports for RAG ingestion service
"""

import sys
import os

# Add the rag_ingestion_service directory to path
sys.path.append('rag_ingestion_service')

try:
    print("Testing imports...")
    
    # Test basic imports
    from rag_ingestion_service.pdf_to_markdown import PDFToMarkdownConverter
    print("✅ PDFToMarkdownConverter imported successfully")
    
    from rag_ingestion_service.semantic_chunker import SemanticChunker
    print("✅ SemanticChunker imported successfully")
    
    from rag_ingestion_service.embedding_generator import EmbeddingGenerator
    print("✅ EmbeddingGenerator imported successfully")
    
    from rag_ingestion_service.vector_store import VectorStore
    print("✅ VectorStore imported successfully")
    
    from rag_ingestion_service.cli_main import process_pdf_to_vector
    print("✅ CLI functions imported successfully")
    
    print("\n🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
