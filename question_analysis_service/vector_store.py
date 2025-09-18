"""
Vector Store using Qdrant
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages vector storage using Qdrant"""
    
    def __init__(self, api_key: str, url: str = None):
        """
        Initialize the vector store
        
        Args:
            api_key: Qdrant API key
            url: Qdrant cluster URL (if None, will try to extract from API key)
        """
        self.api_key = api_key
        
        # If no URL provided, try to use Qdrant Cloud with API key
        if not url:
            # For Qdrant Cloud, extract cluster URL from API key or use default cloud URL
            url = "https://9becb4cf-82b6-456f-ae0c-d797c6c946cc.us-east4-0.gcp.cloud.qdrant.io"
            logger.info(f"Using Qdrant Cloud URL: {url}")
        
        self.url = url
        
        try:
            self.client = QdrantClient(
                url=url,
                api_key=api_key,
                timeout=30  # 30 second timeout
            )
            logger.info(f"Connected to Qdrant at {url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant at {url}: {str(e)}")
            raise
        
        self.embedding_dimension = 768  # text-embedding-004 dimension
        
        # Test connection
        self._test_connection()
    
    def create_collection(self, collection_name: str, book_name: str) -> bool:
        """
        Create a new collection for a book
        
        Args:
            collection_name: Name of the collection
            book_name: Name of the book
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if collection already exists
            collections = self.client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if collection_name in existing_collections:
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Create collection with basic configuration
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Created collection {collection_name} for book {book_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {str(e)}")
            return False
    
    def _test_connection(self) -> bool:
        """Test connection to Qdrant"""
        try:
            # Try to get cluster info
            info = self.client.get_collections()
            logger.info(f"Successfully connected to Qdrant. Found {len(info.collections)} existing collections.")
            return True
        except Exception as e:
            logger.error(f"Qdrant connection test failed: {str(e)}")
            return False
    
    def upsert_chunks(self, collection_name: str, chunks: List[Any], embeddings: List[List[float]]) -> bool:
        """
        Upsert chunks and their embeddings to the collection
        
        Args:
            collection_name: Name of the collection
            chunks: List of Chunk objects
            embeddings: List of embedding vectors
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(chunks) != len(embeddings):
                logger.error("Number of chunks and embeddings must match")
                return False
            
            # Prepare points for upsert
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                
                # Prepare payload with chunk metadata
                payload = {
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                    **chunk.metadata
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} chunks to collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting chunks to {collection_name}: {str(e)}")
            return False
    
    def search_similar(self, collection_name: str, query_embedding: List[float], 
                      limit: int = 10, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar chunks
        
        Args:
            collection_name: Name of the collection
            query_embedding: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {str(e)}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information or None if not found
        """
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {str(e)}")
            return None
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all collections
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
