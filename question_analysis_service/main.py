"""
Question Analysis Service Main Entry Point
Cloud Run service for analyzing CBSE question papers
"""

import os
import json
import logging
from typing import Dict, Any
from flask import Flask, request, jsonify
from datetime import datetime

from .batch_processor import BatchQuestionProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global processor instance
processor = None

def initialize_processor():
    """Initialize the batch processor with environment variables"""
    global processor
    
    if processor is None:
        try:
            # Get configuration from environment variables
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'book-qc-cf')
            qdrant_api_key = os.getenv('QDRANT_API_KEY')
            qdrant_url = os.getenv('QDRANT_URL')
            bucket_name = os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
            location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
            
            # For now, use placeholder values if API keys are not provided
            # In production, these should be set via environment variables or secrets
            if not qdrant_api_key:
                logger.warning("QDRANT_API_KEY not set, using placeholder. Set this for production use.")
                qdrant_api_key = "placeholder-qdrant-key"
            
            processor = BatchQuestionProcessor(
                project_id=project_id,
                qdrant_api_key=qdrant_api_key,
                qdrant_url=qdrant_url,
                bucket_name=bucket_name,
                location=location
            )
            
            logger.info("✅ Question Analysis Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize processor: {str(e)}")
            raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "question-analysis-service",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/analyze/file', methods=['POST'])
def analyze_single_file():
    """Analyze a single JSON file"""
    try:
        initialize_processor()
        
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                "error": "file_path is required in request body"
            }), 400
        
        file_path = data['file_path']
        verbose = data.get('verbose', False)
        
        logger.info(f"Analyzing single file: {file_path}")
        
        # Process the file
        result = processor.process_json_file(file_path, verbose=verbose)
        
        # Store in Qdrant
        if result['status'] == 'completed':
            processor.store_analysis_in_qdrant(result)
        
        return jsonify({
            "status": "success",
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error analyzing single file: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/analyze/folder', methods=['POST'])
def analyze_folder():
    """Analyze all JSON files in a folder"""
    try:
        initialize_processor()
        
        data = request.get_json()
        if not data or 'folder_path' not in data:
            return jsonify({
                "error": "folder_path is required in request body"
            }), 400
        
        folder_path = data['folder_path']
        file_pattern = data.get('file_pattern', '*.json')
        batch_size = data.get('batch_size', 5)
        store_in_qdrant = data.get('store_in_qdrant', True)
        verbose = data.get('verbose', False)
        
        logger.info(f"Analyzing folder: {folder_path}")
        
        # Process the folder
        summary = processor.process_folder(
            folder_path=folder_path,
            file_pattern=file_pattern,
            batch_size=batch_size,
            store_in_qdrant=store_in_qdrant,
            verbose=verbose
        )
        
        return jsonify({
            "status": "success",
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error analyzing folder: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/analyze/gcs-folder', methods=['POST'])
def analyze_gcs_folder():
    """Analyze all JSON files in a GCS folder"""
    try:
        initialize_processor()
        
        data = request.get_json()
        if not data or 'gcs_folder_path' not in data:
            return jsonify({
                "error": "gcs_folder_path is required in request body"
            }), 400
        
        gcs_folder_path = data['gcs_folder_path']
        local_temp_dir = data.get('local_temp_dir', '/tmp/question_analysis')
        file_pattern = data.get('file_pattern', '*.json')
        batch_size = data.get('batch_size', 5)
        store_in_qdrant = data.get('store_in_qdrant', True)
        verbose = data.get('verbose', False)
        
        logger.info(f"Analyzing GCS folder: {gcs_folder_path}")
        
        # Process the GCS folder
        summary = processor.process_gcs_folder(
            gcs_folder_path=gcs_folder_path,
            local_temp_dir=local_temp_dir,
            file_pattern=file_pattern,
            batch_size=batch_size,
            store_in_qdrant=store_in_qdrant,
            verbose=verbose
        )
        
        return jsonify({
            "status": "success",
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error analyzing GCS folder: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/search/analysis', methods=['POST'])
def search_analysis():
    """Search analysis results in Qdrant"""
    try:
        initialize_processor()
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "error": "query is required in request body"
            }), 400
        
        query = data['query']
        limit = data.get('limit', 10)
        score_threshold = data.get('score_threshold', 0.7)
        
        logger.info(f"Searching analysis results for: {query}")
        
        # Generate query embedding using the processor's embedding generator
        query_embedding = processor.embedding_generator.generate_single_embedding(query)
        
        if not query_embedding:
            return jsonify({
                "error": "Failed to generate query embedding"
            }), 500
        
        # Search in Qdrant
        results = processor.vector_store.search_similar(
            collection_name=processor.collection_name,
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error searching analysis: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/collections', methods=['GET'])
def list_collections():
    """List all collections in Qdrant"""
    try:
        initialize_processor()
        
        collections = processor.vector_store.list_collections()
        
        return jsonify({
            "status": "success",
            "collections": collections
        })
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/collections/<collection_name>/info', methods=['GET'])
def get_collection_info(collection_name):
    """Get information about a specific collection"""
    try:
        initialize_processor()
        
        info = processor.vector_store.get_collection_info(collection_name)
        
        if info is None:
            return jsonify({
                "error": f"Collection {collection_name} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "collection_info": info
        })
        
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Initialize processor on startup
    try:
        initialize_processor()
    except Exception as e:
        logger.error(f"Failed to initialize processor: {str(e)}")
        exit(1)
    
    # Run the Flask app
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
