#!/usr/bin/env python3
"""
Debug script to test bucket access and path resolution
"""

import os
import sys
import tempfile
import logging

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.gcp.bucket_manager import BucketManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_filename_from_gcs_path(gcs_path: str) -> str:
    """Extract filename from GCS path"""
    if gcs_path.startswith('gs://'):
        # Remove gs://bucket-name/ prefix to get the relative path
        parts = gcs_path.split('/', 3)
        if len(parts) >= 4:
            return parts[3]  # Return the relative path (e.g., question_papers/SQP-2.pdf)
        return gcs_path.split('/')[-1]  # Fallback to just filename
    return gcs_path

def test_bucket_access():
    """Test bucket access and file download"""
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'book-qc-cf')
    BUCKET_NAME = os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
    
    print(f"Testing bucket access:")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Bucket Name: {BUCKET_NAME}")
    
    try:
        # Initialize bucket manager
        bucket_manager = BucketManager(PROJECT_ID, BUCKET_NAME)
        print("✅ Bucket manager initialized successfully")
        
        # Test file path
        test_gcs_path = "gs://book-qc-cf-pdf-storage/book_ip_sqp/answer_keys/SQP-5-SOLUTION.pdf"
        print(f"Test GCS path: {test_gcs_path}")
        
        # Extract filename
        pdf_filename = extract_filename_from_gcs_path(test_gcs_path)
        print(f"Extracted filename: {pdf_filename}")
        
        # Check if file exists
        print(f"Checking if file exists...")
        exists = bucket_manager.file_exists(pdf_filename)
        print(f"File exists: {exists}")
        
        if exists:
            # Try to download
            print(f"Attempting to download file...")
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf_path = temp_pdf.name
            
            try:
                success = bucket_manager.download_file(pdf_filename, temp_pdf_path)
                print(f"Download successful: {success}")
                if success:
                    print(f"File downloaded to: {temp_pdf_path}")
                    print(f"File size: {os.path.getsize(temp_pdf_path)} bytes")
                else:
                    print("❌ Download failed")
            except Exception as e:
                print(f"❌ Download error: {str(e)}")
            finally:
                # Clean up
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
        else:
            print("❌ File does not exist in bucket")
            
        # Test listing files in the folder
        print(f"\nTesting folder listing...")
        folder_files = bucket_manager.list_files_in_folder("book_ip_sqp/answer_keys", ".pdf")
        print(f"Found {len(folder_files)} PDF files in folder:")
        for file in folder_files:
            print(f"  - {file}")
            
    except Exception as e:
        print(f"❌ Error initializing bucket manager: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bucket_access()
