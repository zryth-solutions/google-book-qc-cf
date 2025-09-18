#!/usr/bin/env python3
"""
Book Extraction CLI Application
Command-line interface for PDF question and answer extraction
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
from vertex.extractor import VertexAIPDFExtractor
from vertex.subject_mapper import SubjectExtractorFactory

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gcp.bucket_manager import BucketManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_gcs_path
        }

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
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_gcs_path
        }

def process_folder_questions(folder_path: str, subject: str = "computer_applications") -> Dict[str, Any]:
    """Extract questions from all PDFs in a folder"""
    try:
        logger.info(f"Starting folder extraction: {folder_path}, subject: {subject}")
        
        # List all PDF files in the folder
        pdf_files = bucket_manager.list_files_in_folder(folder_path, ".pdf", return_full_paths=False)
        
        if not pdf_files:
            return {
                'status': 'error',
                'message': f'No PDF files found in folder: {folder_path}'
            }
        
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
                if result['status'] == 'success':
                    successful_extractions += 1
                else:
                    failed_extractions += 1
                logger.info(f"Successfully processed {pdf_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}")
                results.append({
                    'pdf_file': pdf_file,
                    'status': 'error',
                    'error': str(e)
                })
                failed_extractions += 1
        
        return {
            'status': 'success',
            'folder_path': folder_path,
            'subject': subject,
            'total_files': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in folder extraction: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'folder_path': folder_path
        }

def process_folder_answers(folder_path: str, subject: str = "computer_applications") -> Dict[str, Any]:
    """Extract answers from all PDFs in a folder"""
    try:
        logger.info(f"Starting folder answer extraction: {folder_path}, subject: {subject}")
        
        # List all PDF files in the folder
        pdf_files = bucket_manager.list_files_in_folder(folder_path, ".pdf", return_full_paths=False)
        
        if not pdf_files:
            return {
                'status': 'error',
                'message': f'No PDF files found in folder: {folder_path}'
            }
        
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
                if result['status'] == 'success':
                    successful_extractions += 1
                else:
                    failed_extractions += 1
                logger.info(f"Successfully processed {pdf_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {str(e)}")
                results.append({
                    'pdf_file': pdf_file,
                    'status': 'error',
                    'error': str(e)
                })
                failed_extractions += 1
        
        return {
            'status': 'success',
            'folder_path': folder_path,
            'subject': subject,
            'total_files': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in folder answer extraction: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'folder_path': folder_path
        }

def process_book_folder_complete(folder_path: str, subject: str = 'computer_applications') -> Dict[str, Any]:
    """
    Process complete book folder structure:
    - Process all PDFs in question_papers/ subfolder -> save to extracted_questions/
    - Process all PDFs in answer_keys/ subfolder -> save to extracted_answers/
    """
    try:
        logger.info(f"Starting complete book folder processing for: {folder_path}")
        
        # Ensure folder_path doesn't start with gs://
        if folder_path.startswith('gs://'):
            folder_path = folder_path.replace(f'gs://{BUCKET_NAME}/', '')
        
        # Define subfolder paths
        question_papers_path = f"{folder_path}/question_papers"
        answer_keys_path = f"{folder_path}/answer_keys"
        
        # Define output paths
        extracted_questions_path = f"{folder_path}/extracted_questions"
        extracted_answers_path = f"{folder_path}/extracted_answers"
        
        logger.info(f"Processing questions from: {question_papers_path}")
        logger.info(f"Processing answers from: {answer_keys_path}")
        logger.info(f"Output questions to: {extracted_questions_path}")
        logger.info(f"Output answers to: {extracted_answers_path}")
        
        results = {}
        
        # Process question papers
        try:
            questions_result = process_folder_questions_with_output(question_papers_path, subject, extracted_questions_path)
            results['questions'] = questions_result
            logger.info(f"Question processing completed: {questions_result.get('successful_extractions', 0)} successful")
        except Exception as e:
            logger.error(f"Failed to process question papers: {str(e)}")
            results['questions'] = {
                'status': 'error',
                'error': str(e),
                'folder_path': question_papers_path
            }
        
        # Process answer keys
        try:
            answers_result = process_folder_answers_with_output(answer_keys_path, subject, extracted_answers_path)
            results['answers'] = answers_result
            logger.info(f"Answer processing completed: {answers_result.get('successful_extractions', 0)} successful")
        except Exception as e:
            logger.error(f"Failed to process answer keys: {str(e)}")
            results['answers'] = {
                'status': 'error',
                'error': str(e),
                'folder_path': answer_keys_path
            }
        
        # Calculate overall statistics
        total_questions = results.get('questions', {}).get('successful_extractions', 0)
        total_answers = results.get('answers', {}).get('successful_extractions', 0)
        total_failed = (results.get('questions', {}).get('failed_extractions', 0) + 
                       results.get('answers', {}).get('failed_extractions', 0))
        
        return {
            'status': 'success',
            'message': 'Complete book folder processing completed',
            'folder_path': folder_path,
            'subject': subject,
            'total_questions_extracted': total_questions,
            'total_answers_extracted': total_answers,
            'total_failed': total_failed,
            'extracted_questions_path': extracted_questions_path,
            'extracted_answers_path': extracted_answers_path,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in complete book folder processing: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'folder_path': folder_path
        }

def process_folder_questions_with_output(folder_path: str, subject: str, output_folder: str) -> Dict[str, Any]:
    """Process folder questions and save to specific output folder"""
    try:
        # Get list of PDF files
        pdf_files = bucket_manager.list_files_in_folder(folder_path, file_extension='.pdf', return_full_paths=False)
        
        if not pdf_files:
            return {
                'status': 'error',
                'message': f'No PDF files found in folder: {folder_path}'
            }
        
        # Process each PDF file
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for pdf_file in pdf_files:
            logger.info(f"Processing question paper: {pdf_file}")
            try:
                # Create full GCS path
                pdf_gcs_path = f"gs://{BUCKET_NAME}/{pdf_file}"
                
                # Extract filename without extension for output naming
                filename = pdf_file.split('/')[-1].replace('.pdf', '')
                output_path = f"{output_folder}/{filename}_questions.json"
                
                # Process the PDF with custom output path
                result = process_question_paper_with_output(pdf_gcs_path, subject, output_path)
                result['pdf_file'] = pdf_file
                result['output_path'] = output_path
                results.append(result)
                
                if result['status'] == 'success':
                    successful_extractions += 1
                else:
                    failed_extractions += 1
                logger.info(f"Successfully processed question paper: {pdf_file}")
                
            except Exception as e:
                logger.error(f"Failed to process question paper {pdf_file}: {str(e)}")
                results.append({
                    'pdf_file': pdf_file,
                    'status': 'error',
                    'error': str(e)
                })
                failed_extractions += 1
        
        return {
            'status': 'success',
            'folder_path': folder_path,
            'output_folder': output_folder,
            'subject': subject,
            'total_files': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'results': results
        }

    except Exception as e:
        logger.error(f"Error in folder question extraction with output: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'folder_path': folder_path
        }

def process_folder_answers_with_output(folder_path: str, subject: str, output_folder: str) -> Dict[str, Any]:
    """Process folder answers and save to specific output folder"""
    try:
        # Get list of PDF files
        pdf_files = bucket_manager.list_files_in_folder(folder_path, file_extension='.pdf', return_full_paths=False)
        
        if not pdf_files:
            return {
                'status': 'error',
                'message': f'No PDF files found in folder: {folder_path}'
            }
        
        # Process each PDF file
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for pdf_file in pdf_files:
            logger.info(f"Processing answer key: {pdf_file}")
            try:
                # Create full GCS path
                pdf_gcs_path = f"gs://{BUCKET_NAME}/{pdf_file}"
                
                # Extract filename without extension for output naming
                filename = pdf_file.split('/')[-1].replace('.pdf', '')
                output_path = f"{output_folder}/{filename}_answers.json"
                
                # Process the PDF with custom output path
                result = process_answer_key_with_output(pdf_gcs_path, subject, output_path)
                result['pdf_file'] = pdf_file
                result['output_path'] = output_path
                results.append(result)
                
                if result['status'] == 'success':
                    successful_extractions += 1
                else:
                    failed_extractions += 1
                logger.info(f"Successfully processed answer key: {pdf_file}")
                
            except Exception as e:
                logger.error(f"Failed to process answer key {pdf_file}: {str(e)}")
                results.append({
                    'pdf_file': pdf_file,
                    'status': 'error',
                    'error': str(e)
                })
                failed_extractions += 1
        
        return {
            'status': 'success',
            'folder_path': folder_path,
            'output_folder': output_folder,
            'subject': subject,
            'total_files': len(pdf_files),
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in folder answer extraction with output: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'folder_path': folder_path
        }

def process_question_paper_with_output(pdf_path: str, subject: str, output_path: str) -> Dict[str, Any]:
    """Process question paper and save to specific output path"""
    try:
        # Extract filename from GCS path
        pdf_filename = extract_filename_from_gcs_path(pdf_path)
        logger.info(f"Processing question paper: {pdf_filename}")
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                raise Exception(f"Failed to download PDF from GCS: {pdf_filename}")
            
            # Get subject-specific extractor and config
            factory = SubjectExtractorFactory()
            subject_extractor = factory.get_extractor(subject)
            question_config = subject_extractor.get_question_config()
            
            # Initialize Vertex AI extractor
            vertex_extractor = VertexAIPDFExtractor(PROJECT_ID, VERTEX_AI_LOCATION)
            
            # Extract questions
            logger.info(f"Starting question extraction for: {pdf_filename}")
            result = vertex_extractor.process_pdf(temp_pdf_path, question_config, subject_extractor)
            
            if not result:
                raise Exception("Question extraction failed")
            
            # Save to specified output path
            bucket_manager.upload_json(result, output_path)
            
            return {
                'status': 'success',
                'message': 'Questions extracted successfully',
                'pdf_path': pdf_path,
                'subject': subject,
                'output_path': output_path,
                'question_count': len(result.get('questions', [])),
                'document_info': result.get('document_info', {})
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
        
    except Exception as e:
        logger.error(f"Error processing question paper with output: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_path
        }

def process_answer_key_with_output(pdf_path: str, subject: str, output_path: str) -> Dict[str, Any]:
    """Process answer key and save to specific output path"""
    try:
        # Extract filename from GCS path
        pdf_filename = extract_filename_from_gcs_path(pdf_path)
        logger.info(f"Processing answer key: {pdf_filename}")
        
        # Download PDF from GCS to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Download PDF from bucket
            if not bucket_manager.download_file(pdf_filename, temp_pdf_path):
                raise Exception(f"Failed to download PDF from GCS: {pdf_filename}")
            
            # Get subject-specific extractor and config
            factory = SubjectExtractorFactory()
            subject_extractor = factory.get_extractor(subject)
            answer_config = subject_extractor.get_answer_config()
            
            # Initialize Vertex AI extractor
            vertex_extractor = VertexAIPDFExtractor(PROJECT_ID, VERTEX_AI_LOCATION)
            
            # Extract answers
            logger.info(f"Starting answer extraction for: {pdf_filename}")
            result = vertex_extractor.process_pdf(temp_pdf_path, answer_config, subject_extractor)
            
            if not result:
                raise Exception("Answer extraction failed")
            
            # Save to specified output path
            bucket_manager.upload_json(result, output_path)
            
            return {
                'status': 'success',
                'message': 'Answers extracted successfully',
                'pdf_path': pdf_path,
                'subject': subject,
                'output_path': output_path,
                'answer_count': len(result.get('answers', [])),
                'document_info': result.get('document_info', {})
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
        
    except Exception as e:
        logger.error(f"Error processing answer key with output: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'pdf_path': pdf_path
        }

def get_available_subjects() -> Dict[str, Any]:
    """Get list of available subjects"""
    try:
        factory = SubjectExtractorFactory()
        subjects = factory.get_available_subjects()
        
        return {
            'status': 'success',
            'subjects': subjects
        }
        
    except Exception as e:
        logger.error(f"Error getting subjects: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Book Extraction CLI')
    parser.add_argument('operation', choices=[
        'extract-questions',
        'extract-answers', 
        'extract-all',
        'extract-folder-questions',
        'extract-folder-answers',
        'process-book-folder',
        'get-subjects'
    ], help='Operation to perform')
    
    # Common arguments
    parser.add_argument('--pdf-path', help='GCS path to PDF file')
    parser.add_argument('--subject', default='computer_applications', help='Subject for extraction')
    parser.add_argument('--folder-path', help='GCS folder path for batch processing')
    parser.add_argument('--question-pdf-path', help='GCS path to question paper PDF')
    parser.add_argument('--answer-pdf-path', help='GCS path to answer key PDF')
    
    args = parser.parse_args()
    
    result = {}
    
    try:
        if args.operation == 'extract-questions':
            if not args.pdf_path:
                raise ValueError("--pdf-path is required for extract-questions")
            result = process_question_paper(args.pdf_path, args.subject)
            
        elif args.operation == 'extract-answers':
            if not args.pdf_path:
                raise ValueError("--pdf-path is required for extract-answers")
            result = process_answer_key(args.pdf_path, args.subject)
            
        elif args.operation == 'extract-all':
            results = {}
            if args.question_pdf_path:
                results['questions'] = process_question_paper(args.question_pdf_path, args.subject)
            if args.answer_pdf_path:
                results['answers'] = process_answer_key(args.answer_pdf_path, args.subject)
            if not args.question_pdf_path and not args.answer_pdf_path:
                raise ValueError("At least one of --question-pdf-path or --answer-pdf-path is required")
            result = {
                'status': 'success',
                'message': 'Extraction completed successfully',
                'results': results
            }
            
        elif args.operation == 'extract-folder-questions':
            if not args.folder_path:
                raise ValueError("--folder-path is required for extract-folder-questions")
            result = process_folder_questions(args.folder_path, args.subject)
            
        elif args.operation == 'extract-folder-answers':
            if not args.folder_path:
                raise ValueError("--folder-path is required for extract-folder-answers")
            result = process_folder_answers(args.folder_path, args.subject)
            
        elif args.operation == 'process-book-folder':
            if not args.folder_path:
                raise ValueError("--folder-path is required for process-book-folder")
            result = process_book_folder_complete(args.folder_path, args.subject)
            
        elif args.operation == 'get-subjects':
            result = get_available_subjects()
    
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
