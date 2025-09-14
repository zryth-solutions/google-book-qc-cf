#!/usr/bin/env python3
"""
Verification script for PDF processing microservice setup
"""

import subprocess
import json
import sys

def run_command(command, description):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True, result.stdout
        else:
            print(f"❌ {description}: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False, str(e)

def check_project():
    """Check if project is set correctly"""
    success, output = run_command("gcloud config get-value project", "Checking current project")
    if success and "book-qc-cf" in output:
        return True
    else:
        print("⚠️  Project not set to book-qc-cf")
        return False

def check_apis():
    """Check if required APIs are enabled"""
    print("\n🔧 Checking API status...")
    
    apis = [
        "run.googleapis.com",
        "workflows.googleapis.com", 
        "storage.googleapis.com",
        "artifactregistry.googleapis.com",
        "cloudbuild.googleapis.com"
    ]
    
    all_enabled = True
    for api in apis:
        success, output = run_command(f"gcloud services list --enabled --filter='name:{api}'", f"Checking {api}")
        if not success or api not in output:
            print(f"❌ {api} not enabled")
            all_enabled = False
        else:
            print(f"✅ {api} enabled")
    
    return all_enabled

def check_bucket():
    """Check if GCS bucket exists"""
    success, output = run_command("gsutil ls gs://book-qc-cf-pdf-storage", "Checking GCS bucket")
    return success

def check_artifact_registry():
    """Check if Artifact Registry repository exists"""
    success, output = run_command("gcloud artifacts repositories list --location=us-central1 --filter='name:pdf-processor'", "Checking Artifact Registry")
    return success and "pdf-processor" in output

def check_service_account():
    """Check if service account exists"""
    success, output = run_command("gcloud iam service-accounts list --filter='email:pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com'", "Checking service account")
    return success and "pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com" in output

def check_billing():
    """Check if billing is enabled"""
    success, output = run_command("gcloud billing projects describe book-qc-cf", "Checking billing status")
    if success and "billingEnabled: true" in output:
        return True
    else:
        print("⚠️  Billing may not be enabled")
        return False

def main():
    print("🔍 PDF Processing Microservice Setup Verification")
    print("=" * 50)
    
    # Check project
    print("\n📋 Checking project configuration...")
    project_ok = check_project()
    
    # Check billing
    print("\n💳 Checking billing status...")
    billing_ok = check_billing()
    
    if not billing_ok:
        print("\n⚠️  BILLING NOT ENABLED")
        print("Please enable billing for project 'book-qc-cf' before proceeding.")
        print("Go to: https://console.cloud.google.com/billing")
        return
    
    # Check APIs
    apis_ok = check_apis()
    
    # Check resources
    print("\n🪣 Checking GCS bucket...")
    bucket_ok = check_bucket()
    
    print("\n📦 Checking Artifact Registry...")
    registry_ok = check_artifact_registry()
    
    print("\n🔐 Checking service account...")
    sa_ok = check_service_account()
    
    # Summary
    print("\n📊 Setup Status Summary:")
    print("=" * 30)
    print(f"Project: {'✅' if project_ok else '❌'}")
    print(f"Billing: {'✅' if billing_ok else '❌'}")
    print(f"APIs: {'✅' if apis_ok else '❌'}")
    print(f"GCS Bucket: {'✅' if bucket_ok else '❌'}")
    print(f"Artifact Registry: {'✅' if registry_ok else '❌'}")
    print(f"Service Account: {'✅' if sa_ok else '❌'}")
    
    if all([project_ok, billing_ok, apis_ok, bucket_ok, registry_ok, sa_ok]):
        print("\n🎉 All resources are set up correctly!")
        print("\nNext steps:")
        print("1. Add GitHub secrets (GCP_SA_KEY, BUCKET_NAME)")
        print("2. Push code to trigger deployment")
        print("3. Test the service")
    else:
        print("\n⚠️  Some resources are missing. Run ./setup_gcp_resources.sh to complete setup.")
        
        if not billing_ok:
            print("\n🔴 CRITICAL: Enable billing first!")
        elif not apis_ok:
            print("\n🟡 Run: gcloud services enable run.googleapis.com workflows.googleapis.com storage.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com")
        elif not bucket_ok:
            print("\n🟡 Run: gsutil mb gs://book-qc-cf-pdf-storage")
        elif not registry_ok:
            print("\n🟡 Run: gcloud artifacts repositories create pdf-processor --repository-format=docker --location=us-central1")
        elif not sa_ok:
            print("\n🟡 Run: gcloud iam service-accounts create pdf-processor-sa --display-name='PDF Processor Service Account'")

if __name__ == '__main__':
    main()
