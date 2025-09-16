"""
Embedding Generator using Google Vertex AI
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from google.cloud import aiplatform
from vertexai.preview.language_models import TextEmbeddingModel

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings using Google Vertex AI"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize the embedding generator
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location
        """
        self.project_id = project_id
        self.location = location
        self.model_name = "textembedding-gecko@001"
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        self.model = TextEmbeddingModel.from_pretrained(self.model_name)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
            
            # Generate embeddings in batches to avoid rate limits
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self._generate_batch_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []
    
    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            embeddings = self.model.get_embeddings(texts)
            return [embedding.values for embedding in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return []
    
    def generate_single_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            embeddings = self.generate_embeddings([text])
            return embeddings[0] if embeddings else None
        except Exception as e:
            logger.error(f"Error generating single embedding: {str(e)}")
            return None
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        # textembedding-gecko@001 has 768 dimensions
        return 768
