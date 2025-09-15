#!/usr/bin/env python3
"""
PDF Processing CLI Application  
Command-line interface for PDF analysis and splitting
Replaces the Flask web server for Cloud Run Jobs
"""

import os
import sys
import json
import argparse
import tempfile
import logging
from typing import Dict, Any, Optional

# Import our modules
from analyze_pdf import PDFAnalyzer
from split_pdf import PDFSplitter

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gcp.bucket_manager import BucketManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize components
pdf_analyzer = PDFAnalyzer()
pdf_splitter = PDFSplitter()

# Get configuration from environment variables
PROJECT_ID = os.getenv('PROJECT_ID', 'book-qc-cf')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
REGION = os.getenv('REGION', 'us-central1')

# Initialize bucket manager
bucket_manager = BucketManager(PROJECT_ID, BUCKET_NAME)

def extract_filename_from_gcs_path(gcs_path) -> str:
    """Extract filename from GCS path"""
    # Handle case where gcs_path might be a dict or other type
    if not isinstance(gcs_path, str):
        logger.error(f"Expected string but got {type(gcs_path)}: {gcs_path}")
        raise ValueError(f"Expected string for GCS path, got {type(gcs_path)}")
    
    if gcs_path.startswith('gs://'):
        # Remove gs://bucket-name/ prefix
        parts = gcs_path.split('/', 3)
        if len(parts) >= 4:
            return parts[3]  # Return the filename part
    return gcs_path

