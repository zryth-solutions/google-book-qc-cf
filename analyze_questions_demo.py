#!/usr/bin/env python3
"""
Demo script to analyze the extracted questions using the Question Analysis Service
This script demonstrates how to use the service with the existing Qdrant collection
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def main():
    """Main demo function"""
    print("🚀 Question Analysis Service Demo")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("question_analysis_service").exists():
        print("❌ Please run this script from the project root directory")
        print("   The question_analysis_service folder should be in the current directory")
        return
    
    # Check environment variables
    print("🔍 Checking environment...")
    required_vars = ['GEMINI_API_KEY', 'QDRANT_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\n💡 Please set the following environment variables:")
        for var in missing_vars:
            print(f"   export {var}=your_api_key_here")
        return
    
    print("✅ All required environment variables are set")
    
    # Set default values for optional variables
    os.environ.setdefault('GCP_PROJECT_ID', 'book-qc-cf')
    os.environ.setdefault('BUCKET_NAME', 'book-qc-cf-pdf-storage')
    os.environ.setdefault('QDRANT_URL', 'https://9becb4cf-82b6-456f-ae0c-d797c6c946cc.us-east4-0.gcp.cloud.qdrant.io')
    
    print(f"   GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID')}")
    print(f"   BUCKET_NAME: {os.getenv('BUCKET_NAME')}")
    print(f"   QDRANT_URL: {os.getenv('QDRANT_URL')}")
    
    print("\n🎯 Available options:")
    print("1. Analyze extracted questions from GCS")
    print("2. Search existing analysis results")
    print("3. List Qdrant collections")
    print("4. Run test suite")
    print("5. Start the service locally")
    
    choice = input("\nSelect an option (1-5): ").strip()
    
    if choice == '1':
        print("\n🔍 Analyzing extracted questions from GCS...")
        try:
            from question_analysis_service.example_usage import analyze_extracted_questions
            analyze_extracted_questions()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    elif choice == '2':
        query = input("Enter search query: ").strip()
        if query:
            try:
                from question_analysis_service.example_usage import search_analysis_results
                search_analysis_results(query)
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    elif choice == '3':
        try:
            from question_analysis_service.example_usage import list_collections
            list_collections()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    elif choice == '4':
        print("\n🧪 Running test suite...")
        try:
            from question_analysis_service.test_service import main as run_tests
            run_tests()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    elif choice == '5':
        print("\n🚀 Starting service locally...")
        print("   Service will be available at: http://localhost:8080")
        print("   Press Ctrl+C to stop")
        try:
            from question_analysis_service.main import app
            app.run(host='0.0.0.0', port=8080, debug=True)
        except KeyboardInterrupt:
            print("\n👋 Service stopped")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    else:
        print("❌ Invalid choice. Please select 1-5.")
    
    print("\n💡 For more options, use the CLI directly:")
    print("   python question_analysis_service/cli_main.py --help")

if __name__ == '__main__':
    main()
