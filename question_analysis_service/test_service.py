#!/usr/bin/env python3
"""
Test script for Question Analysis Service
Demonstrates usage of the service with sample data
"""

import os
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def create_sample_questions():
    """Create sample question data for testing"""
    sample_data = {
        "document_info": {
            "title": "Sample Question Paper - Computer Applications Class 10",
            "class": "10",
            "subject": "Computer Applications",
            "year": "2024"
        },
        "questions": [
            {
                "question_number": 1,
                "question_text": "What is the full form of CPU?",
                "section": "A",
                "marks": 1,
                "diagram_explain": None
            },
            {
                "question_number": 2,
                "question_text": "Which of the following is not a component of MS Word?",
                "section": "A",
                "marks": 1,
                "diagram_explain": None
            },
            {
                "question_number": 3,
                "question_text": "Explain the process of mail merge in MS Word with an example.",
                "section": "B",
                "marks": 3,
                "diagram_explain": "Draw a flowchart showing mail merge process"
            },
            {
                "question_number": 4,
                "question_text": "What are the different types of charts available in MS Excel?",
                "section": "B",
                "marks": 2,
                "diagram_explain": None
            },
            {
                "question_number": 5,
                "question_text": "Create a database table with fields: StudentID, Name, Class, Marks. Write SQL query to find students with marks > 80.",
                "section": "C",
                "marks": 4,
                "diagram_explain": "Show table structure and sample data"
            }
        ]
    }
    return sample_data

def test_single_file_analysis():
    """Test single file analysis"""
    print("🧪 Testing Single File Analysis...")
    
    try:
        from analyzer import CBSEQuestionAnalyzer
        
        # Create sample data
        sample_data = create_sample_questions()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f, indent=2)
            temp_file = f.name
        
        try:
            # Initialize analyzer (will use environment variables)
            analyzer = CBSEQuestionAnalyzer()
            
            # Analyze the file
            report, output_path = analyzer.analyze_question_paper(
                temp_file,
                verbose=True
            )
            
            print(f"✅ Analysis completed successfully!")
            print(f"📄 Report saved to: {output_path}")
            print(f"📊 Report preview:")
            print("-" * 50)
            print(report[:500] + "..." if len(report) > 500 else report)
            print("-" * 50)
            
        finally:
            # Clean up
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"❌ Error in single file analysis: {str(e)}")
        print("💡 Make sure to set GEMINI_API_KEY environment variable")

def test_batch_processing():
    """Test batch processing with multiple files"""
    print("\n🧪 Testing Batch Processing...")
    
    try:
        from batch_processor import BatchQuestionProcessor
        
        # Check environment variables
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not gemini_api_key:
            print("❌ GEMINI_API_KEY not set, skipping batch processing test")
            return
        
        if not qdrant_api_key:
            print("❌ QDRANT_API_KEY not set, skipping batch processing test")
            return
        
        # Create temporary directory with sample files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple sample files
            for i in range(3):
                sample_data = create_sample_questions()
                sample_data["document_info"]["title"] = f"Sample Paper {i+1}"
                
                file_path = temp_path / f"sample_paper_{i+1}.json"
                with open(file_path, 'w') as f:
                    json.dump(sample_data, f, indent=2)
            
            # Initialize processor
            processor = BatchQuestionProcessor(
                gemini_api_key=gemini_api_key,
                qdrant_api_key=qdrant_api_key,
                gcp_project_id=os.getenv('GCP_PROJECT_ID', 'book-qc-cf'),
                bucket_name=os.getenv('BUCKET_NAME', 'book-qc-cf-pdf-storage')
            )
            
            # Process the folder
            summary = processor.process_folder(
                folder_path=str(temp_path),
                file_pattern="*.json",
                batch_size=3,
                verbose=True
            )
            
            print(f"✅ Batch processing completed!")
            print(f"📊 Summary:")
            print(f"   Total files: {summary['total_files']}")
            print(f"   Processed: {summary['processed_files']}")
            print(f"   Failed: {summary['failed_files']}")
            
    except Exception as e:
        print(f"❌ Error in batch processing: {str(e)}")

def test_api_endpoints():
    """Test API endpoints (requires running service)"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        import requests
        
        # Check if service is running
        service_url = os.getenv('SERVICE_URL', 'http://localhost:8080')
        
        # Test health endpoint
        response = requests.get(f"{service_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
        
        # Test collections endpoint
        response = requests.get(f"{service_url}/collections", timeout=10)
        if response.status_code == 200:
            print("✅ Collections endpoint working")
            print(f"   Collections: {response.json()}")
        else:
            print(f"❌ Collections endpoint failed: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Service not running. Start with: python question_analysis_service/main.py")
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Question Analysis Service Test Suite")
    print("=" * 50)
    
    # Check environment
    print("🔍 Environment Check:")
    print(f"   GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Not set'}")
    print(f"   QDRANT_API_KEY: {'✅ Set' if os.getenv('QDRANT_API_KEY') else '❌ Not set'}")
    print(f"   GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    print(f"   BUCKET_NAME: {os.getenv('BUCKET_NAME', 'Not set')}")
    print()
    
    # Run tests
    test_single_file_analysis()
    test_batch_processing()
    test_api_endpoints()
    
    print("\n🎉 Test suite completed!")
    print("\n💡 To run the service locally:")
    print("   python question_analysis_service/main.py")
    print("\n💡 To use CLI:")
    print("   python question_analysis_service/cli_main.py --help")

if __name__ == '__main__':
    main()
