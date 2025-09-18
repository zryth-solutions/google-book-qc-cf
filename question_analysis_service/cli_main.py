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

# Search functionality removed - analysis results are stored in GCS only

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
    
    # GCS folder analysis
    gcs_parser = subparsers.add_parser('gcs-folder', help='Analyze all JSON files in a GCS folder')
    gcs_parser.add_argument('gcs_folder_path', help='GCS folder path (e.g., book_ip_sqp/extracted_questions/)')
    gcs_parser.add_argument('--local-temp-dir', default='/tmp/question_analysis',
                           help='Local temporary directory for downloads (default: /tmp/question_analysis)')
    gcs_parser.add_argument('--file-pattern', default='*.json', 
                           help='File pattern to match (default: *.json)')
    gcs_parser.add_argument('-b', '--batch-size', type=int, default=5, 
                           help='Questions per batch for detailed analysis (default: 5)')
    
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
        analyze_folder(args)
    elif args.command == 'gcs-folder':
        analyze_gcs_folder(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
