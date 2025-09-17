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
from embeddings_cache import EmbeddingsCache

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
QDRANT_URL = os.getenv('QDRANT_URL', 'https://9becb4cf-82b6-456f-ae0c-d797c6c946cc.us-east4-0.gcp.cloud.qdrant.io')

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
        embeddings_cache = EmbeddingsCache(PROJECT_ID, BUCKET_NAME)
        bucket_manager = BucketManager(PROJECT_ID, BUCKET_NAME)
        
        # Initialize vector store (with error handling)
        vector_store = None
        vector_store_error = None
        try:
            vector_store = VectorStore(QDRANT_API_KEY, QDRANT_URL)
            logger.info("✅ Vector store connection successful")
        except Exception as e:
            vector_store_error = str(e)
            logger.warning(f"⚠️ Vector store connection failed: {vector_store_error}")
            logger.info("📦 Will use embeddings cache only")
        
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
        
        # Step 4: Check embeddings cache first
        logger.info(f"Checking embeddings cache for {len(chunks)} chunks")
        cached_result = embeddings_cache.load_embeddings(book_name, chapter, chunks)
        cache_saved = False
        
        if cached_result:
            chunks, embeddings = cached_result
            logger.info(f"✅ Using cached embeddings ({len(embeddings)} embeddings)")
            cache_saved = True  # Already cached
        else:
            # Step 4a: Generate embeddings
            logger.info(f"🔄 Generating new embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = embedding_generator.generate_embeddings(chunk_texts)
            
            if not embeddings:
                return {
                    "status": "error",
                    "error": "Failed to generate embeddings",
                    "step": "embedding_generation"
                }
            
            # Step 4b: Save embeddings to cache
            logger.info("💾 Saving embeddings to cache")
            cache_saved = embeddings_cache.save_embeddings(book_name, chapter, chunks, embeddings)
            if cache_saved:
                logger.info("✅ Embeddings cached successfully")
            else:
                logger.warning("⚠️ Failed to cache embeddings (continuing anyway)")
        
        # Step 5: Try to store in vector database (optional if connection failed)
        collection_info = None
        vector_storage_status = "skipped"
        
        if vector_store is not None:
            try:
                collection_name = f"book_{book_name.lower().replace(' ', '_')}"
                if chapter is not None:
                    collection_name += f"_chapter_{chapter}"
                
                logger.info(f"🗄️ Creating/updating vector collection: {collection_name}")
                
                if vector_store.create_collection(collection_name, book_name):
                    logger.info("✅ Vector collection created successfully")
                    
                    # Store chunks and embeddings
                    logger.info("📤 Storing chunks and embeddings in vector database")
                    if vector_store.upsert_chunks(collection_name, chunks, embeddings):
                        logger.info("✅ Chunks stored in vector database successfully")
                        collection_info = vector_store.get_collection_info(collection_name)
                        vector_storage_status = "success"
                    else:
                        logger.warning("⚠️ Failed to store chunks in vector database")
                        vector_storage_status = "failed_upsert"
                else:
                    logger.warning("⚠️ Failed to create vector collection")
                    vector_storage_status = "failed_collection"
                    
            except Exception as e:
                logger.warning(f"⚠️ Vector database operation failed: {str(e)}")
                vector_storage_status = f"error: {str(e)}"
        else:
            logger.info("⏭️ Skipping vector database storage (connection not available)")
            logger.info(f"   Embeddings are safely cached in GCS for later processing")
        
        return {
            "status": "success",
            "book_name": book_name,
            "chapter": chapter,
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings),
            "embeddings_cached": cache_saved,
            "embeddings_from_cache": bool(cached_result),
            "markdown_gcs_path": gcs_path,
            "vector_storage_status": vector_storage_status,
            "collection_info": collection_info,
            "vector_store_error": vector_store_error
        }
        
    except Exception as e:
        logger.error(f"Error in process_pdf_to_vector: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "step": "unknown"
        }

def process_folder_to_vector(folder_path: str, book_name: str, 
                           update_existing: bool = False) -> Dict[str, Any]:
    """
    Process all PDFs in a folder: PDFs -> Markdown -> Chunks -> Embeddings -> Vector Store
    
    Args:
        folder_path: Path to folder containing PDF files (GCS)
        book_name: Name of the book
        update_existing: Whether to update existing collection
        
    Returns:
        Dict containing processing results
    """
    logger.info(f"Starting folder processing for {folder_path}")
    
    # Initialize bucket manager
    bucket_manager = BucketManager(PROJECT_ID, BUCKET_NAME)
    
    # List all PDF files in the folder
    pdf_files = bucket_manager.list_files_in_folder(folder_path, '.pdf')
    
    if not pdf_files:
        logger.warning(f"No PDF files found in folder {folder_path}")
        return {
            'status': 'warning',
            'message': f'No PDF files found in folder {folder_path}',
            'processed_files': [],
            'failed_files': []
        }
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    results = {
        'status': 'success',
        'message': f'Processed {len(pdf_files)} PDF files from folder {folder_path}',
        'processed_files': [],
        'failed_files': [],
        'folder_path': folder_path,
        'book_name': book_name
    }
    
    # Process each PDF file
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_path}")
            
            # Extract chapter number from filename if possible
            # Assuming filename format like "chapter_1.pdf" or "01.pdf"
            import re
            filename = pdf_path.split('/')[-1]
            chapter_match = re.search(r'chapter[_\s]*(\d+)', filename, re.IGNORECASE)
            if not chapter_match:
                chapter_match = re.search(r'^(\d+)', filename)
            
            chapter = int(chapter_match.group(1)) if chapter_match else None
            
            # Process the PDF
            file_result = process_pdf_to_vector(
                pdf_path, 
                book_name, 
                chapter, 
                update_existing
            )
            
            if file_result.get('status') == 'success':
                results['processed_files'].append({
                    'file': pdf_path,
                    'chapter': chapter,
                    'result': file_result
                })
                logger.info(f"Successfully processed {pdf_path}")
            else:
                results['failed_files'].append({
                    'file': pdf_path,
                    'chapter': chapter,
                    'error': file_result.get('message', 'Unknown error')
                })
                logger.error(f"Failed to process {pdf_path}: {file_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Error processing {pdf_path}: {str(e)}"
            logger.error(error_msg)
            results['failed_files'].append({
                'file': pdf_path,
                'chapter': None,
                'error': error_msg
            })
    
    # Update overall status based on results
    if results['failed_files'] and not results['processed_files']:
        results['status'] = 'error'
        results['message'] = f'All {len(pdf_files)} files failed to process'
    elif results['failed_files']:
        results['status'] = 'partial'
        results['message'] = f'Processed {len(results["processed_files"])}/{len(pdf_files)} files successfully'
    
    logger.info(f"Folder processing completed. Status: {results['status']}")
    return results

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
    parser.add_argument('--folder-path', help='Path to folder containing PDF files (for process operation)')
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
    
    # QDRANT_URL now has a default value, so no warning needed
    
    result = {}
    
    try:
        if args.operation == 'process':
            if not args.pdf_path and not args.folder_path:
                logger.error("Either --pdf-path or --folder-path is required for process operation")
                sys.exit(1)
            
            if args.pdf_path and args.folder_path:
                logger.error("Cannot specify both --pdf-path and --folder-path. Choose one.")
                sys.exit(1)
            
            if args.pdf_path:
                # Process single PDF
                result = process_pdf_to_vector(
                    args.pdf_path, 
                    args.book_name, 
                    args.chapter, 
                    args.update_existing
                )
            else:
                # Process folder
                result = process_folder_to_vector(
                    args.folder_path,
                    args.book_name,
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
