"""
RAG Ingestion Microservice
Cloud Run service for PDF to markdown conversion with vector storage
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

# Import our modules
from cli_main import process_pdf_to_vector, search_vectors, list_collections

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

# Get configuration from environment variables
PROJECT_ID = os.getenv('PROJECT_ID', 'book-qc-cf')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'llm-books')
REGION = os.getenv('REGION', 'us-central1')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'rag-ingestion',
        'version': '1.0.0'
    })

@app.route('/process', methods=['POST'])
def process_pdf():
    """
    Process PDF to markdown with vector storage
    Expects JSON with:
    - pdf_path: Path to PDF file
    - book_name: Name of the book
    - chapter: (optional) Chapter number
    - update_existing: (optional) Whether to update existing collection
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_path = data.get('pdf_path')
        book_name = data.get('book_name')
        chapter = data.get('chapter')
        update_existing = data.get('update_existing', True)
        
        if not pdf_path or not book_name:
            raise BadRequest("pdf_path and book_name are required")
        
        logger.info(f"Processing PDF: {pdf_path} for book: {book_name}")
        
        # Process PDF to vector
        result = process_pdf_to_vector(pdf_path, book_name, chapter, update_existing)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in process_pdf: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/search', methods=['POST'])
def search():
    """
    Search for similar content in vector database
    Expects JSON with:
    - query: Search query
    - book_name: Name of the book
    - chapter: (optional) Chapter number
    - limit: (optional) Maximum number of results
    - score_threshold: (optional) Minimum similarity score
    """
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        query = data.get('query')
        book_name = data.get('book_name')
        chapter = data.get('chapter')
        limit = data.get('limit', 10)
        score_threshold = data.get('score_threshold', 0.7)
        
        if not query or not book_name:
            raise BadRequest("query and book_name are required")
        
        logger.info(f"Searching for: {query} in book: {book_name}")
        
        # Search vectors
        result = search_vectors(book_name, query, chapter, limit, score_threshold)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/collections', methods=['GET'])
def get_collections():
    """Get list of all collections"""
    try:
        result = list_collections()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in get_collections: {str(e)}")
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
