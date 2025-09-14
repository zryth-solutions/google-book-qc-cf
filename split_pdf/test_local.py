#!/usr/bin/env python3
"""
Local test script for PDF processing
"""

import json
import os
from analyze_pdf import PDFAnalyzer
from split_pdf import PDFSplitter

def test_pdf_processing():
    """Test PDF analysis and splitting locally"""
    
    pdf_path = "test_pdf/book_ip_sqp.pdf"
    output_dir = "test_output"
    
    print("🧪 Testing PDF Processing Locally")
    print("=" * 40)
    
    # Step 1: Analyze PDF
    print("\n1. Analyzing PDF...")
    analyzer = PDFAnalyzer()
    analysis_result = analyzer.analyze_pdf(pdf_path)
    
    print(f"✅ Analysis completed!")
    print(f"   Book title: {analysis_result['book_title']}")
    print(f"   Total pages: {analysis_result['book_end_page']}")
    print(f"   Chapters found: {len(analysis_result['chapters'])}")
    print(f"   Confidence score: {analysis_result['confidence_score']}")
    
    # Show chapters with filenames
    print("\n   Chapters with filenames:")
    for i, chapter in enumerate(analysis_result['chapters']):
        if 'pdf_filename' in chapter:
            print(f"     {i+1}. {chapter['chapter_name']} -> {chapter['pdf_filename']} ({chapter['pdf_folder']})")
        else:
            print(f"     {i+1}. {chapter['chapter_name']} -> (no filename)")
    
    # Step 2: Split PDF
    print(f"\n2. Splitting PDF...")
    splitter = PDFSplitter()
    split_files = splitter.split_pdf_by_json(pdf_path, analysis_result, output_dir)
    
    print(f"✅ Splitting completed!")
    print(f"   Files created: {len(split_files)}")
    
    # Show split files
    print("\n   Split files:")
    for file_info in split_files:
        print(f"     - {file_info['filename']} ({file_info['pages']}) -> {file_info['path']}")
    
    # Step 3: Save analysis JSON
    analysis_file = os.path.join(output_dir, "analysis.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis saved to: {analysis_file}")
    print(f"\n🎉 Local testing completed successfully!")
    
    return analysis_result, split_files

if __name__ == '__main__':
    test_pdf_processing()
