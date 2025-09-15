#!/usr/bin/env python3
"""
Test script for Cloud Run Jobs
Demonstrates how to execute the new serverless job-based pipeline
"""

import subprocess
import sys
import json
import time
from typing import Dict, Any

def run_command(cmd: list) -> tuple:
    """Run a command and return result"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def execute_cloud_run_job(job_name: str, args: list, region: str = "us-central1") -> Dict[str, Any]:
    """Execute a Cloud Run Job with given arguments"""
    print(f"🚀 Executing Cloud Run Job: {job_name}")
    print(f"   Args: {' '.join(args)}")
    
    cmd = [
        "gcloud", "run", "jobs", "execute", job_name,
        "--region", region,
        "--wait"
    ] + [f"--args={arg}" for arg in args]
    
    print(f"Command: {' '.join(cmd)}")
    success, stdout, stderr = run_command(cmd)
    
    return {
        "success": success,
        "job_name": job_name,
        "args": args,
        "stdout": stdout,
        "stderr": stderr
    }

def test_pdf_analysis():
    """Test PDF analysis job"""
    print("\n" + "="*60)
    print("TEST 1: PDF Analysis")
    print("="*60)
    
    result = execute_cloud_run_job(
        "pdf-processor-job",
        [
            "analyze",
            "--pdf-path", "gs://book-qc-cf-pdf-storage/sample.pdf",
            "--bucket-name", "book-qc-cf-pdf-storage"
        ]
    )
    
    if result["success"]:
        print("✅ PDF Analysis job completed successfully")
    else:
        print("❌ PDF Analysis job failed")
        print(f"Error: {result['stderr']}")
    
    return result

def test_question_extraction():
    """Test question extraction job"""
    print("\n" + "="*60)
    print("TEST 2: Question Extraction")
    print("="*60)
    
    result = execute_cloud_run_job(
        "book-extractor-job",
        [
            "extract-questions",
            "--pdf-path", "gs://book-qc-cf-pdf-storage/sample_question_paper.pdf",
            "--subject", "computer_applications"
        ]
    )
    
    if result["success"]:
        print("✅ Question Extraction job completed successfully")
    else:
        print("❌ Question Extraction job failed")
        print(f"Error: {result['stderr']}")
    
    return result

def test_workflow_execution():
    """Test workflow execution"""
    print("\n" + "="*60)
    print("TEST 3: Workflow Execution")
    print("="*60)
    
    # Execute PDF processing workflow
    cmd = [
        "gcloud", "workflows", "run", "pdf-processing-workflow",
        "--data", json.dumps({"pdf_path": "gs://book-qc-cf-pdf-storage/sample.pdf"}),
        "--location", "us-central1"
    ]
    
    print(f"Executing workflow: {' '.join(cmd)}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ PDF Processing Workflow executed successfully")
        print(f"Execution ID: {stdout}")
    else:
        print("❌ Workflow execution failed")
        print(f"Error: {stderr}")
    
    return {"success": success, "stdout": stdout, "stderr": stderr}

def test_local_cli():
    """Test CLI applications locally"""
    print("\n" + "="*60)
    print("TEST 4: Local CLI Testing")
    print("="*60)
    
    # Test book extractor CLI locally
    print("Testing book extractor CLI...")
    cmd = [
        "python3", "book_extractor_service/cli_main.py",
        "get-subjects"
    ]
    
    success, stdout, stderr = run_command(cmd)
    if success:
        print("✅ Book extractor CLI working")
        try:
            result = json.loads(stdout)
            print(f"Available subjects: {result.get('subjects', [])}")
        except:
            print(f"Output: {stdout}")
    else:
        print("❌ Book extractor CLI failed")
        print(f"Error: {stderr}")
    
    # Test PDF processor CLI locally  
    print("\nTesting PDF processor CLI...")
    cmd = [
        "python3", "split_pdf_service/cli_main.py",
        "analyze",
        "--pdf-path", "split_pdf_service/test_pdf/book_ip_sqp.pdf"
    ]
    
    success, stdout, stderr = run_command(cmd)
    if success:
        print("✅ PDF processor CLI working")
    else:
        print("❌ PDF processor CLI failed")
        print(f"Error: {stderr}")

def show_job_status():
    """Show current job status"""
    print("\n" + "="*60)
    print("CURRENT JOB STATUS")
    print("="*60)
    
    # List Cloud Run Jobs
    cmd = ["gcloud", "run", "jobs", "list", "--region", "us-central1"]
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("Cloud Run Jobs:")
        print(stdout)
    else:
        print(f"Failed to list jobs: {stderr}")

def main():
    """Main test function"""
    print("🧪 Cloud Run Jobs Testing Suite")
    print("Testing the new serverless pipeline...")
    
    # Check if we're authenticated with gcloud
    cmd = ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"]
    success, stdout, stderr = run_command(cmd)
    
    if not success or not stdout:
        print("❌ Not authenticated with gcloud")
        print("Please run: gcloud auth login")
        sys.exit(1)
    
    print(f"✅ Authenticated as: {stdout}")
    
    # Show current job status
    show_job_status()
    
    # Run tests
    print("\n🚀 Starting tests...")
    
    # Test 1: Local CLI testing (doesn't require deployed jobs)
    test_local_cli()
    
    # Test 2: PDF Analysis (requires deployed pdf-processor-job)
    # test_pdf_analysis()
    
    # Test 3: Question Extraction (requires deployed book-extractor-job)  
    # test_question_extraction()
    
    # Test 4: Workflow Execution (requires deployed workflows)
    # test_workflow_execution()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("📝 Notes:")
    print("- Uncomment the job execution tests after deployment")
    print("- Jobs are now serverless and only run when needed")
    print("- No more idle costs from always-on Flask servers!")
    print("- Use 'gcloud run jobs execute' to run jobs manually")
    print("- Use 'gcloud workflows run' to execute workflows")

if __name__ == "__main__":
    main()
