#!/usr/bin/env python3
"""
RAG Ingestion CLI Application
Command-line interface for PDF to markdown conversion with vector storage
"""

import os
import sys
import json
import argparse
import tempfile
import logging
from typing import Dict, Any, Optional

# Import our modules
from pdf_to_markdown import PDFToMarkdownConverter
from semantic_chunker import SemanticChunker
from embedding_generator import EmbeddingGenerator
from vector_store import VectorStore

# Add parent directory to path for utils import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gcp.bucket_manager import BucketManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get configuration from environment variables
PROJECT_ID = os.getenv('PROJECT_ID', 'book-qc-cf')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'llm-books')
REGION = os.getenv('REGION', 'us-central1')
MARKER_API_KEY = os.getenv('MARKER_API_KEY')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL', 'https://qdrant.tech')

def process_pdf_to_vector(pdf_path: str, book_name: str, chapter: Optional[int] = None, 
                         update_existing: bool = False) -> Dict[str, Any]:
    """
    Complete pipeline: PDF -> Markdown -> Chunks -> Embeddings -> Vector Store
    
    Args:
        pdf_path: Path to PDF file (local or GCS)
        book_name: Name of the book
        chapter: Optional chapter number
        update_existing: Whether to update existing collection
        
    Returns:
        Processing result
    """
    try:
        # Initialize components
        pdf_converter = PDFToMarkdownConverter(MARKER_API_KEY)
        chunker = SemanticChunker()
        embedding_generator = EmbeddingGenerator(PROJECT_ID, REGION)
        vector_store = VectorStore(QDRANT_API_KEY, QDRANT_URL)
        bucket_manager = BucketManager(PROJECT_ID, BUCKET_NAME)
        
        # Step 1: Convert PDF to Markdown
        logger.info(f"Converting PDF to markdown: {pdf_path}")
        conversion_result = pdf_converter.convert_pdf_to_markdown(pdf_path)
        
        if not conversion_result["success"]:
            return {
                "status": "error",
                "error": f"PDF conversion failed: {conversion_result['error']}",
                "step": "pdf_conversion"
            }
        
        markdown_content = conversion_result["markdown_content"]
        
        # Step 2: Upload markdown to GCS
        logger.info("Uploading markdown to GCS")
        # Generate file path
        if chapter is not None:
            file_path = f"books/{book_name}/chapter_{chapter:02d}.md"
        else:
            file_path = f"books/{book_name}/full_book.md"
        
        if not bucket_manager.upload_text(markdown_content, file_path, "text/markdown"):
            return {
                "status": "error",
                "error": "Failed to upload markdown to GCS",
                "step": "markdown_upload"
            }
        
        gcs_path = f"gs://{BUCKET_NAME}/{file_path}"
        
        # Step 3: Create semantic chunks
        logger.info("Creating semantic chunks")
        chunks = chunker.chunk_markdown(markdown_content, book_name, chapter)
        
        if not chunks:
            return {
                "status": "error",
                "error": "Failed to create chunks",
                "step": "chunking"
            }
        
        # Step 4: Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = embedding_generator.generate_embeddings(chunk_texts)
        
        if not embeddings:
            return {
                "status": "error",
                "error": "Failed to generate embeddings",
                "step": "embedding_generation"
            }
        
        # Step 5: Create/Update vector collection
        collection_name = f"book_{book_name.lower().replace(' ', '_')}"
        if chapter is not None:
            collection_name += f"_chapter_{chapter}"
        
        logger.info(f"Creating/updating collection: {collection_name}")
        
        if not vector_store.create_collection(collection_name, book_name):
            return {
                "status": "error",
                "error": "Failed to create collection",
                "step": "collection_creation"
            }
        
        # Step 6: Store chunks and embeddings
        logger.info("Storing chunks and embeddings in vector database")
        if not vector_store.upsert_chunks(collection_name, chunks, embeddings):
            return {
                "status": "error",
                "error": "Failed to store chunks in vector database",
                "step": "vector_storage"
            }
        
        # Get collection info
        collection_info = vector_store.get_collection_info(collection_name)
        
        return {
            "status": "success",
            "book_name": book_name,
            "chapter": chapter,
            "collection_name": collection_name,
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings),
            "markdown_gcs_path": gcs_path,
            "collection_info": collection_info
        }
        
    except Exception as e:
        logger.error(f"Error in process_pdf_to_vector: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "step": "unknown"
        }

