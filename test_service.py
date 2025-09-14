#!/usr/bin/env python3
"""
Test script for PDF processing microservice
"""

import requests
import json
import sys
import time
from typing import Dict, Any

def test_health_endpoint(base_url: str) -> bool:
    """Test the health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_analyze_endpoint(base_url: str, pdf_path: str, bucket_name: str) -> Dict[str, Any]:
    """Test the analyze endpoint"""
    try:
        data = {
            "pdf_path": pdf_path,
            "bucket_name": bucket_name
        }
        
        response = requests.post(
            f"{base_url}/analyze",
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis successful: {result['status']}")
            return result
        else:
            print(f"❌ Analysis failed: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return {}

def test_split_endpoint(base_url: str, pdf_path: str, analysis_path: str, bucket_name: str) -> Dict[str, Any]:
    """Test the split endpoint"""
    try:
        data = {
            "pdf_path": pdf_path,
            "analysis_path": analysis_path,
            "bucket_name": bucket_name
        }
        
        response = requests.post(
            f"{base_url}/split",
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Splitting successful: {result['status']}")
            return result
        else:
            print(f"❌ Splitting failed: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Splitting error: {str(e)}")
        return {}

def test_process_endpoint(base_url: str, pdf_path: str, bucket_name: str) -> Dict[str, Any]:
    """Test the complete process endpoint"""
    try:
        data = {
            "pdf_path": pdf_path,
            "bucket_name": bucket_name
        }
        
        response = requests.post(
            f"{base_url}/process",
            json=data,
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Complete processing successful: {result['status']}")
            return result
        else:
            print(f"❌ Complete processing failed: {response.status_code} - {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Complete processing error: {str(e)}")
        return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_service.py <service_url> [pdf_path] [bucket_name]")
        print("Example: python test_service.py https://pdf-processor-xxx.run.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else "gs://your-bucket/sample.pdf"
    bucket_name = sys.argv[3] if len(sys.argv) > 3 else "your-bucket"
    
    print(f"Testing service at: {base_url}")
    print(f"PDF path: {pdf_path}")
    print(f"Bucket: {bucket_name}")
    print("-" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    health_ok = test_health_endpoint(base_url)
    if not health_ok:
        print("❌ Service is not healthy, stopping tests")
        sys.exit(1)
    
    print()
    
    # Test 2: Analyze endpoint
    print("2. Testing analyze endpoint...")
    analysis_result = test_analyze_endpoint(base_url, pdf_path, bucket_name)
    
    print()
    
    # Test 3: Split endpoint (if analysis was successful)
    if analysis_result and analysis_result.get('status') == 'success':
        print("3. Testing split endpoint...")
        analysis_path = analysis_result.get('analysis_gcs_path')
        if analysis_path:
            split_result = test_split_endpoint(base_url, pdf_path, analysis_path, bucket_name)
        else:
            print("❌ No analysis path found for splitting test")
    else:
        print("⚠️  Skipping split test due to analysis failure")
    
    print()
    
    # Test 4: Complete process endpoint
    print("4. Testing complete process endpoint...")
    process_result = test_process_endpoint(base_url, pdf_path, bucket_name)
    
    print()
    print("-" * 50)
    print("Test summary:")
    print(f"Health check: {'✅' if health_ok else '❌'}")
    print(f"Analysis: {'✅' if analysis_result.get('status') == 'success' else '❌'}")
    print(f"Complete process: {'✅' if process_result.get('status') == 'success' else '❌'}")

if __name__ == '__main__':
    main()
