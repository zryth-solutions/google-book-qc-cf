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
from rag_ingestion_service.vector_store import VectorStore
from rag_ingestion_service.embedding_generator import EmbeddingGenerator
from utils.gcp.bucket_manager import BucketManager

logger = logging.getLogger(__name__)

class BatchQuestionProcessor:
    """Processes multiple question JSON files and stores analysis results"""
    
    def __init__(self, 
                 project_id: str,
                 qdrant_api_key: str,
                 qdrant_url: str = None,
                 bucket_name: str = None,
                 location: str = "us-central1"):
        """
        Initialize the batch processor
        
        Args:
            project_id: GCP project ID for Vertex AI and bucket operations
            qdrant_api_key: Qdrant API key for vector storage
            qdrant_url: Qdrant cluster URL (optional)
            bucket_name: GCS bucket name for file storage
            location: Vertex AI location
        """
        self.project_id = project_id
        self.location = location
        
        # Initialize analyzer with Vertex AI
        self.analyzer = CBSEQuestionAnalyzer(project_id, location)
        
        # Initialize vector store
        self.vector_store = VectorStore(qdrant_api_key, qdrant_url)
        
        # Initialize embedding generator
        self.embedding_generator = EmbeddingGenerator(project_id, location)
        
        # Initialize bucket manager
        if bucket_name:
            self.bucket_manager = BucketManager(project_id, bucket_name)
        else:
            self.bucket_manager = None
            
        self.collection_name = "question_analysis_results"
        
    def create_analysis_collection(self) -> bool:
        """Create collection for storing analysis results"""
        try:
            # Skip collection creation if using placeholder API keys
            if self.vector_store.api_key == "placeholder-qdrant-key":
                logger.warning("Skipping Qdrant collection creation - using placeholder API key")
                return False
                
            return self.vector_store.create_collection(
                self.collection_name, 
                "Question Analysis Results"
            )
        except Exception as e:
            logger.error(f"Failed to create analysis collection: {str(e)}")
            return False
    
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
    
    def store_analysis_in_qdrant(self, analysis_result: Dict[str, Any]) -> bool:
        """
        Store analysis result in Qdrant vector store
        
        Args:
            analysis_result: Analysis result dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a chunk for the analysis report
            from rag_ingestion_service.semantic_chunker import Chunk
            
            chunk = Chunk(
                content=analysis_result["analysis_report"],
                chunk_index=0,
                start_position=0,
                end_position=len(analysis_result["analysis_report"]),
                metadata={
                    "file_name": analysis_result["file_name"],
                    "file_path": analysis_result["file_path"],
                    "analysis_date": analysis_result["analysis_date"],
                    "analysis_id": analysis_result["analysis_id"],
                    "total_questions": analysis_result.get("total_questions", 0),
                    "document_title": analysis_result.get("document_info", {}).get("title", "Unknown"),
                    "document_class": analysis_result.get("document_info", {}).get("class", "10"),
                    "status": analysis_result["status"],
                    "gcs_report_path": analysis_result.get("gcs_report_path", ""),
                    "chunk_type": "analysis_report"
                }
            )
            
            # Generate embedding for the analysis report using Vertex AI
            embedding = self.embedding_generator.generate_single_embedding(analysis_result["analysis_report"])
            
            if not embedding:
                logger.error("Failed to generate embedding for analysis report")
                return False
            
            # Store in Qdrant
            success = self.vector_store.upsert_chunks(
                self.collection_name,
                [chunk],
                [embedding]
            )
            
            if success:
                logger.info(f"✅ Stored analysis for {analysis_result['file_name']} in Qdrant")
            else:
                logger.error(f"❌ Failed to store analysis for {analysis_result['file_name']} in Qdrant")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error storing analysis in Qdrant: {str(e)}")
            return False
    
    def process_folder(self, 
                      folder_path: str, 
                      file_pattern: str = "*.json",
                      batch_size: int = 5,
                      store_in_qdrant: bool = True,
                      verbose: bool = False) -> Dict[str, Any]:
        """
        Process all JSON files in a folder
        
        Args:
            folder_path: Path to the folder containing JSON files
            file_pattern: File pattern to match (default: "*.json")
            batch_size: Number of questions per batch for analysis
            store_in_qdrant: Whether to store results in Qdrant
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
            
            # Create analysis collection if storing in Qdrant
            if store_in_qdrant:
                self.create_analysis_collection()
            
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
                        
                        # Store in Qdrant if requested
                        if store_in_qdrant:
                            self.store_analysis_in_qdrant(analysis_result)
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
                          store_in_qdrant: bool = True,
                          verbose: bool = False) -> Dict[str, Any]:
        """
        Process JSON files from a GCS folder
        
        Args:
            gcs_folder_path: GCS folder path (e.g., "book_ip_sqp/extracted_questions/")
            local_temp_dir: Local temporary directory for downloads
            file_pattern: File pattern to match (default: "*.json")
            batch_size: Number of questions per batch for analysis
            store_in_qdrant: Whether to store results in Qdrant
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
            
            # Create analysis collection if storing in Qdrant
            if store_in_qdrant:
                self.create_analysis_collection()
            
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
                        
                        # Store in Qdrant if requested
                        if store_in_qdrant:
                            self.store_analysis_in_qdrant(analysis_result)
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
