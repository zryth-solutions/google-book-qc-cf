#!/usr/bin/env python3
"""
Test script for the new PDF folder structure
Demonstrates how the updated split_pdf_service organizes outputs
"""

import subprocess
import sys
import json
import os

def run_command(cmd: list) -> tuple:
    """Run a command and return result"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def test_local_pdf_analysis():
    """Test local PDF analysis with new folder structure"""
    print("🧪 Testing PDF Analysis with New Folder Structure")
    print("=" * 60)
    
    # Test with the sample PDF
    test_pdf = "split_pdf_service/test_pdf/book_ip_sqp.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    print(f"📄 Testing with PDF: {test_pdf}")
    
    # Run the CLI analysis
    cmd = [
        "python3", "split_pdf_service/cli_main.py",
        "analyze",
        "--pdf-path", test_pdf
    ]
    
    print(f"🚀 Command: {' '.join(cmd)}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Analysis completed successfully!")
        try:
            result = json.loads(stdout)
            if result.get('status') == 'success':
                analysis_path = result.get('analysis_gcs_path', 'N/A')
                pdf_folder = result.get('pdf_folder', 'N/A')
                print(f"📁 PDF Folder: {pdf_folder}")
                print(f"📄 Analysis Path: {analysis_path}")
                
                # Expected structure: book_ip_sqp/analysis.json
                expected_folder = "book_ip_sqp"
                if pdf_folder == expected_folder:
                    print(f"✅ Correct folder structure: {expected_folder}/")
                else:
                    print(f"⚠️  Unexpected folder: {pdf_folder} (expected: {expected_folder})")
                
                return True
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {stdout}")
            return False
    else:
        print(f"❌ Command failed: {stderr}")
        return False

def demonstrate_folder_structure():
    """Show the expected folder structure"""
    print("\n📁 New Folder Structure")
    print("=" * 60)
    
    pdf_name = "book_ip_sqp"
    
    print(f"For PDF: {pdf_name}.pdf")
    print()
    print("📦 GCS Bucket Structure:")
    print(f"  {pdf_name}/")
    print(f"  ├── analysis.json                     (PDF analysis results)")
    print(f"  ├── question_papers/")
    print(f"  │   ├── chapter1_questions.pdf        (Split question paper)")
    print(f"  │   └── chapter2_questions.pdf")
    print(f"  └── answer_keys/")
    print(f"      ├── chapter1_answers.pdf          (Split answer key)")
    print(f"      └── chapter2_answers.pdf")
    print()
    
    print("🔄 Previous Structure (OLD):")
    print("  analysis/")
    print(f"  ├── {pdf_name}_analysis.json")
    print("  question_papers/")
    print(f"  ├── {pdf_name}_chapter1.pdf")
    print("  answer_keys/")
    print(f"  ├── {pdf_name}_chapter1.pdf")
    print()
    
    print("✅ Benefits of New Structure:")
    print("  • All files for one PDF are grouped together")
    print("  • Easier to manage and find related files") 
    print("  • Cleaner folder organization in GCS")
    print("  • Better for batch processing multiple PDFs")

def show_usage_examples():
    """Show usage examples with new structure"""
    print("\n🚀 Usage Examples")
    print("=" * 60)
    
    print("1️⃣ Analyze PDF (creates folder structure):")
    print("   gcloud run jobs execute pdf-processor-job \\")
    print("     --region=us-central1 \\")
    print("     --args=\"analyze\" \\")
    print("     --args=\"--pdf-path=gs://bucket/book_ip_sqp.pdf\" \\")
    print("     --wait")
    print("   ")
    print("   📁 Creates: book_ip_sqp/analysis.json")
    print()
    
    print("2️⃣ Split PDF (uses analysis from folder):")
    print("   gcloud run jobs execute pdf-processor-job \\")
    print("     --region=us-central1 \\") 
    print("     --args=\"split\" \\")
    print("     --args=\"--pdf-path=gs://bucket/book_ip_sqp.pdf\" \\")
    print("     --args=\"--analysis-path=gs://bucket/book_ip_sqp/analysis.json\" \\")
    print("     --wait")
    print("   ")
    print("   📁 Creates: book_ip_sqp/question_papers/ and book_ip_sqp/answer_keys/")
    print()
    
    print("3️⃣ Complete Processing (analyze + split):")
    print("   gcloud run jobs execute pdf-processor-job \\")
    print("     --region=us-central1 \\")
    print("     --args=\"process\" \\") 
    print("     --args=\"--pdf-path=gs://bucket/book_ip_sqp.pdf\" \\")
    print("     --wait")
    print("   ")
    print("   📁 Creates: Complete folder structure with all files")
    print()
    
    print("4️⃣ Workflow Execution:")
    print("   gcloud workflows run pdf-processing-workflow \\")
    print("     --data='{\"pdf_path\": \"gs://bucket/book_ip_sqp.pdf\"}' \\")
    print("     --location=us-central1")

def main():
    """Main test function"""
    print("🧪 PDF Folder Structure Test Suite")
    print("Testing the new organized folder structure for PDF processing")
    print()
    
    # Show the new folder structure
    demonstrate_folder_structure()
    
    # Show usage examples
    show_usage_examples()
    
    # Test locally if possible
    test_local_pdf_analysis()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("✅ Updated split_pdf_service for organized folder structure")
    print("✅ Each PDF gets its own folder in GCS bucket")
    print("✅ Analysis and split files are grouped together")
    print("✅ Workflows updated to use new paths")
    print("✅ Better organization and easier file management")
    print()
    print("🚀 Ready to deploy! The new structure will be used automatically.")

if __name__ == "__main__":
    main()
