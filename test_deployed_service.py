#!/usr/bin/env python3
"""
Test script for deployed PDF processing service
"""

import requests
import json
import time
import sys

def test_deployed_service(service_url):
    """Test the deployed PDF processing service"""
    
    print("🧪 Testing Deployed PDF Processing Service")
    print("=" * 50)
    print(f"Service URL: {service_url}")
    print()
    
    # Test data
    pdf_path = "gs://book-qc-cf-pdf-storage/book_ip_sqp.pdf"
    bucket_name = "book-qc-cf-pdf-storage"
    
    # Step 1: Health Check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{service_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False
    
    print()
    
    # Step 2: Test Complete Processing
    print("2. Testing complete PDF processing...")
    print(f"   PDF: {pdf_path}")
    print(f"   Bucket: {bucket_name}")
    
    try:
        data = {
            "pdf_path": pdf_path,
            "bucket_name": bucket_name
        }
        
        print("   Sending request...")
        response = requests.post(
            f"{service_url}/process",
            json=data,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Processing successful!")
            print(f"   Status: {result['status']}")
            print(f"   Book title: {result['analysis_result']['book_title']}")
            print(f"   Chapters found: {len(result['analysis_result']['chapters'])}")
            print(f"   Files created: {result['total_files']}")
            
            # Show split files
            print("\n   Split files:")
            for file_info in result['split_files']:
                print(f"     - {file_info['filename']} ({file_info['pages']}) -> {file_info['gcs_path']}")
            
            return True
        else:
            print(f"❌ Processing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Processing error: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_deployed_service.py <service_url>")
        print("Example: python test_deployed_service.py https://pdf-processor-xxx.run.app")
        sys.exit(1)
    
    service_url = sys.argv[1].rstrip('/')
    
    success = test_deployed_service(service_url)
    
    print()
    print("=" * 50)
    if success:
        print("🎉 All tests passed! Service is working correctly.")
    else:
        print("❌ Some tests failed. Check the logs above.")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