def search_vectors(book_name: str, query: str, chapter: Optional[int] = None, 
                  limit: int = 10, score_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Search for similar content in vector database
    
    Args:
        book_name: Name of the book
        query: Search query
        chapter: Optional chapter number
        limit: Maximum number of results
        score_threshold: Minimum similarity score
        
    Returns:
        Search results
    """
    try:
        # Initialize components
        embedding_generator = EmbeddingGenerator(PROJECT_ID, REGION)
        vector_store = VectorStore(QDRANT_API_KEY, QDRANT_URL)
        
        # Generate query embedding
        query_embedding = embedding_generator.generate_single_embedding(query)
        if not query_embedding:
            return {
                "status": "error",
                "error": "Failed to generate query embedding"
            }
        
        # Determine collection name
        collection_name = f"book_{book_name.lower().replace(' ', '_')}"
        if chapter is not None:
            collection_name += f"_chapter_{chapter}"
        
        # Search vectors
        results = vector_store.search_similar(
            collection_name, 
            query_embedding, 
            limit, 
            score_threshold
        )
        
        return {
            "status": "success",
            "query": query,
            "book_name": book_name,
            "chapter": chapter,
            "collection_name": collection_name,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in search_vectors: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def list_collections() -> Dict[str, Any]:
    """List all collections in vector database"""
    try:
        vector_store = VectorStore(QDRANT_API_KEY, QDRANT_URL)
        collections = vector_store.list_collections()
        
        collection_info = []
        for collection_name in collections:
            info = vector_store.get_collection_info(collection_name)
            if info:
                collection_info.append(info)
        
        return {
            "status": "success",
            "collections": collection_info,
            "total_collections": len(collection_info)
        }
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='RAG Ingestion CLI')
    parser.add_argument('operation', choices=[
        'process',
        'search',
        'list-collections'
    ], help='Operation to perform')
    
    # Common arguments
    parser.add_argument('--pdf-path', help='Path to PDF file (for process operation)')
    parser.add_argument('--book-name', required=True, help='Name of the book')
    parser.add_argument('--chapter', type=int, help='Chapter number (optional)')
    parser.add_argument('--update-existing', action='store_true', 
                       help='Update existing collection (for process operation)')
    
    # Search arguments
    parser.add_argument('--query', help='Search query (for search operation)')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of search results')
    parser.add_argument('--score-threshold', type=float, default=0.7, 
                       help='Minimum similarity score for search results')
    
    args = parser.parse_args()
    
    # Validate required environment variables
    if not MARKER_API_KEY:
        logger.error("MARKER_API_KEY environment variable is required")
        sys.exit(1)
    
    if not QDRANT_API_KEY:
        logger.error("QDRANT_API_KEY environment variable is required")
        sys.exit(1)
    
    result = {}
    
    try:
        if args.operation == 'process':
            if not args.pdf_path:
                logger.error("--pdf-path is required for process operation")
                sys.exit(1)
            
            result = process_pdf_to_vector(
                args.pdf_path, 
                args.book_name, 
                args.chapter, 
                args.update_existing
            )
            
        elif args.operation == 'search':
            if not args.query:
                logger.error("--query is required for search operation")
                sys.exit(1)
            
            result = search_vectors(
                args.book_name, 
                args.query, 
                args.chapter, 
                args.limit, 
                args.score_threshold
            )
            
        elif args.operation == 'list-collections':
            result = list_collections()
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        result = {
            "status": "error",
            "error": str(e)
        }
    
    # Output result as JSON
    print(json.dumps(result, indent=2))
    
    # Set exit code based on status
    if result.get('status') != 'success':
        sys.exit(1)

if __name__ == '__main__':
    main()
