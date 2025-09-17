"""
PDF to Markdown Converter using Marker PDF
"""

import os
import tempfile
import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFToMarkdownConverter:
    """Converts PDF files to markdown using Marker PDF"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the converter with Marker PDF
        
        Args:
            api_key: Not used for Marker PDF (kept for compatibility)
        """
        self.api_key = api_key  # Not used but kept for compatibility
    
    def convert_pdf_to_markdown(self, pdf_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert PDF to markdown using Marker PDF
        
        Args:
            pdf_path: Path to the PDF file (local or GCS)
            output_path: Optional output path for markdown file
            
        Returns:
            Dict containing conversion result and metadata
        """
        try:
            # Download PDF from GCS if needed
            local_pdf_path = self._prepare_pdf(pdf_path)
            if not local_pdf_path:
                return {
                    "success": False,
                    "error": "Failed to prepare PDF file"
                }
            
            # Convert PDF to markdown using Marker PDF
            markdown_content = self._convert_with_marker(local_pdf_path)
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
                    "source_pdf": pdf_path,
                    "content_length": len(markdown_content["content"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error converting PDF to markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_pdf(self, pdf_path: str) -> Optional[str]:
        """Prepare PDF file for processing (download from GCS if needed)"""
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
                    return temp_file.name
            else:
                # Local file path
                return pdf_path
                
        except Exception as e:
            logger.error(f"Error preparing PDF: {str(e)}")
            return None
    
    def _convert_with_marker(self, pdf_path: str) -> Dict[str, Any]:
        """Convert PDF to markdown using Marker PDF"""
        try:
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run Marker PDF conversion
                cmd = [
                    "python", "-m", "marker.scripts.convert_single",
                    pdf_path,
                    "--output_dir", temp_dir
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Marker conversion failed: {result.stderr}"
                    }
                
                # Find the generated markdown file
                output_files = list(Path(temp_dir).glob("*.md"))
                if not output_files:
                    return {
                        "success": False,
                        "error": "No markdown file generated"
                    }
                
                # Read the markdown content
                with open(output_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "content": content
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Marker conversion timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }