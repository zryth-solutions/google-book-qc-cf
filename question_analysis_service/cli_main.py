#!/usr/bin/env python3
"""
Question Analysis Service CLI
Command-line interface for analyzing question papers
"""

import os
import sys
import json
import argparse
from pathlib import Path
import logging

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from analyzer import CBSEQuestionAnalyzer
from batch_processor import BatchQuestionProcessor

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def analyze_single_file(args):
    """Analyze a single JSON file"""
    try:
        project_id = args.project_id or os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'book-qc-cf')
        analyzer = CBSEQuestionAnalyzer(project_id)
        
        report, output_path = analyzer.analyze_question_paper(
            args.input_file,
            args.output,
            args.batch_size,
            args.verbose
        )
        
        print(f"\n📋 ANALYSIS REPORT PREVIEW:")
        print("="*60)
        preview = report[:1000] + "..." if len(report) > 1000 else report
        print(preview)
        print("="*60)
        print(f"📄 Complete report: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def analyze_folder(args):
    """Analyze all JSON files in a folder"""
    try:
        # Get configuration
        project_id = args.project_id or os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'book-qc-cf')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_api_key:
            print("❌ Error: Please set QDRANT_API_KEY environment variable")
            sys.exit(1)
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            project_id=project_id,
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL'),
            bucket_name=os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage'),
            location=os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        )
        
        # Process folder
        summary = processor.process_folder(
            folder_path=args.folder_path,
            file_pattern=args.file_pattern,
            batch_size=args.batch_size,
            store_in_qdrant=args.store_in_qdrant,
            verbose=args.verbose
        )
        
        print(f"\n📊 BATCH PROCESSING SUMMARY:")
        print("="*60)
        print(f"📁 Folder: {summary['folder_path']}")
        print(f"📄 Total files: {summary['total_files']}")
        print(f"✅ Processed: {summary['processed_files']}")
        print(f"❌ Failed: {summary['failed_files']}")
        print(f"📅 Processing date: {summary['processing_date']}")
        
        if args.verbose:
            print(f"\n📋 DETAILED RESULTS:")
            for result in summary['results']:
                status_emoji = "✅" if result['status'] == 'completed' else "❌"
                print(f"{status_emoji} {result['file_name']}: {result['status']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def analyze_gcs_folder(args):
    """Analyze all JSON files in a GCS folder"""
    try:
        # Get configuration
        project_id = args.project_id or os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'book-qc-cf')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_api_key:
            print("❌ Error: Please set QDRANT_API_KEY environment variable")
            sys.exit(1)
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            project_id=project_id,
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL'),
            bucket_name=os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage'),
            location=os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        )
        
        # Process GCS folder
        summary = processor.process_gcs_folder(
            gcs_folder_path=args.gcs_folder_path,
            local_temp_dir=args.local_temp_dir,
            file_pattern=args.file_pattern,
            batch_size=args.batch_size,
            store_in_qdrant=args.store_in_qdrant,
            verbose=args.verbose
        )
        
        print(f"\n📊 GCS BATCH PROCESSING SUMMARY:")
        print("="*60)
        print(f"📁 GCS Folder: {summary['gcs_folder_path']}")
        print(f"📄 Total files: {summary['total_files']}")
        print(f"✅ Processed: {summary['processed_files']}")
        print(f"❌ Failed: {summary['failed_files']}")
        print(f"📅 Processing date: {summary['processing_date']}")
        
        if args.verbose:
            print(f"\n📋 DETAILED RESULTS:")
            for result in summary['results']:
                status_emoji = "✅" if result['status'] == 'completed' else "❌"
                print(f"{status_emoji} {result['file_name']}: {result['status']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def search_analysis(args):
    """Search analysis results"""
    try:
        # Get configuration
        project_id = args.project_id or os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'book-qc-cf')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_api_key:
            print("❌ Error: Please set QDRANT_API_KEY environment variable")
            sys.exit(1)
        
        # Initialize processor
        processor = BatchQuestionProcessor(
            project_id=project_id,
            qdrant_api_key=qdrant_api_key,
            qdrant_url=os.getenv('QDRANT_URL'),
            location=os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        )
        
        # Generate query embedding
        query_embedding = processor.embedding_generator.generate_single_embedding(args.query)
        
        if not query_embedding:
            print("❌ Error: Failed to generate query embedding")
            sys.exit(1)
        
        # Search in Qdrant
        results = processor.vector_store.search_similar(
            collection_name=processor.collection_name,
            query_embedding=query_embedding,
            limit=args.limit,
            score_threshold=args.score_threshold
        )
        
        print(f"\n🔍 SEARCH RESULTS FOR: '{args.query}'")
        print("="*60)
        
        if not results:
            print("No results found.")
        else:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Score: {result['score']:.3f}")
                print(f"   File: {result['metadata'].get('file_name', 'Unknown')}")
                print(f"   Analysis ID: {result['metadata'].get('analysis_id', 'Unknown')}")
                print(f"   Questions: {result['metadata'].get('total_questions', 'Unknown')}")
                print(f"   Content preview: {result['content'][:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="CBSE Question Analysis Service CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  python cli_main.py single-file questions.json -o report.md -v
  
  # Analyze local folder
  python cli_main.py folder ./question_files --verbose
  
  # Analyze GCS folder
  python cli_main.py gcs-folder book_ip_sqp/extracted_questions --verbose
  
  # Search analysis results
  python cli_main.py search "grammar errors" --limit 5
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Show detailed processing information')
    parser.add_argument('-p', '--project-id', 
                       help='GCP Project ID (or set GOOGLE_CLOUD_PROJECT env var)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single file analysis
    single_parser = subparsers.add_parser('single-file', help='Analyze a single JSON file')
    single_parser.add_argument('input_file', help='Path to questions JSON file')
    single_parser.add_argument('-o', '--output', help='Output report file path')
    single_parser.add_argument('-b', '--batch-size', type=int, default=5, 
                              help='Questions per batch for detailed analysis (default: 5)')
    
    # Folder analysis
    folder_parser = subparsers.add_parser('folder', help='Analyze all JSON files in a folder')
    folder_parser.add_argument('folder_path', help='Path to folder containing JSON files')
    folder_parser.add_argument('--file-pattern', default='*.json', 
                              help='File pattern to match (default: *.json)')
    folder_parser.add_argument('-b', '--batch-size', type=int, default=5, 
                              help='Questions per batch for detailed analysis (default: 5)')
    folder_parser.add_argument('--no-qdrant', action='store_true', 
                              help='Do not store results in Qdrant')
    
    # GCS folder analysis
    gcs_parser = subparsers.add_parser('gcs-folder', help='Analyze all JSON files in a GCS folder')
    gcs_parser.add_argument('gcs_folder_path', help='GCS folder path (e.g., book_ip_sqp/extracted_questions/)')
    gcs_parser.add_argument('--local-temp-dir', default='/tmp/question_analysis',
                           help='Local temporary directory for downloads (default: /tmp/question_analysis)')
    gcs_parser.add_argument('--file-pattern', default='*.json', 
                           help='File pattern to match (default: *.json)')
    gcs_parser.add_argument('-b', '--batch-size', type=int, default=5, 
                           help='Questions per batch for detailed analysis (default: 5)')
    gcs_parser.add_argument('--no-qdrant', action='store_true', 
                           help='Do not store results in Qdrant')
    
    # Search analysis
    search_parser = subparsers.add_parser('search', help='Search analysis results')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, 
                              help='Maximum number of results (default: 10)')
    search_parser.add_argument('--score-threshold', type=float, default=0.7, 
                              help='Minimum similarity score (default: 0.7)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if args.command == 'single-file':
        analyze_single_file(args)
    elif args.command == 'folder':
        args.store_in_qdrant = not args.no_qdrant
        analyze_folder(args)
    elif args.command == 'gcs-folder':
        args.store_in_qdrant = not args.no_qdrant
        analyze_gcs_folder(args)
    elif args.command == 'search':
        search_analysis(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
