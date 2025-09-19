"""
Batch Question Analysis Processor
Processes multiple JSON files in a folder and stores results in Qdrant
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from analyzer import CBSEQuestionAnalyzer
from vector_store import VectorStore
from embedding_generator import EmbeddingGenerator
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.gcp.bucket_manager import BucketManager

logger = logging.getLogger(__name__)

class BatchQuestionProcessor:
    """Processes multiple question JSON files and stores analysis results"""
    
    def __init__(self, 
                 project_id: str,
                 qdrant_api_key: str = None,
                 qdrant_url: str = None,
                 bucket_name: str = None,
                 location: str = "us-central1"):
        """
        Initialize the batch processor
        
        Args:
            project_id: GCP project ID for Vertex AI and bucket operations
            qdrant_api_key: Qdrant API key for content retrieval
            qdrant_url: Qdrant cluster URL (optional)
            bucket_name: GCS bucket name for file storage
            location: Vertex AI location
        """
        self.project_id = project_id
        self.location = location
        
        # Initialize vector store for content retrieval (not storage)
        if qdrant_api_key:
            self.vector_store = VectorStore(api_key=qdrant_api_key, url=qdrant_url)
            self.embedding_generator = EmbeddingGenerator(project_id=project_id, location=location)
            self.content_collection_name = "book_social_science_ncert_class_xii"  # Collection for book content
        else:
            self.vector_store = None
            self.embedding_generator = None
            logger.warning("Qdrant not configured - content retrieval will be disabled")
        
        # Initialize analyzer with Vertex AI and content retriever
        self.analyzer = CBSEQuestionAnalyzer(
            project_id, 
            location, 
            content_retriever=self.retrieve_relevant_content if self.vector_store else None
        )
        
        # Initialize bucket manager
        if bucket_name:
            self.bucket_manager = BucketManager(project_id, bucket_name)
        else:
            self.bucket_manager = None
    
    def retrieve_relevant_content(self, question_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant book content for a question to improve analysis accuracy
        
        Args:
            question_text: The question text to find relevant content for
            limit: Maximum number of relevant passages to retrieve
            
        Returns:
            List of relevant content passages with metadata
        """
        if not self.vector_store or not self.embedding_generator:
            logger.warning("Vector store not available - skipping content retrieval")
            return []
        
        try:
            # Generate embedding for the question
            question_embedding = self.embedding_generator.generate_single_embedding(question_text)
            if not question_embedding:
                logger.warning("Failed to generate embedding for question")
                return []
            
            # Search for relevant content in Qdrant
            results = self.vector_store.search_similar(
                collection_name=self.content_collection_name,
                query_embedding=question_embedding,
                limit=limit,
                score_threshold=0.7  # Only return highly relevant content
            )
            
            if results:
                logger.info(f"Retrieved {len(results)} relevant content passages for question analysis")
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving relevant content: {str(e)}")
            return []
    
    def process_json_file(self, file_path: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Process a single JSON file and return analysis results
        
        Args:
            file_path: Path to the JSON file
            verbose: Whether to show detailed logging
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Analyze the question paper
            analysis_report, output_path = self.analyzer.analyze_question_paper(
                file_path, 
                verbose=verbose
            )
            
            # Load the original JSON to get metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # Create analysis result document
            analysis_result = {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "analysis_date": datetime.now().isoformat(),
                "analysis_report": analysis_report,
                "document_info": original_data.get('document_info', {}),
                "total_questions": len(original_data.get('questions', [])),
                "analysis_id": str(uuid.uuid4()),
                "status": "completed"
            }
            
            # Upload analysis report to GCS if bucket manager is available
            if self.bucket_manager:
                gcs_path = f"analysis_reports/{Path(file_path).stem}_analysis.md"
                self.bucket_manager.upload_text(
                    analysis_report, 
                    gcs_path, 
                    "text/markdown"
                )
                analysis_result["gcs_report_path"] = f"gs://{self.bucket_manager.bucket_name}/{gcs_path}"
            
            logger.info(f"✅ Successfully processed {file_path}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path}: {str(e)}")
            return {
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "analysis_date": datetime.now().isoformat(),
                "error": str(e),
                "status": "failed"
            }
    
    
    def process_folder(self, 
                      folder_path: str, 
                      file_pattern: str = "*.json",
                      batch_size: int = 5,
                      verbose: bool = False) -> Dict[str, Any]:
        """
        Process all JSON files in a folder
        
        Args:
            folder_path: Path to the folder containing JSON files
            file_pattern: File pattern to match (default: "*.json")
            batch_size: Number of questions per batch for analysis
            verbose: Whether to show detailed logging
            
        Returns:
            Dictionary containing processing summary and results
        """
        try:
            logger.info(f"🚀 Starting batch processing of folder: {folder_path}")
            
            # Find all JSON files
            folder = Path(folder_path)
            if not folder.exists():
                raise ValueError(f"Folder does not exist: {folder_path}")
            
            json_files = list(folder.glob(file_pattern))
            if not json_files:
                logger.warning(f"No JSON files found in {folder_path} with pattern {file_pattern}")
                return {
                    "folder_path": folder_path,
                    "total_files": 0,
                    "processed_files": 0,
                    "failed_files": 0,
                    "results": []
                }
            
            logger.info(f"📁 Found {len(json_files)} JSON files to process")
            
            # Note: Qdrant is used for content retrieval, not for storing analysis results
            
            # Process each file
            results = []
            processed_count = 0
            failed_count = 0
            
            for i, json_file in enumerate(json_files, 1):
                logger.info(f"📄 Processing file {i}/{len(json_files)}: {json_file.name}")
                
                try:
                    # Process the file
                    analysis_result = self.process_json_file(str(json_file), verbose)
                    results.append(analysis_result)
                    
                    if analysis_result["status"] == "completed":
                        processed_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {json_file.name}: {str(e)}")
                    failed_count += 1
                    results.append({
                        "file_path": str(json_file),
                        "file_name": json_file.name,
                        "analysis_date": datetime.now().isoformat(),
                        "error": str(e),
                        "status": "failed"
                    })
            
            # Create summary
            summary = {
                "folder_path": folder_path,
                "total_files": len(json_files),
                "processed_files": processed_count,
                "failed_files": failed_count,
                "processing_date": datetime.now().isoformat(),
                "results": results
            }
            
            # Save summary to file
            summary_path = folder / "batch_analysis_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Batch processing completed!")
            logger.info(f"📊 Processed: {processed_count}/{len(json_files)} files")
            logger.info(f"❌ Failed: {failed_count}/{len(json_files)} files")
            logger.info(f"💾 Summary saved to: {summary_path}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error during batch processing: {str(e)}")
            raise
    
    def process_gcs_folder(self, 
                          gcs_folder_path: str,
                          local_temp_dir: str = "/tmp/question_analysis",
                          file_pattern: str = "*.json",
                          batch_size: int = 5,
                          verbose: bool = False) -> Dict[str, Any]:
        """
        Process JSON files from a GCS folder
        
        Args:
            gcs_folder_path: GCS folder path (e.g., "book_ip_sqp/extracted_questions/")
            local_temp_dir: Local temporary directory for downloads
            file_pattern: File pattern to match (default: "*.json")
            batch_size: Number of questions per batch for analysis
            verbose: Whether to show detailed logging
            
        Returns:
            Dictionary containing processing summary and results
        """
        if not self.bucket_manager:
            raise ValueError("Bucket manager not initialized. Provide GCP project ID and bucket name.")
        
        try:
            logger.info(f"🚀 Starting GCS batch processing of folder: {gcs_folder_path}")
            
            # Create local temp directory
            temp_dir = Path(local_temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # List files in GCS folder
            gcs_files = self.bucket_manager.list_files_in_folder(gcs_folder_path)
            json_files = [f for f in gcs_files if f.endswith('.json')]
            
            if not json_files:
                logger.warning(f"No JSON files found in GCS folder: {gcs_folder_path}")
                return {
                    "gcs_folder_path": gcs_folder_path,
                    "total_files": 0,
                    "processed_files": 0,
                    "failed_files": 0,
                    "results": []
                }
            
            logger.info(f"📁 Found {len(json_files)} JSON files in GCS folder")
            
            # Note: Qdrant is used for content retrieval, not for storing analysis results
            
            # Process each file
            results = []
            processed_count = 0
            failed_count = 0
            
            for i, gcs_file in enumerate(json_files, 1):
                try:
                    # Extract filename from GCS path
                    file_name = Path(gcs_file).name
                    local_file_path = temp_dir / file_name
                    
                    logger.info(f"📄 Processing file {i}/{len(json_files)}: {file_name}")
                    
                    # Download file from GCS
                    if not self.bucket_manager.download_file(gcs_file, str(local_file_path)):
                        logger.error(f"❌ Failed to download {gcs_file}")
                        failed_count += 1
                        continue
                    
                    # Process the file
                    analysis_result = self.process_json_file(str(local_file_path), verbose)
                    analysis_result["gcs_source_path"] = gcs_file
                    results.append(analysis_result)
                    
                    if analysis_result["status"] == "completed":
                        processed_count += 1
                    else:
                        failed_count += 1
                    
                    # Clean up local file
                    local_file_path.unlink()
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {gcs_file}: {str(e)}")
                    failed_count += 1
                    results.append({
                        "gcs_source_path": gcs_file,
                        "file_name": Path(gcs_file).name,
                        "analysis_date": datetime.now().isoformat(),
                        "error": str(e),
                        "status": "failed"
                    })
            
            # Create summary
            summary = {
                "gcs_folder_path": gcs_folder_path,
                "total_files": len(json_files),
                "processed_files": processed_count,
                "failed_files": failed_count,
                "processing_date": datetime.now().isoformat(),
                "results": results
            }
            
            # Save summary to GCS
            summary_gcs_path = f"{gcs_folder_path.rstrip('/')}/analysis_summary.json"
            self.bucket_manager.upload_json(summary, summary_gcs_path)
            
            logger.info(f"✅ GCS batch processing completed!")
            logger.info(f"📊 Processed: {processed_count}/{len(json_files)} files")
            logger.info(f"❌ Failed: {failed_count}/{len(json_files)} files")
            logger.info(f"💾 Summary saved to GCS: gs://{self.bucket_manager.bucket_name}/{summary_gcs_path}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error during GCS batch processing: {str(e)}")
            raise
        finally:
            # Clean up temp directory
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
