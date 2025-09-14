"""
PDF Processing Microservice
Cloud Run service for PDF analysis and splitting
"""

import os
import json
import tempfile
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

# Import our modules
from analyze_pdf import PDFAnalyzer
from split_pdf import PDFSplitter

# Add parent directory to path for utils import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gcp.bucket_manager import BucketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize components
pdf_analyzer = PDFAnalyzer()
pdf_splitter = PDFSplitter()

# Get configuration from environment variables
PROJECT_ID = os.getenv('PROJECT_ID', 'your-project-id')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'your-bucket-name')
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'pdf-processor',
        'version': '1.0.0'
    })

@app.route('/analyze', methods=['POST'])
def analyze_pdf():
    """
    Analyze PDF endpoint
    Expects JSON with:
    - pdf_path: GCS path to PDF file
    - bucket_name: (optional) Override bucket name
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_gcs_path = data.get('pdf_path')
        if not pdf_gcs_path:
            raise BadRequest("pdf_path is required")
        
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        # Debug logging
        logger.info(f"Received data: {data}")
        logger.info(f"pdf_gcs_path type: {type(pdf_gcs_path)}, value: {pdf_gcs_path}")
        
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
                return jsonify({
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path,
                    'filename': pdf_filename
                }), 400
            
            # Analyze PDF
            logger.info(f"Starting PDF analysis for: {pdf_filename}")
            analysis_result = pdf_analyzer.analyze_pdf(temp_pdf_path)
            
            if not analysis_result:
                return jsonify({
                    'error': 'PDF analysis failed',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            # Upload analysis result to GCS
            analysis_filename = f"analysis/{pdf_filename.replace('.pdf', '_analysis.json')}"
            if not bucket_manager.upload_json(analysis_result, analysis_filename):
                return jsonify({
                    'error': 'Failed to upload analysis to GCS',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            return jsonify({
                'status': 'success',
                'analysis_result': analysis_result,
                'analysis_gcs_path': f"gs://{bucket_name}/{analysis_filename}",
                'pdf_path': pdf_gcs_path
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in analyze_pdf: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/split', methods=['POST'])
def split_pdf():
    """
    Split PDF endpoint
    Expects JSON with:
    - pdf_path: GCS path to PDF file
    - analysis_path: GCS path to analysis JSON
    - bucket_name: (optional) Override bucket name
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_gcs_path = data.get('pdf_path')
        analysis_gcs_path = data.get('analysis_path')
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        if not pdf_gcs_path or not analysis_gcs_path:
            raise BadRequest("pdf_path and analysis_path are required")
        
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
            return jsonify({
                'error': 'Failed to download analysis from GCS',
                'analysis_path': analysis_gcs_path
            }), 400
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                return jsonify({
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            # Split PDF
            logger.info(f"Starting PDF splitting for: {pdf_filename}")
            split_files = pdf_splitter.split_pdf_by_json(temp_pdf_path, analysis_data, bucket_name)
            
            if not split_files:
                return jsonify({
                    'error': 'PDF splitting failed',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            return jsonify({
                'status': 'success',
                'split_files': split_files,
                'total_files': len(split_files),
                'pdf_path': pdf_gcs_path
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in split_pdf: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def _analyze_pdf_internal(pdf_gcs_path: str, bucket_name: str) -> tuple:
    """Internal function to analyze PDF without Flask request context"""
    try:
        # Extract filename from GCS path
        pdf_filename = extract_filename_from_gcs_path(pdf_gcs_path)
        logger.info(f"Extracted filename: {pdf_filename} from {pdf_gcs_path}")
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                return jsonify({
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path,
                    'filename': pdf_filename
                }), 400
            
            # Analyze PDF
            logger.info(f"Starting PDF analysis for: {pdf_filename}")
            analysis_result = pdf_analyzer.analyze_pdf(temp_pdf_path)
            
            if not analysis_result:
                return jsonify({
                    'error': 'PDF analysis failed',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            # Upload analysis result to GCS
            analysis_filename = f"analysis/{pdf_filename.replace('.pdf', '_analysis.json')}"
            if not bucket_manager.upload_json(analysis_result, analysis_filename):
                return jsonify({
                    'error': 'Failed to upload analysis to GCS',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            return jsonify({
                'status': 'success',
                'analysis_result': analysis_result,
                'analysis_gcs_path': f"gs://{bucket_name}/{analysis_filename}",
                'pdf_path': pdf_gcs_path
            }), 200
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        logger.error(f"Error in _analyze_pdf_internal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def _split_pdf_internal(pdf_gcs_path: str, analysis_gcs_path: str, bucket_name: str) -> tuple:
    """Internal function to split PDF without Flask request context"""
    try:
        # Extract filenames from GCS paths
        pdf_filename = extract_filename_from_gcs_path(pdf_gcs_path)
        analysis_filename = extract_filename_from_gcs_path(analysis_gcs_path)
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        # Download analysis JSON from GCS
        analysis_data = bucket_manager.download_json(analysis_filename)
        if not analysis_data:
            return jsonify({
                'error': 'Failed to download analysis from GCS',
                'analysis_path': analysis_gcs_path
            }), 400
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                return jsonify({
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            # Split PDF
            logger.info(f"Starting PDF splitting for: {pdf_filename}")
            split_files = pdf_splitter.split_pdf_by_json(temp_pdf_path, analysis_data, bucket_name)
            
            if not split_files:
                return jsonify({
                    'error': 'PDF splitting failed',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            return jsonify({
                'status': 'success',
                'split_files': split_files,
                'total_files': len(split_files),
                'pdf_path': pdf_gcs_path
            }), 200
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        logger.error(f"Error in _split_pdf_internal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/process', methods=['POST'])
def process_pdf():
    """
    Complete PDF processing endpoint (analyze + split)
    Expects JSON with:
    - pdf_path: GCS path to PDF file
    - bucket_name: (optional) Override bucket name
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_gcs_path = data.get('pdf_path')
        if not pdf_gcs_path:
            raise BadRequest("pdf_path is required")
        
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        # Handle nested pdf_path structure from workflow
        if isinstance(pdf_gcs_path, dict) and 'pdf_path' in pdf_gcs_path:
            pdf_gcs_path = pdf_gcs_path['pdf_path']
        
        logger.info(f"Starting complete processing for: {pdf_gcs_path}")
        
        # Step 1: Analyze PDF
        analyze_response, analyze_status = _analyze_pdf_internal(pdf_gcs_path, bucket_name)
        if analyze_status != 200:
            return analyze_response
        
        analyze_result = analyze_response.get_json()
        
        # Step 2: Split PDF
        split_response, split_status = _split_pdf_internal(
            pdf_gcs_path, 
            analyze_result['analysis_gcs_path'], 
            bucket_name
        )
        if split_status != 200:
            return split_response
        
        split_result = split_response.get_json()
        
        # Combine results
        return jsonify({
            'status': 'success',
            'pdf_path': pdf_gcs_path,
            'analysis_result': analyze_result['analysis_result'],
            'analysis_gcs_path': analyze_result['analysis_gcs_path'],
            'split_files': split_result['split_files'],
            'total_files': split_result['total_files']
        })
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in process_pdf: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Get port from environment variable (Cloud Run requirement)
    port = int(os.getenv('PORT', 8080))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)