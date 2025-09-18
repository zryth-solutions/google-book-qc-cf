#!/usr/bin/env python3
"""
Example usage of Question Analysis Service
Demonstrates how to analyze questions and search results using the existing Qdrant collection
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def analyze_extracted_questions():
    """Analyze the extracted questions from the GCS bucket"""
    print("🔍 Analyzing extracted questions from GCS...")
    
    try:
        from batch_processor import BatchQuestionProcessor
        
        # Get API keys from environment
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not gemini_api_key:
            print("❌ Please set GEMINI_API_KEY environment variable")
            return
        
        if not qdrant_api_key:
            print("❌ Please set QDRANT_API_KEY environment variable")
            return
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            gemini_api_key=gemini_api_key,
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL'),
            gcp_project_id=os.getenv('GCP_PROJECT_ID', 'book-qc-cf'),
            bucket_name=os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
        )
        
        # Process the extracted questions folder
        gcs_folder_path = "book_ip_sqp/extracted_questions"
        
        print(f"📁 Processing GCS folder: {gcs_folder_path}")
        
        summary = processor.process_gcs_folder(
            gcs_folder_path=gcs_folder_path,
            local_temp_dir="/tmp/question_analysis",
            file_pattern="*.json",
            batch_size=5,
            store_in_qdrant=True,
            verbose=True
        )
        
        print(f"\n📊 Analysis Summary:")
        print(f"   Total files: {summary['total_files']}")
        print(f"   Successfully processed: {summary['processed_files']}")
        print(f"   Failed: {summary['failed_files']}")
        print(f"   Success rate: {(summary['processed_files']/summary['total_files']*100):.1f}%")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error analyzing questions: {str(e)}")
        return None

def search_analysis_results(query: str, limit: int = 5):
    """Search analysis results in Qdrant"""
    print(f"\n🔍 Searching for: '{query}'")
    
    try:
        from batch_processor import BatchQuestionProcessor
        from embedding_generator import EmbeddingGenerator
        
        # Get API keys
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_api_key:
            print("❌ Please set QDRANT_API_KEY environment variable")
            return
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            gemini_api_key="dummy",  # Not needed for search
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL')
        )
        
        # Generate query embedding
        embedding_gen = EmbeddingGenerator()
        query_embedding = embedding_gen.generate_embedding(query)
        
        # Search in Qdrant
        results = processor.vector_store.search_similar(
            collection_name=processor.collection_name,
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=0.7
        )
        
        if not results:
            print("❌ No results found")
            return
        
        print(f"✅ Found {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result['score']:.3f}")
            print(f"   File: {result['metadata'].get('file_name', 'Unknown')}")
            print(f"   Analysis ID: {result['metadata'].get('analysis_id', 'Unknown')}")
            print(f"   Questions: {result['metadata'].get('total_questions', 'Unknown')}")
            print(f"   Document: {result['metadata'].get('document_title', 'Unknown')}")
            print(f"   Content preview: {result['content'][:200]}...")
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching results: {str(e)}")
        return None

def list_collections():
    """List all collections in Qdrant"""
    print("\n📚 Listing Qdrant collections...")
    
    try:
        from batch_processor import BatchQuestionProcessor
        
        # Get API keys
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_api_key:
            print("❌ Please set QDRANT_API_KEY environment variable")
            return
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            gemini_api_key="dummy",  # Not needed for listing
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL')
        )
        
        # List collections
        collections = processor.vector_store.list_collections()
        
        print(f"✅ Found {len(collections)} collections:")
        for collection in collections:
            print(f"   - {collection}")
            
            # Get collection info
            info = processor.vector_store.get_collection_info(collection)
            if info:
                print(f"     Points: {info.get('points_count', 'Unknown')}")
                print(f"     Status: {info.get('status', 'Unknown')}")
        
        return collections
        
    except Exception as e:
        print(f"❌ Error listing collections: {str(e)}")
        return None

def main():
    """Main example function"""
    print("🚀 Question Analysis Service Example")
    print("=" * 50)
    
    # Check environment
    print("🔍 Environment Check:")
    print(f"   GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Not set'}")
    print(f"   QDRANT_API_KEY: {'✅ Set' if os.getenv('QDRANT_API_KEY') else '❌ Not set'}")
    print(f"   GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    print(f"   BUCKET_NAME: {os.getenv('BUCKET_NAME', 'Not set')}")
    print()
    
    # List existing collections
    list_collections()
    
    # Example search queries
    search_queries = [
        "grammar errors in questions",
        "technical accuracy issues",
        "syllabus alignment problems",
        "marking scheme issues",
        "MCQ quality problems"
    ]
    
    print(f"\n🔍 Example searches:")
    for query in search_queries:
        search_analysis_results(query, limit=3)
    
    # Ask user if they want to run analysis
    print(f"\n❓ Would you like to analyze the extracted questions from GCS?")
    print("   This will process all JSON files in book_ip_sqp/extracted_questions/")
    print("   and store analysis results in Qdrant.")
    
    response = input("   Run analysis? (y/N): ").strip().lower()
    
    if response == 'y':
        analyze_extracted_questions()
    else:
        print("   Skipping analysis. You can run it later with:")
        print("   python question_analysis_service/cli_main.py gcs-folder book_ip_sqp/extracted_questions --verbose")

if __name__ == '__main__':
    main()
