"""
PDF to Markdown Converter using Marker API
"""

import os
import requests
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFToMarkdownConverter:
    """Converts PDF files to markdown using Marker API"""
    
    def __init__(self, api_key: str):
        """
        Initialize the converter with Marker API key
        
        Args:
            api_key: Marker API key
        """
        self.api_key = api_key
        self.base_url = "https://api.marker.io/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def convert_pdf_to_markdown(self, pdf_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert PDF to markdown using Marker API
        
        Args:
            pdf_path: Path to the PDF file (local or GCS)
            output_path: Optional output path for markdown file
            
        Returns:
            Dict containing conversion result and metadata
        """
        try:
            # Upload PDF to Marker API
            upload_result = self._upload_pdf(pdf_path)
            if not upload_result["success"]:
                return {
                    "success": False,
                    "error": upload_result["error"]
                }
            
            # Convert PDF to markdown
            conversion_result = self._convert_to_markdown(upload_result["file_id"])
            if not conversion_result["success"]:
                return {
                    "success": False,
                    "error": conversion_result["error"]
                }
            
            # Download markdown content
            markdown_content = self._download_markdown(conversion_result["markdown_id"])
            if not markdown_content["success"]:
                return {
                    "success": False,
                    "error": markdown_content["error"]
                }
            
            # Save to output path if provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content["content"])
                logger.info(f"Markdown saved to {output_path}")
            
            return {
                "success": True,
                "markdown_content": markdown_content["content"],
                "metadata": {
                    "file_id": upload_result["file_id"],
                    "markdown_id": conversion_result["markdown_id"],
                    "content_length": len(markdown_content["content"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error converting PDF to markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _upload_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Upload PDF file to Marker API"""
        try:
            # Check if it's a GCS path
            if pdf_path.startswith('gs://'):
                # Download from GCS first
                from google.cloud import storage
                client = storage.Client()
                bucket_name = pdf_path.split('/')[2]
                blob_name = '/'.join(pdf_path.split('/')[3:])
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    blob.download_to_filename(temp_file.name)
                    pdf_path = temp_file.name
            
            # Upload to Marker API
            with open(pdf_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/upload",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "file_id": result["file_id"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Upload failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Upload error: {str(e)}"
            }
    
    def _convert_to_markdown(self, file_id: str) -> Dict[str, Any]:
        """Convert uploaded PDF to markdown"""
        try:
            response = requests.post(
                f"{self.base_url}/convert",
                headers=self.headers,
                json={
                    "file_id": file_id,
                    "output_format": "markdown",
                    "include_images": True,
                    "image_descriptions": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "markdown_id": result["markdown_id"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Conversion failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Conversion error: {str(e)}"
            }
    
    def _download_markdown(self, markdown_id: str) -> Dict[str, Any]:
        """Download converted markdown content"""
        try:
            response = requests.get(
                f"{self.base_url}/download/{markdown_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "content": response.text
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Download error: {str(e)}"
            }
