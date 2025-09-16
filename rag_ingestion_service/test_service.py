#!/usr/bin/env python3
"""
Test script for Markdown Converter Service
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return success, stdout, stderr"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_local_cli():
    """Test CLI locally"""
    print("\n" + "="*60)
    print("TEST: Local CLI Test")
    print("="*60)
    
    # Set environment variables for testing
    os.environ['PROJECT_ID'] = 'book-qc-cf'
    os.environ['BUCKET_NAME'] = 'llm-books'
    os.environ['REGION'] = 'us-central1'
    os.environ['MARKER_API_KEY'] = 'test-key'
    os.environ['QDRANT_API_KEY'] = 'test-key'
    os.environ['QDRANT_URL'] = 'https://qdrant.tech'
    
    # Test help command
    cmd = "python cli_main.py --help"
    print(f"Running: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ CLI help command works")
    else:
        print("❌ CLI help command failed")
        print(f"Error: {stderr}")
    
    return success

def test_workflow_deployment():
    """Test workflow deployment"""
    print("\n" + "="*60)
    print("TEST: Workflow Deployment")
    print("="*60)
    
    # Deploy workflow
    cmd = f"gcloud workflows deploy rag-ingestion-workflow --source=rag_ingestion_workflow.yaml --location=us-central1 --project=book-qc-cf"
    print(f"Running: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Workflow deployed successfully")
        print(f"Output: {stdout}")
    else:
        print("❌ Workflow deployment failed")
        print(f"Error: {stderr}")
    
    return success

def test_workflow_execution():
    """Test workflow execution"""
    print("\n" + "="*60)
    print("TEST: Workflow Execution")
    print("="*60)
    
    # Execute workflow
    cmd = f"gcloud workflows execute rag-ingestion-workflow --location=us-central1 --data='{{\"pdf_path\":\"gs://book-qc-cf-pdf-storage/book_ip_sqp.pdf\",\"book_name\":\"Test Book\"}}' --project=book-qc-cf"
    print(f"Running: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Workflow executed successfully")
        print(f"Execution ID: {stdout}")
    else:
        print("❌ Workflow execution failed")
        print(f"Error: {stderr}")
    
    return success

def main():
    """Main test function"""
    print("🧪 Testing RAG Ingestion Service")
    
    # Change to service directory
    os.chdir(Path(__file__).parent)
    
    # Run tests
    tests = [
        ("Local CLI", test_local_cli),
        ("Workflow Deployment", test_workflow_deployment),
        ("Workflow Execution", test_workflow_execution)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
