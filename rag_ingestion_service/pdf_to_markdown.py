"""
PDF to Markdown Converter using Marker PDF
"""

import os
import tempfile
import logging
import subprocess
import requests
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFToMarkdownConverter:
    """Converts PDF files to markdown using Marker PDF"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the converter with Marker PDF
        
        Args:
            api_key: Marker PDF API key for cloud conversion
        """
        self.api_key = api_key
        self.use_api = bool(api_key)  # Use API if key provided, otherwise local
    
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
            if self.use_api:
                logger.info(f"Using Marker PDF API for conversion")
                markdown_content = self._convert_with_marker_api(local_pdf_path)
            else:
                logger.info(f"Using local Marker PDF for conversion")
                markdown_content = self._convert_with_marker_local(local_pdf_path)
                
            if not markdown_content["success"]:
                logger.error(f"Conversion failed: {markdown_content['error']}")
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
    
    def _convert_with_marker_api(self, pdf_path: str) -> Dict[str, Any]:
        """Convert PDF to markdown using Datalab Marker API"""
        import time
        
        try:
            logger.info(f"Converting PDF with Datalab Marker API: {pdf_path}")
            
            # Marker API endpoint
            api_url = "https://www.datalab.to/api/v1/marker"
            
            # Prepare form data for multipart/form-data request
            form_data = {
                'file': (os.path.basename(pdf_path), open(pdf_path, 'rb'), 'application/pdf'),
                'output_format': (None, 'markdown'),
                'force_ocr': (None, False),
                'paginate': (None, False),
                'use_llm': (None, False),
                'strip_existing_ocr': (None, False),
                'disable_image_extraction': (None, False)
            }
            
            headers = {"X-Api-Key": self.api_key}
            
            # Submit PDF for processing
            logger.info("Submitting PDF to Marker API...")
            response = requests.post(api_url, files=form_data, headers=headers)
            
            if response.status_code != 200:
                error_msg = f"API submission failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            data = response.json()
            if not data.get('success'):
                return {
                    "success": False,
                    "error": data.get('error', 'Unknown API error')
                }
            
            # Get the polling URL
            check_url = data.get('request_check_url')
            request_id = data.get('request_id')
            
            if not check_url:
                return {
                    "success": False,
                    "error": "No request_check_url received from API"
                }
            
            logger.info(f"PDF submitted successfully. Request ID: {request_id}")
            logger.info("Polling for completion...")
            
            # Poll for completion (max 10 minutes)
            max_polls = 300  # 300 * 2 seconds = 10 minutes
            
            for i in range(max_polls):
                time.sleep(2)  # Wait 2 seconds between polls
                
                try:
                    poll_response = requests.get(check_url, headers=headers)
                    
                    if poll_response.status_code != 200:
                        logger.warning(f"Poll request failed with status {poll_response.status_code}")
                        continue
                    
                    poll_data = poll_response.json()
                    status = poll_data.get('status')
                    
                    logger.info(f"Poll {i+1}/{max_polls}: Status = {status}")
                    
                    if status == 'complete':
                        if poll_data.get('success'):
                            markdown_content = poll_data.get('markdown', '')
                            if markdown_content:
                                logger.info(f"Successfully converted PDF. Markdown length: {len(markdown_content)} characters")
                                return {
                                    "success": True,
                                    "content": markdown_content
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": "No markdown content in response"
                                }
                        else:
                            error_msg = poll_data.get('error', 'Conversion failed')
                            logger.error(f"Conversion failed: {error_msg}")
                            return {
                                "success": False,
                                "error": error_msg
                            }
                    elif status == 'processing':
                        # Continue polling
                        continue
                    else:
                        logger.warning(f"Unknown status: {status}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Poll request failed: {str(e)}")
                    continue
            
            # Timeout reached
            return {
                "success": False,
                "error": f"Conversion timed out after {max_polls * 2} seconds"
            }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Marker API request failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in Marker API conversion: {str(e)}")
            return {
                "success": False,
                "error": f"Conversion error: {str(e)}"
            }
        finally:
            # Close the file if it was opened
            try:
                if 'form_data' in locals() and form_data.get('file'):
                    form_data['file'][1].close()
            except:
                pass

    def _convert_with_marker_local(self, pdf_path: str) -> Dict[str, Any]:
        """Convert PDF to markdown using local Marker PDF installation (fallback)"""
        try:
            logger.info(f"Converting PDF with local Marker: {pdf_path}")
            
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