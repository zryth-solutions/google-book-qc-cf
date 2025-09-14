"""
GCP Cloud Storage Bucket Manager
Handles all bucket operations for PDF processing pipeline
"""

import os
import json
from typing import Optional, List, Dict, Any
from google.cloud import storage
from google.cloud.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)

class BucketManager:
    """Manages GCP Cloud Storage bucket operations"""
    
    def __init__(self, project_id: str, bucket_name: str):
        """
        Initialize bucket manager
        
        Args:
            project_id: GCP project ID
            bucket_name: Name of the GCS bucket
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
    
    def upload_file(self, local_file_path: str, gcs_path: str) -> bool:
        """
        Upload a file to GCS bucket
        
        Args:
            local_file_path: Path to local file
            gcs_path: Destination path in GCS bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_file_path)
            logger.info(f"Uploaded {local_file_path} to gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {local_file_path}: {str(e)}")
            return False
    
    def download_file(self, gcs_path: str, local_file_path: str) -> bool:
        """
        Download a file from GCS bucket
        
        Args:
            gcs_path: Source path in GCS bucket
            local_file_path: Destination path for local file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.download_to_filename(local_file_path)
            logger.info(f"Downloaded gs://{self.bucket_name}/{gcs_path} to {local_file_path}")
            return True
        except NotFound:
            logger.error(f"File not found: gs://{self.bucket_name}/{gcs_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to download {gcs_path}: {str(e)}")
            return False
    
    def upload_json(self, data: Dict[Any, Any], gcs_path: str) -> bool:
        """
        Upload JSON data to GCS bucket
        
        Args:
            data: Dictionary to upload as JSON
            gcs_path: Destination path in GCS bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            logger.info(f"Uploaded JSON to gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload JSON to {gcs_path}: {str(e)}")
            return False
    
    def download_json(self, gcs_path: str) -> Optional[Dict[Any, Any]]:
        """
        Download and parse JSON from GCS bucket
        
        Args:
            gcs_path: Source path in GCS bucket
            
        Returns:
            Dict or None if failed
        """
        try:
            blob = self.bucket.blob(gcs_path)
            json_str = blob.download_as_text()
            data = json.loads(json_str)
            logger.info(f"Downloaded JSON from gs://{self.bucket_name}/{gcs_path}")
            return data
        except NotFound:
            logger.error(f"JSON file not found: gs://{self.bucket_name}/{gcs_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to download JSON from {gcs_path}: {str(e)}")
            return None
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in bucket with optional prefix
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file paths
        """
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {str(e)}")
            return []
    
    def file_exists(self, gcs_path: str) -> bool:
        """
        Check if file exists in bucket
        
        Args:
            gcs_path: Path in GCS bucket
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Failed to check if file exists {gcs_path}: {str(e)}")
            return False
    
    def delete_file(self, gcs_path: str) -> bool:
        """
        Delete file from bucket
        
        Args:
            gcs_path: Path in GCS bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.delete()
            logger.info(f"Deleted gs://{self.bucket_name}/{gcs_path}")
            return True
        except NotFound:
            logger.warning(f"File not found for deletion: gs://{self.bucket_name}/{gcs_path}")
            return True  # Consider it successful if already deleted
        except Exception as e:
            logger.error(f"Failed to delete {gcs_path}: {str(e)}")
            return False
    
    def get_public_url(self, gcs_path: str) -> str:
        """
        Get public URL for a file in the bucket
        
        Args:
            gcs_path: Path in GCS bucket
            
        Returns:
            str: Public URL
        """
        return f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
