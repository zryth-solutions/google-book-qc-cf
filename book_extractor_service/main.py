import os
import json
import tempfile
import logging
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
from typing import Dict, Any, Optional

# Import our modules
from vertex.extractor import VertexAIPDFExtractor
from vertex.subject_mapper import SubjectExtractorFactory

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

# Environment variables
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'book-qc-cf')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
VERTEX_AI_LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')

# Initialize services
bucket_manager = BucketManager(PROJECT_ID, BUCKET_NAME)

def extract_filename_from_gcs_path(gcs_path: str) -> str:
    """Extract filename from GCS path"""
    if gcs_path.startswith('gs://'):
        # Remove gs://bucket-name/ prefix to get the relative path
        parts = gcs_path.split('/', 3)
        if len(parts) >= 4:
            return parts[3]  # Return the relative path (e.g., question_papers/SQP-2.pdf)
        return gcs_path.split('/')[-1]  # Fallback to just filename
    return gcs_path

def process_question_paper(pdf_gcs_path: str, subject: str = "computer_applications") -> Dict[str, Any]:
    """Process question paper PDF and extract questions"""
    try:
        # Extract filename from GCS path
        pdf_filename = extract_filename_from_gcs_path(pdf_gcs_path)
        logger.info(f"Processing question paper: {pdf_filename}")
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                raise Exception(f"Failed to download PDF from GCS: {pdf_filename}")
            
            # Get subject-specific extractor
            extractor_factory = SubjectExtractorFactory()
            subject_extractor = extractor_factory.get_extractor(subject)
            
            # Initialize Vertex AI extractor
            vertex_extractor = VertexAIPDFExtractor(PROJECT_ID, VERTEX_AI_LOCATION)
            
            # Get question extraction config
            question_config = subject_extractor.get_question_config()
            
            # Extract questions
            logger.info(f"Starting question extraction for: {pdf_filename}")
            result = vertex_extractor.process_pdf(temp_pdf_path, question_config, subject_extractor)
            
            if not result:
                raise Exception("Question extraction failed")
            
            # Upload result to GCS
            output_filename = f"extractions/questions/{pdf_filename.replace('.pdf', '_questions.json')}"
            if not bucket_manager.upload_json(result, output_filename):
                raise Exception(f"Failed to upload questions to GCS: {output_filename}")
            
            return {
                'status': 'success',
                'extraction_type': 'questions',
                'subject': subject,
                'extraction_gcs_path': f"gs://{BUCKET_NAME}/{output_filename}",
                'pdf_path': pdf_gcs_path,
                'total_questions': len(result.get('questions', [])),
                'document_info': result.get('document_info', {})
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        logger.error(f"Error processing question paper: {str(e)}")
        raise

def process_answer_key(pdf_gcs_path: str, subject: str = "computer_applications") -> Dict[str, Any]:
    """Process answer key PDF and extract answers"""
    try:
        # Extract filename from GCS path
        pdf_filename = extract_filename_from_gcs_path(pdf_gcs_path)
        logger.info(f"Processing answer key: {pdf_filename}")
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                raise Exception(f"Failed to download PDF from GCS: {pdf_filename}")
            
            # Get subject-specific extractor
            extractor_factory = SubjectExtractorFactory()
            subject_extractor = extractor_factory.get_extractor(subject)
            
            # Initialize Vertex AI extractor
            vertex_extractor = VertexAIPDFExtractor(PROJECT_ID, VERTEX_AI_LOCATION)
            
            # Get answer extraction config
            answer_config = subject_extractor.get_answer_config()
            
            # Extract answers
            logger.info(f"Starting answer extraction for: {pdf_filename}")
            result = vertex_extractor.process_pdf(temp_pdf_path, answer_config, subject_extractor)
            
            if not result:
                raise Exception("Answer extraction failed")
            
            # Upload result to GCS
            output_filename = f"extractions/answers/{pdf_filename.replace('.pdf', '_answers.json')}"
            if not bucket_manager.upload_json(result, output_filename):
                raise Exception(f"Failed to upload answers to GCS: {output_filename}")
            
            return {
                'status': 'success',
                'extraction_type': 'answers',
                'subject': subject,
                'extraction_gcs_path': f"gs://{BUCKET_NAME}/{output_filename}",
                'pdf_path': pdf_gcs_path,
                'total_answers': len(result.get('answers', [])),
                'document_info': result.get('document_info', {})
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
                
    except Exception as e:
        logger.error(f"Error processing answer key: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'book-extractor'}), 200

@app.route('/extract-questions', methods=['POST'])
def extract_questions():
    """Extract questions from question paper PDF"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_gcs_path = data.get('pdf_path')
        if not pdf_gcs_path:
            raise BadRequest("pdf_path is required")
        
        subject = data.get('subject', 'computer_applications')
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        # Handle nested pdf_path structure from workflow
        if isinstance(pdf_gcs_path, dict) and 'pdf_path' in pdf_gcs_path:
            pdf_gcs_path = pdf_gcs_path['pdf_path']
            logger.info(f"Extracted nested pdf_path: {pdf_gcs_path}")
        
        logger.info(f"Received question extraction request: {pdf_gcs_path}, subject: {subject}")
        
        # Process question paper
        result = process_question_paper(pdf_gcs_path, subject)
        
        return jsonify(result), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in extract_questions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/extract-answers', methods=['POST'])
def extract_answers():
    """Extract answers from answer key PDF"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        pdf_gcs_path = data.get('pdf_path')
        if not pdf_gcs_path:
            raise BadRequest("pdf_path is required")
        
        subject = data.get('subject', 'computer_applications')
        bucket_name = data.get('bucket_name', BUCKET_NAME)
        
        # Handle nested pdf_path structure from workflow
        if isinstance(pdf_gcs_path, dict) and 'pdf_path' in pdf_gcs_path:
            pdf_gcs_path = pdf_gcs_path['pdf_path']
            logger.info(f"Extracted nested pdf_path: {pdf_gcs_path}")
        
        logger.info(f"Received answer extraction request: {pdf_gcs_path}, subject: {subject}")
        
        # Process answer key
        result = process_answer_key(pdf_gcs_path, subject)
        
        return jsonify(result), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in extract_answers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/extract-all', methods=['POST'])
def extract_all():
    """Extract both questions and answers from PDFs"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        question_pdf_path = data.get('question_pdf_path')
        answer_pdf_path = data.get('answer_pdf_path')
        subject = data.get('subject', 'computer_applications')
        
        if not question_pdf_path and not answer_pdf_path:
            raise BadRequest("At least one PDF path is required (question_pdf_path or answer_pdf_path)")
        
        results = {}
        
        # Process question paper if provided
        if question_pdf_path:
            logger.info(f"Processing question paper: {question_pdf_path}")
            results['questions'] = process_question_paper(question_pdf_path, subject)
        
        # Process answer key if provided
        if answer_pdf_path:
            logger.info(f"Processing answer key: {answer_pdf_path}")
            results['answers'] = process_answer_key(answer_pdf_path, subject)
        
        return jsonify({
            'status': 'success',
            'message': 'Extraction completed successfully',
            'results': results
        }), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in extract_all: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/subjects', methods=['GET'])
def get_available_subjects():
    """Get list of available subjects"""
    try:
        factory = SubjectExtractorFactory()
        subjects = factory.get_available_subjects()
        
        return jsonify({
            'status': 'success',
            'subjects': subjects
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subjects: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/extract-folder-questions', methods=['POST'])
def extract_folder_questions():
    """Extract questions from all PDFs in a folder"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        folder_path = data.get('folder_path')
        if not folder_path:
            raise BadRequest("folder_path is required")
        
        subject = data.get('subject', 'computer_applications')
        
        logger.info(f"Starting folder extraction: {folder_path}, subject: {subject}")
        
        # List all PDF files in the folder
        pdf_files = bucket_manager.list_files_in_folder(folder_path, ".pdf")
        
        if not pdf_files:
            return jsonify({
                'status': 'error',
                'message': f'No PDF files found in folder: {folder_path}'
            }), 404
        
        # Process each PDF file
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for pdf_file in pdf_files:
            logger.info(f"Processing {pdf_file}")
            try:
                # Create full GCS path
                pdf_gcs_path = f"gs://{BUCKET_NAME}/{pdf_file}"
                
                # Process the PDF
                result = process_question_paper(pdf_gcs_path, subject)
                result['pdf_file'] = pdf_file
                results.append(result)
                successful_extractions += 1
                logger.info(f"Successfully processed {pdf_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}")
                results.append({
                    'pdf_file': pdf_file,
                    'status': 'error',
                    'error': str(e)
                })
                failed_extractions += 1
        
        return jsonify({
            'status': 'success',
            'folder_path': folder_path,
            'subject': subject,
            'total_files': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'results': results
        }), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in extract_folder_questions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/extract-folder-answers', methods=['POST'])
def extract_folder_answers():
    """Extract answers from all PDFs in a folder"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        folder_path = data.get('folder_path')
        if not folder_path:
            raise BadRequest("folder_path is required")
        
        subject = data.get('subject', 'computer_applications')
        
        logger.info(f"Starting folder answer extraction: {folder_path}, subject: {subject}")
        
        # List all PDF files in the folder
        pdf_files = bucket_manager.list_files_in_folder(folder_path, ".pdf")
        
        if not pdf_files:
            return jsonify({
                'status': 'error',
                'message': f'No PDF files found in folder: {folder_path}'
            }), 404
        
        # Process each PDF file
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for pdf_file in pdf_files:
            logger.info(f"Processing {pdf_file}")
            try:
                # Create full GCS path
                pdf_gcs_path = f"gs://{BUCKET_NAME}/{pdf_file}"
                
                # Process the PDF
                result = process_answer_key(pdf_gcs_path, subject)
                result['pdf_file'] = pdf_file
                results.append(result)
                successful_extractions += 1
                logger.info(f"Successfully processed {pdf_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}")
                results.append({
                    'pdf_file': pdf_file,
                    'status': 'error',
                    'error': str(e)
                })
                failed_extractions += 1
        
        return jsonify({
            'status': 'success',
            'folder_path': folder_path,
            'subject': subject,
            'total_files': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'results': results
        }), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in extract_folder_answers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/list-folder-files', methods=['POST'])
def list_folder_files():
    """List all PDF files in a folder"""
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        folder_path = data.get('folder_path')
        if not folder_path:
            raise BadRequest("folder_path is required")
        
        file_extension = data.get('file_extension', '.pdf')
        
        logger.info(f"Listing files in folder: {folder_path}")
        
        # List all files in the folder
        files = bucket_manager.list_files_in_folder(folder_path, file_extension)
        
        return jsonify({
            'status': 'success',
            'folder_path': folder_path,
            'file_extension': file_extension,
            'total_files': len(files),
            'files': files
        }), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in list_folder_files: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
