#!/usr/bin/env python3
"""
Setup script for PDF processing microservice
"""

import os
import sys
import subprocess
import argparse
import yaml
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_prerequisites() -> bool:
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    tools = {
        'gcloud': 'Google Cloud SDK',
        'docker': 'Docker',
        'python3': 'Python 3'
    }
    
    all_good = True
    for tool, name in tools.items():
        if run_command(f"which {tool}", f"Checking {name}"):
            continue
        else:
            print(f"❌ {name} not found. Please install it first.")
            all_good = False
    
    return all_good

def setup_gcp_project(project_id: str, region: str, bucket_name: str) -> bool:
    """Set up GCP project and resources"""
    print(f"🚀 Setting up GCP project: {project_id}")
    
    commands = [
        (f"gcloud config set project {project_id}", "Setting project"),
        (f"gcloud services enable run.googleapis.com", "Enabling Cloud Run API"),
        (f"gcloud services enable workflows.googleapis.com", "Enabling Workflows API"),
        (f"gcloud services enable storage.googleapis.com", "Enabling Storage API"),
        (f"gcloud services enable artifactregistry.googleapis.com", "Enabling Artifact Registry API"),
        (f"gsutil mb gs://{bucket_name}", "Creating GCS bucket"),
        (f"gcloud artifacts repositories create pdf-processor --repository-format=docker --location={region}", "Creating Artifact Registry repository")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def update_config(project_id: str, region: str, bucket_name: str) -> bool:
    """Update configuration files with provided values"""
    print("📝 Updating configuration files...")
    
    # Update config.yaml
    config_file = Path("config.yaml")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        config['gcp']['project_id'] = project_id
        config['gcp']['region'] = region
        config['gcp']['bucket_name'] = bucket_name
        config['environment']['PROJECT_ID'] = project_id
        config['environment']['BUCKET_NAME'] = bucket_name
        config['environment']['REGION'] = region
        config['cloud_run']['image_uri'] = f"{region}-docker.pkg.dev/{project_id}/pdf-processor/pdf-processor:latest"
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print("✅ Updated config.yaml")
    
    # Update GitHub Actions workflow
    workflow_file = Path(".github/workflows/deploy.yml")
    if workflow_file.exists():
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        content = content.replace("your-project-id", project_id)
        content = content.replace("your-bucket-name", bucket_name)
        
        with open(workflow_file, 'w') as f:
            content = f.write(content)
        
        print("✅ Updated GitHub Actions workflow")
    
    return True

def create_service_account() -> bool:
    """Create service account for GitHub Actions"""
    print("🔐 Creating service account for GitHub Actions...")
    
    commands = [
        ("gcloud iam service-accounts create pdf-processor-sa --display-name='PDF Processor Service Account'", "Creating service account"),
        ("gcloud projects add-iam-policy-binding $(gcloud config get-value project) --member='serviceAccount:pdf-processor-sa@$(gcloud config get-value project).iam.gserviceaccount.com' --role='roles/run.admin'", "Adding Cloud Run Admin role"),
        ("gcloud projects add-iam-policy-binding $(gcloud config get-value project) --member='serviceAccount:pdf-processor-sa@$(gcloud config get-value project).iam.gserviceaccount.com' --role='roles/storage.admin'", "Adding Storage Admin role"),
        ("gcloud projects add-iam-policy-binding $(gcloud config get-value project) --member='serviceAccount:pdf-processor-sa@$(gcloud config get-value project).iam.gserviceaccount.com' --role='roles/workflows.admin'", "Adding Workflows Admin role"),
        ("gcloud projects add-iam-policy-binding $(gcloud config get-value project) --member='serviceAccount:pdf-processor-sa@$(gcloud config get-value project).iam.gserviceaccount.com' --role='roles/artifactregistry.admin'", "Adding Artifact Registry Admin role"),
        ("gcloud iam service-accounts keys create pdf-processor-sa-key.json --iam-account=pdf-processor-sa@$(gcloud config get-value project).iam.gserviceaccount.com", "Creating service account key")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    print("✅ Service account created. Key saved as pdf-processor-sa-key.json")
    print("🔑 Add this key as GCP_SA_KEY secret in your GitHub repository")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Set up PDF processing microservice')
    parser.add_argument('--project-id', default='book-qc-cf', help='GCP Project ID')
    parser.add_argument('--region', default='us-central1', help='GCP Region')
    parser.add_argument('--bucket-name', default='book-qc-cf-pdf-storage', help='GCS Bucket name')
    parser.add_argument('--skip-prereq', action='store_true', help='Skip prerequisite checks')
    parser.add_argument('--skip-gcp', action='store_true', help='Skip GCP setup')
    parser.add_argument('--skip-sa', action='store_true', help='Skip service account creation')
    
    args = parser.parse_args()
    
    print("🚀 PDF Processing Microservice Setup")
    print("=" * 40)
    
    # Check prerequisites
    if not args.skip_prereq:
        if not check_prerequisites():
            print("❌ Prerequisites check failed. Please install required tools.")
            sys.exit(1)
    
    # Set up GCP project
    if not args.skip_gcp:
        if not setup_gcp_project(args.project_id, args.region, args.bucket_name):
            print("❌ GCP setup failed.")
            sys.exit(1)
    
    # Update configuration files
    if not update_config(args.project_id, args.region, args.bucket_name):
        print("❌ Configuration update failed.")
        sys.exit(1)
    
    # Create service account
    if not args.skip_sa:
        if not create_service_account():
            print("❌ Service account creation failed.")
            sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Add the service account key (pdf-processor-sa-key.json) as GCP_SA_KEY secret in GitHub")
    print("2. Add BUCKET_NAME secret in GitHub with your bucket name")
    print("3. Push your code to trigger the GitHub Actions deployment")
    print("4. Or run manual deployment: python deploy.py --project-id <project-id> --image-uri <image-uri> --bucket-name <bucket-name>")

if __name__ == '__main__':
    main()
