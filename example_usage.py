#!/usr/bin/env python3
"""
Example usage of PDF processing microservice
"""

import requests
import json
import time

def example_usage():
    """Example of how to use the PDF processing service"""
    
    # Configuration
    SERVICE_URL = "https://pdf-processor-xxx.run.app"  # Replace with your actual service URL
    PDF_PATH = "gs://book-qc-cf-pdf-storage/sample.pdf"  # Replace with your PDF path
    BUCKET_NAME = "book-qc-cf-pdf-storage"  # Replace with your bucket name
    
    print("📚 PDF Processing Microservice Example")
    print("=" * 40)
    
    # Step 1: Health Check
    print("\n1. Checking service health...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Service is healthy")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error checking service health: {str(e)}")
        return
    
    # Step 2: Analyze PDF
    print(f"\n2. Analyzing PDF: {PDF_PATH}")
    try:
        analyze_data = {
            "pdf_path": PDF_PATH,
            "bucket_name": BUCKET_NAME
        }
        
        response = requests.post(
            f"{SERVICE_URL}/analyze",
            json=analyze_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF analysis completed")
            print(f"   Book title: {result['analysis_result']['book_title']}")
            print(f"   Chapters found: {len(result['analysis_result']['chapters'])}")
            print(f"   Analysis saved to: {result['analysis_gcs_path']}")
            
            # Show first few chapters
            chapters = result['analysis_result']['chapters']
            print("\n   First few chapters:")
            for i, chapter in enumerate(chapters[:3]):
                print(f"     {i+1}. {chapter['chapter_name']} (pages {chapter['chapter_start_page_number']}-{chapter['chapter_end_page_number']})")
            
        else:
            print(f"❌ PDF analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error analyzing PDF: {str(e)}")
        return
    
    # Step 3: Split PDF
    print(f"\n3. Splitting PDF...")
    try:
        split_data = {
            "pdf_path": PDF_PATH,
            "analysis_path": result['analysis_gcs_path'],
            "bucket_name": BUCKET_NAME
        }
        
        response = requests.post(
            f"{SERVICE_URL}/split",
            json=split_data,
            timeout=120
        )
        
        if response.status_code == 200:
            split_result = response.json()
            print("✅ PDF splitting completed")
            print(f"   Files created: {split_result['total_files']}")
            
            # Show split files
            print("\n   Split files:")
            for file_info in split_result['split_files']:
                print(f"     - {file_info['filename']} ({file_info['pages']}) -> {file_info['gcs_path']}")
            
        else:
            print(f"❌ PDF splitting failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error splitting PDF: {str(e)}")
        return
    
    # Step 4: Complete Processing (Alternative approach)
    print(f"\n4. Alternative: Complete processing in one step...")
    try:
        process_data = {
            "pdf_path": PDF_PATH,
            "bucket_name": BUCKET_NAME
        }
        
        response = requests.post(
            f"{SERVICE_URL}/process",
            json=process_data,
            timeout=180
        )
        
        if response.status_code == 200:
            process_result = response.json()
            print("✅ Complete processing successful")
            print(f"   Total files created: {process_result['total_files']}")
        else:
            print(f"❌ Complete processing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in complete processing: {str(e)}")
    
    print("\n🎉 Example completed!")

def test_workflow_execution():
    """Example of how to execute the workflow"""
    print("\n🔄 Workflow Execution Example")
    print("=" * 30)
    
    # This would typically be done via gcloud CLI or Workflow API
    workflow_command = """
    gcloud workflows executions create pdf-processing-workflow \\
        --location=us-central1 \\
        --argument='{
            "pdf_path": "gs://your-bucket/sample.pdf",
            "bucket_name": "your-bucket",
            "project_id": "your-project-id"
        }'
    """
    
    print("To execute the workflow, run:")
    print(workflow_command)
    
    print("\nTo check workflow status:")
    print("gcloud workflows executions list --location=us-central1")
    
    print("\nTo view workflow logs:")
    print("gcloud logging read 'resource.type=workflow_execution' --limit=10")

if __name__ == '__main__':
    print("Choose an example:")
    print("1. Service API usage")
    print("2. Workflow execution")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        example_usage()
    elif choice == "2":
        test_workflow_execution()
    else:
        print("Invalid choice. Running service API example...")
        example_usage()
