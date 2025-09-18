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
    
    def list_files_in_folder(self, folder_path: str, file_extension: str = None, return_full_paths: bool = True) -> List[str]:
        """
        List all files in a GCS folder
        
        Args:
            folder_path: Path to the folder in GCS bucket (without leading slash)
            file_extension: Optional file extension filter (e.g., '.pdf', '.md')
            return_full_paths: If True, return full GCS paths (gs://bucket/path). If False, return relative paths.
            
        Returns:
            List[str]: List of file paths in the folder
        """
        try:
            # Ensure folder_path doesn't start with slash
            if folder_path.startswith('/'):
                folder_path = folder_path[1:]
            
            # Add trailing slash if not present
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            blobs = self.bucket.list_blobs(prefix=folder_path)
            files = []
            
            for blob in blobs:
                # Skip if it's a directory (ends with /)
                if blob.name.endswith('/'):
                    continue
                
                # Apply file extension filter if provided
                if file_extension and not blob.name.lower().endswith(file_extension.lower()):
                    continue
                
                # Return full GCS path or relative path based on parameter
                if return_full_paths:
                    files.append(f"gs://{self.bucket_name}/{blob.name}")
                else:
                    files.append(blob.name)
            
            logger.info(f"Found {len(files)} files in folder gs://{self.bucket_name}/{folder_path}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files in folder {folder_path}: {str(e)}")
            return []
    
    def upload_text(self, content: str, gcs_path: str, content_type: str = "text/plain") -> bool:
        """
        Upload text content to GCS bucket
        
        Args:
            content: Text content to upload
            gcs_path: Destination path in GCS bucket
            content_type: MIME type of the content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(content, content_type=content_type)
            logger.info(f"Uploaded text content to gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload text content to {gcs_path}: {str(e)}")
            return False
    
    def download_text(self, gcs_path: str) -> Optional[str]:
        """
        Download text content from GCS bucket
        
        Args:
            gcs_path: Source path in GCS bucket
            
        Returns:
            str: Text content or None if failed
        """
        try:
            blob = self.bucket.blob(gcs_path)
            content = blob.download_as_text()
            logger.info(f"Downloaded text content from gs://{self.bucket_name}/{gcs_path}")
            return content
        except NotFound:
            logger.error(f"Text file not found: gs://{self.bucket_name}/{gcs_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to download text content from {gcs_path}: {str(e)}")
            return None
    
    
    def get_folder_structure(self, folder_path: str) -> Dict[str, Any]:
        """
        Get the folder structure with file information
        
        Args:
            folder_path: Path to the folder in GCS bucket
            
        Returns:
            Dict containing folder structure and file metadata
        """
        try:
            # Ensure folder_path doesn't start with slash
            if folder_path.startswith('/'):
                folder_path = folder_path[1:]
            
            # Add trailing slash if not present
            if not folder_path.endswith('/'):
                folder_path += '/'
            
            blobs = self.bucket.list_blobs(prefix=folder_path)
            structure = {
                'folder_path': f"gs://{self.bucket_name}/{folder_path}",
                'files': [],
                'subfolders': set()
            }
            
            for blob in blobs:
                # Get relative path from folder
                relative_path = blob.name[len(folder_path):]
                
                if relative_path.endswith('/'):
                    # It's a subfolder
                    subfolder = relative_path.rstrip('/')
                    if subfolder:
                        structure['subfolders'].add(subfolder)
                else:
                    # It's a file
                    file_info = {
                        'name': relative_path,
                        'full_path': f"gs://{self.bucket_name}/{blob.name}",
                        'size': blob.size,
                        'created': blob.time_created.isoformat() if blob.time_created else None,
                        'updated': blob.updated.isoformat() if blob.updated else None,
                        'content_type': blob.content_type
                    }
                    structure['files'].append(file_info)
            
            # Convert set to list for JSON serialization
            structure['subfolders'] = list(structure['subfolders'])
            
            logger.info(f"Retrieved folder structure for gs://{self.bucket_name}/{folder_path}")
            return structure
            
        except Exception as e:
            logger.error(f"Failed to get folder structure for {folder_path}: {str(e)}")
            return {'folder_path': f"gs://{self.bucket_name}/{folder_path}", 'files': [], 'subfolders': []}