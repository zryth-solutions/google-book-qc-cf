"""
Embeddings Cache Manager - Saves/loads embeddings to/from GCS
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class EmbeddingsCache:
    """Manages embeddings caching to GCS for reliability and cost optimization"""
    
    def __init__(self, project_id: str, bucket_name: str):
        """
        Initialize embeddings cache
        
        Args:
            project_id: Google Cloud project ID
            bucket_name: GCS bucket name
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        
        # Import bucket manager
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from utils.gcp.bucket_manager import BucketManager
        self.bucket_manager = BucketManager(project_id, bucket_name)
        
    def _get_cache_key(self, book_name: str, chapter: Optional[int] = None) -> str:
        """Generate cache key for embeddings"""
        if chapter is not None:
            return f"embeddings/{book_name.lower().replace(' ', '_')}/chapter_{chapter:02d}.json"
        else:
            return f"embeddings/{book_name.lower().replace(' ', '_')}/full_book.json"
    
    def _generate_content_hash(self, chunks: List[Any]) -> str:
        """Generate hash of chunk contents for cache validation"""
        content = "".join([chunk.content for chunk in chunks])
        return hashlib.md5(content.encode()).hexdigest()
    
    def save_embeddings(self, book_name: str, chapter: Optional[int], chunks: List[Any], 
                       embeddings: List[List[float]]) -> bool:
        """
        Save embeddings to GCS cache
        
        Args:
            book_name: Name of the book
            chapter: Chapter number (None for full book)
            chunks: List of semantic chunks
            embeddings: List of embeddings corresponding to chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._get_cache_key(book_name, chapter)
            content_hash = self._generate_content_hash(chunks)
            
            # Prepare cache data
            cache_data = {
                "metadata": {
                    "book_name": book_name,
                    "chapter": chapter,
                    "created_at": datetime.utcnow().isoformat(),
                    "content_hash": content_hash,
                    "chunk_count": len(chunks),
                    "embedding_dimension": len(embeddings[0]) if embeddings else 0
                },
                "chunks": [
                    {
                        "id": chunk.id,
                        "content": chunk.content,
                        "chapter": chunk.chapter,
                        "start_page": getattr(chunk, 'start_page', None),
                        "end_page": getattr(chunk, 'end_page', None),
                        "metadata": getattr(chunk, 'metadata', {})
                    } for chunk in chunks
                ],
                "embeddings": embeddings
            }
            
            # Save to GCS as JSON
            json_content = json.dumps(cache_data, ensure_ascii=False, indent=2)
            
            success = self.bucket_manager.upload_text(
                json_content, 
                cache_key, 
                "application/json"
            )
            
            if success:
                logger.info(f"✅ Saved embeddings cache to gs://{self.bucket_name}/{cache_key}")
                logger.info(f"   📊 {len(chunks)} chunks, {len(embeddings)} embeddings")
                return True
            else:
                logger.error(f"❌ Failed to save embeddings cache to GCS")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error saving embeddings cache: {str(e)}")
            return False
    
    def load_embeddings(self, book_name: str, chapter: Optional[int], 
                       chunks: List[Any]) -> Optional[Tuple[List[Any], List[List[float]]]]:
        """
        Load embeddings from GCS cache if they match current chunks
        
        Args:
            book_name: Name of the book
            chapter: Chapter number (None for full book)
            chunks: Current chunks to validate against cache
            
        Returns:
            Tuple of (chunks, embeddings) if cache is valid, None otherwise
        """
        try:
            cache_key = self._get_cache_key(book_name, chapter)
            current_hash = self._generate_content_hash(chunks)
            
            # Try to download cache
            cache_content = self.bucket_manager.download_text(cache_key)
            if not cache_content:
                logger.info(f"📝 No embeddings cache found for {book_name} chapter {chapter}")
                return None
            
            # Parse cache data
            cache_data = json.loads(cache_content)
            cached_hash = cache_data["metadata"]["content_hash"]
            
            # Validate cache
            if cached_hash != current_hash:
                logger.info(f"🔄 Embeddings cache outdated for {book_name} chapter {chapter}")
                logger.info(f"   Current hash: {current_hash}")
                logger.info(f"   Cached hash:  {cached_hash}")
                return None
            
            # Cache is valid - reconstruct chunks and embeddings
            cached_chunks = []
            for chunk_data in cache_data["chunks"]:
                # Reconstruct chunk object (assuming SemanticChunk class)
                from semantic_chunker import SemanticChunk
                chunk = SemanticChunk(
                    id=chunk_data["id"],
                    content=chunk_data["content"],
                    chapter=chunk_data["chapter"],
                    start_page=chunk_data.get("start_page"),
                    end_page=chunk_data.get("end_page"),
                    metadata=chunk_data.get("metadata", {})
                )
                cached_chunks.append(chunk)
            
            embeddings = cache_data["embeddings"]
            
            logger.info(f"✅ Loaded embeddings from cache: gs://{self.bucket_name}/{cache_key}")
            logger.info(f"   📊 {len(cached_chunks)} chunks, {len(embeddings)} embeddings")
            logger.info(f"   📅 Created: {cache_data['metadata']['created_at']}")
            
            return cached_chunks, embeddings
            
        except Exception as e:
            logger.error(f"❌ Error loading embeddings cache: {str(e)}")
            return None
    
    def cache_exists(self, book_name: str, chapter: Optional[int] = None) -> bool:
        """Check if embeddings cache exists for given book/chapter"""
        try:
            cache_key = self._get_cache_key(book_name, chapter)
            return self.bucket_manager.file_exists(cache_key)
        except Exception:
            return False
    
    def delete_cache(self, book_name: str, chapter: Optional[int] = None) -> bool:
        """Delete embeddings cache"""
        try:
            cache_key = self._get_cache_key(book_name, chapter)
            success = self.bucket_manager.delete_file(cache_key)
            if success:
                logger.info(f"🗑️ Deleted embeddings cache: gs://{self.bucket_name}/{cache_key}")
            return success
        except Exception as e:
            logger.error(f"❌ Error deleting embeddings cache: {str(e)}")
            return False
    
    def list_cached_embeddings(self) -> List[Dict[str, Any]]:
        """List all cached embeddings"""
        try:
            files = self.bucket_manager.list_files_in_folder("embeddings/", ".json")
            cache_info = []
            
            for file_path in files:
                try:
                    content = self.bucket_manager.download_text(file_path.split(f"gs://{self.bucket_name}/")[-1])
                    if content:
                        data = json.loads(content)
                        cache_info.append({
                            "file_path": file_path,
                            "book_name": data["metadata"]["book_name"],
                            "chapter": data["metadata"]["chapter"],
                            "chunk_count": data["metadata"]["chunk_count"],
                            "created_at": data["metadata"]["created_at"]
                        })
                except Exception as e:
                    logger.warning(f"Could not parse cache file {file_path}: {str(e)}")
            
            return cache_info
            
        except Exception as e:
            logger.error(f"❌ Error listing cached embeddings: {str(e)}")
            return []
