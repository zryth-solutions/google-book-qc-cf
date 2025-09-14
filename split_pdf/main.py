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
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_gcs_path, temp_pdf_path):
                return jsonify({
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            # Analyze PDF
            logger.info(f"Analyzing PDF: {pdf_gcs_path}")
            analysis_result = pdf_analyzer.analyze_pdf(temp_pdf_path)
            
            # Upload analysis result to GCS
            analysis_gcs_path = f"{pdf_gcs_path}_analysis.json"
            if not bucket_manager.upload_json(analysis_result, analysis_gcs_path):
                return jsonify({
                    'error': 'Failed to upload analysis result to GCS',
                    'analysis_path': analysis_gcs_path
                }), 500
            
            logger.info(f"Analysis completed and uploaded to: {analysis_gcs_path}")
            
            return jsonify({
                'status': 'success',
                'analysis_result': analysis_result,
                'analysis_gcs_path': analysis_gcs_path,
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
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/split', methods=['POST'])
def split_pdf():
    """
    Split PDF endpoint
    Expects JSON with:
    - pdf_path: GCS path to PDF file
    - analysis_path: GCS path to analysis JSON file
    - bucket_name: (optional) Override bucket name
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_gcs_path = data.get('pdf_path')
        analysis_gcs_path = data.get('analysis_path')
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        if not pdf_gcs_path:
            raise BadRequest("pdf_path is required")
        if not analysis_gcs_path:
            raise BadRequest("analysis_path is required")
        
        # Download PDF and analysis from GCS
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_json:
            temp_json_path = temp_json.name
        
        try:
            # Download files from bucket
            if not bucket_manager.download_file(pdf_gcs_path, temp_pdf_path):
                return jsonify({
                    'error': 'Failed to download PDF from GCS',
                    'pdf_path': pdf_gcs_path
                }), 400
            
            analysis_data = bucket_manager.download_json(analysis_gcs_path)
            if not analysis_data:
                return jsonify({
                    'error': 'Failed to download analysis data from GCS',
                    'analysis_path': analysis_gcs_path
                }), 400
            
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_output_dir:
                # Split PDF
                logger.info(f"Splitting PDF: {pdf_gcs_path}")
                split_files = pdf_splitter.split_pdf_by_json(
                    temp_pdf_path, analysis_data, temp_output_dir
                )
                
                # Upload split files to GCS
                uploaded_files = []
                for file_info in split_files:
                    # Determine GCS path for the split file
                    split_gcs_path = f"{pdf_gcs_path}_split/{file_info['folder']}/{file_info['filename']}"
                    
                    # Upload to GCS
                    if bucket_manager.upload_file(file_info['path'], split_gcs_path):
                        uploaded_files.append({
                            'filename': file_info['filename'],
                            'folder': file_info['folder'],
                            'gcs_path': split_gcs_path,
                            'pages': file_info['pages'],
                            'page_count': file_info['page_count'],
                            'chapter_name': file_info['chapter_name']
                        })
                        logger.info(f"Uploaded split file: {split_gcs_path}")
                    else:
                        logger.error(f"Failed to upload split file: {file_info['filename']}")
                
                logger.info(f"Split completed: {len(uploaded_files)} files uploaded")
                
                return jsonify({
                    'status': 'success',
                    'split_files': uploaded_files,
                    'total_files': len(uploaded_files),
                    'pdf_path': pdf_gcs_path,
                    'analysis_path': analysis_gcs_path
                })
        
        finally:
            # Clean up temporary files
            for temp_file in [temp_pdf_path, temp_json_path]:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in split_pdf: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        if not pdf_gcs_path:
            raise BadRequest("pdf_path is required")
        
        # Step 1: Analyze PDF
        logger.info(f"Starting complete processing for: {pdf_gcs_path}")
        
        analyze_data = {
            'pdf_path': pdf_gcs_path,
            'bucket_name': bucket_name
        }
        
        # Call analyze endpoint internally
        analyze_response = analyze_pdf()
        if analyze_response[1] != 200:  # Check status code
            return analyze_response
        
        analyze_result = analyze_response[0].get_json()
        analysis_gcs_path = analyze_result['analysis_gcs_path']
        
        # Step 2: Split PDF
        split_data = {
            'pdf_path': pdf_gcs_path,
            'analysis_path': analysis_gcs_path,
            'bucket_name': bucket_name
        }
        
        # Call split endpoint internally
        split_response = split_pdf()
        if split_response[1] != 200:  # Check status code
            return split_response
        
        split_result = split_response[0].get_json()
        
        logger.info(f"Complete processing finished for: {pdf_gcs_path}")
        
        return jsonify({
            'status': 'success',
            'pdf_path': pdf_gcs_path,
            'analysis_result': analyze_result['analysis_result'],
            'analysis_gcs_path': analysis_gcs_path,
            'split_files': split_result['split_files'],
            'total_files': split_result['total_files']
        })
    
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in process_pdf: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Get port from environment variable (Cloud Run requirement)
    port = int(os.getenv('PORT', 8080))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
