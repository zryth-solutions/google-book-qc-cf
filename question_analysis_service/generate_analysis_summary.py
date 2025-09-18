#!/usr/bin/env python3
"""
Generate comprehensive analysis summary from batch processing results
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.gcp.bucket_manager import BucketManager

def load_analysis_results(gcs_path: str, bucket_manager: BucketManager) -> Dict[str, Any]:
    """Load analysis results from GCS"""
    try:
        # Download the analysis summary
        results = bucket_manager.download_json(gcs_path)
        if not results:
            raise ValueError(f"Failed to load analysis results from {gcs_path}")
        return results
    except Exception as e:
        raise RuntimeError(f"Error loading analysis results: {str(e)}")

def generate_comprehensive_summary(results: Dict[str, Any]) -> str:
    """Generate comprehensive summary from batch results"""
    
    total_files = results.get('total_files', 0)
    processed_files = results.get('processed_files', 0)
    failed_files = results.get('failed_files', 0)
    processing_date = results.get('processing_date', 'Unknown')
    folder_path = results.get('gcs_folder_path', results.get('folder_path', 'Unknown'))
    
    # Analyze individual results
    successful_results = [r for r in results.get('results', []) if r.get('status') == 'completed']
    failed_results = [r for r in results.get('results', []) if r.get('status') == 'failed']
    
    # Extract key metrics
    total_questions = sum(r.get('total_questions', 0) for r in successful_results)
    document_titles = [r.get('document_info', {}).get('title', 'Unknown') for r in successful_results]
    unique_titles = list(set(document_titles))
    
    # Generate summary
    summary = f"""# Question Analysis Batch Processing Summary

## Overview
- **Processing Date:** {processing_date}
- **Source Folder:** {folder_path}
- **Total Files Processed:** {total_files}
- **Successfully Analyzed:** {processed_files}
- **Failed:** {failed_files}
- **Success Rate:** {(processed_files/total_files*100):.1f}% if total_files > 0 else 0

## Analysis Statistics
- **Total Questions Analyzed:** {total_questions}
- **Unique Documents:** {len(unique_titles)}
- **Average Questions per Document:** {total_questions/len(successful_results) if successful_results else 0:.1f}

## Document Titles Analyzed
"""
    
    for i, title in enumerate(unique_titles, 1):
        summary += f"{i}. {title}\n"
    
    if successful_results:
        summary += f"""
## Successful Analyses
"""
        for result in successful_results:
            file_name = result.get('file_name', 'Unknown')
            questions = result.get('total_questions', 0)
            analysis_id = result.get('analysis_id', 'Unknown')
            gcs_path = result.get('gcs_report_path', 'Not stored in GCS')
            
            summary += f"""
### {file_name}
- **Questions:** {questions}
- **Analysis ID:** {analysis_id}
- **Report Location:** {gcs_path}
"""
    
    if failed_results:
        summary += f"""
## Failed Analyses
"""
        for result in failed_results:
            file_name = result.get('file_name', 'Unknown')
            error = result.get('error', 'Unknown error')
            
            summary += f"""
### {file_name}
- **Error:** {error}
"""
    
    summary += f"""
## Recommendations

### For Successful Analyses
- Review individual analysis reports for detailed findings
- Use the analysis IDs to search for specific results in Qdrant
- Consider implementing automated quality checks based on common issues found

### For Failed Analyses
- Check file format and structure for failed files
- Verify that JSON files contain required 'questions' array
- Review error messages for specific issues

## Next Steps
1. Review individual analysis reports for detailed findings
2. Implement quality improvements based on analysis results
3. Set up monitoring for automated analysis pipeline
4. Consider batch processing optimization for large datasets

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='Generate analysis summary from batch results')
    parser.add_argument('analysis_results_path', help='GCS path to analysis results JSON file')
    parser.add_argument('-o', '--output', help='Output file path for summary')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        # Initialize bucket manager
        bucket_manager = BucketManager(
            project_id=os.getenv('GCP_PROJECT_ID', 'book-qc-cf'),
            bucket_name=os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
        )
        
        if args.verbose:
            print(f"Loading analysis results from: {args.analysis_results_path}")
        
        # Load analysis results
        results = load_analysis_results(args.analysis_results_path, bucket_manager)
        
        if args.verbose:
            print(f"Loaded results for {results.get('total_files', 0)} files")
        
        # Generate comprehensive summary
        summary = generate_comprehensive_summary(results)
        
        # Save summary
        if args.output:
            output_path = args.output
        else:
            # Generate output path based on input
            base_name = Path(args.analysis_results_path).stem
            output_path = f"{base_name}_comprehensive_summary.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # Upload to GCS
        gcs_summary_path = f"{Path(args.analysis_results_path).parent}/comprehensive_summary.md"
        bucket_manager.upload_text(summary, gcs_summary_path, "text/markdown")
        
        print(f"✅ Comprehensive summary generated!")
        print(f"📄 Local file: {output_path}")
        print(f"☁️  GCS file: gs://{bucket_manager.bucket_name}/{gcs_summary_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