def analyze_pdf_internal(pdf_gcs_path: str, bucket_name: str = None) -> Dict[str, Any]:
    """Analyze PDF without Flask request context"""
    try:
        if bucket_name is None:
            bucket_name = BUCKET_NAME
            
        # Handle nested pdf_path structure from workflow
        if isinstance(pdf_gcs_path, dict) and 'pdf_path' in pdf_gcs_path:
            pdf_gcs_path = pdf_gcs_path['pdf_path']
            logger.info(f"Extracted nested pdf_path: {pdf_gcs_path}")
        
        # Extract filename from GCS path
        pdf_filename = extract_filename_from_gcs_path(pdf_gcs_path)
        logger.info(f"Extracted filename: {pdf_filename} from {pdf_gcs_path}")
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                return {
                    'status': 'error',
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path,
                    'filename': pdf_filename
                }
            
            # Analyze PDF
            logger.info(f"Starting PDF analysis for: {pdf_filename}")
            analysis_result = pdf_analyzer.analyze_pdf(temp_pdf_path)
            
            if not analysis_result:
                return {
                    'status': 'error',
                    'error': 'PDF analysis failed',
                    'pdf_path': pdf_gcs_path
                }
            
            # Create folder structure based on PDF name
            pdf_name_without_ext = pdf_filename.replace('.pdf', '')
            analysis_filename = f"{pdf_name_without_ext}/analysis.json"
            
            if not bucket_manager.upload_json(analysis_result, analysis_filename):
                return {
                    'status': 'error',
                    'error': 'Failed to upload analysis to GCS',
                    'pdf_path': pdf_gcs_path
                }
            
            return {
                'status': 'success',
                'analysis_result': analysis_result,
                'analysis_gcs_path': f"gs://{bucket_name}/{analysis_filename}",
                'pdf_path': pdf_gcs_path,
                'pdf_folder': pdf_name_without_ext
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        logger.error(f"Error in analyze_pdf_internal: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_gcs_path
        }

def split_pdf_internal(pdf_gcs_path: str, analysis_gcs_path: str, bucket_name: str = None) -> Dict[str, Any]:
    """Split PDF without Flask request context"""
    try:
        if bucket_name is None:
            bucket_name = BUCKET_NAME
            
        # Handle nested pdf_path structure from workflow
        if isinstance(pdf_gcs_path, dict) and 'pdf_path' in pdf_gcs_path:
            pdf_gcs_path = pdf_gcs_path['pdf_path']
        
        if isinstance(analysis_gcs_path, dict) and 'analysis_path' in analysis_gcs_path:
            analysis_gcs_path = analysis_gcs_path['analysis_path']
        
        # Extract filenames from GCS paths
        pdf_filename = extract_filename_from_gcs_path(pdf_gcs_path)
        analysis_filename = extract_filename_from_gcs_path(analysis_gcs_path)
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        # Download analysis JSON from GCS
        analysis_data = bucket_manager.download_json(analysis_filename)
        if not analysis_data:
            return {
                'status': 'error',
                'error': 'Failed to download analysis from GCS',
                'analysis_path': analysis_gcs_path
            }
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                return {
                    'status': 'error',
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path
                }
            
            # Get PDF folder name (without extension)
            pdf_name_without_ext = extract_filename_from_gcs_path(pdf_gcs_path).replace('.pdf', '')
            
            # Split PDF
            logger.info(f"Starting PDF splitting for: {pdf_filename}")
            split_files = pdf_splitter.split_pdf_by_json(temp_pdf_path, analysis_data, "/tmp", bucket_manager, pdf_name_without_ext)
            
            if not split_files:
                return {
                    'status': 'error',
                    'error': 'PDF splitting failed',
                    'pdf_path': pdf_gcs_path
                }
            
            return {
                'status': 'success',
                'split_files': split_files,
                'total_files': len(split_files),
                'pdf_path': pdf_gcs_path
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        logger.error(f"Error in split_pdf_internal: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_gcs_path
        }

def process_pdf_complete(pdf_gcs_path: str, bucket_name: str = None) -> Dict[str, Any]:
    """Complete PDF processing (analyze + split)"""
    try:
        if bucket_name is None:
            bucket_name = BUCKET_NAME
            
        # Handle nested pdf_path structure from workflow
        if isinstance(pdf_gcs_path, dict) and 'pdf_path' in pdf_gcs_path:
            pdf_gcs_path = pdf_gcs_path['pdf_path']
        
        logger.info(f"Starting complete processing for: {pdf_gcs_path}")
        
        # Step 1: Analyze PDF
        analyze_result = analyze_pdf_internal(pdf_gcs_path, bucket_name)
        if analyze_result['status'] != 'success':
            return analyze_result
        
        # Step 2: Split PDF
        split_result = split_pdf_internal(
            pdf_gcs_path, 
            analyze_result['analysis_gcs_path'], 
            bucket_name
        )
        if split_result['status'] != 'success':
            return split_result
        
        # Combine results
        return {
            'status': 'success',
            'pdf_path': pdf_gcs_path,
            'analysis_result': analyze_result['analysis_result'],
            'analysis_gcs_path': analyze_result['analysis_gcs_path'],
            'split_files': split_result['split_files'],
            'total_files': split_result['total_files']
        }
        
    except Exception as e:
        logger.error(f"Error in process_pdf_complete: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_gcs_path
        }

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='PDF Processing CLI')
    parser.add_argument('operation', choices=[
        'analyze',
        'split', 
        'process'
    ], help='Operation to perform')
    
    # Common arguments
    parser.add_argument('--pdf-path', required=True, help='GCS path to PDF file')
    parser.add_argument('--analysis-path', help='GCS path to analysis JSON (required for split)')
    parser.add_argument('--bucket-name', default=BUCKET_NAME, help='Override bucket name')
    
    args = parser.parse_args()
    
    result = {}
    
    try:
        if args.operation == 'analyze':
            result = analyze_pdf_internal(args.pdf_path, args.bucket_name)
            
        elif args.operation == 'split':
            if not args.analysis_path:
                raise ValueError("--analysis-path is required for split operation")
            result = split_pdf_internal(args.pdf_path, args.analysis_path, args.bucket_name)
            
        elif args.operation == 'process':
            result = process_pdf_complete(args.pdf_path, args.bucket_name)
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        result = {
            'status': 'error',
            'error': str(e)
        }
    
    # Output result as JSON
    print(json.dumps(result, indent=2))
    
    # Set exit code based on status
    if result.get('status') != 'success':
        sys.exit(1)

if __name__ == '__main__':
    main()
