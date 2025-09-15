#!/usr/bin/env python3
"""
Script to update book extractor workflow URLs after Cloud Run deployment
"""

import subprocess
import json
import sys
import os

def get_cloud_run_url(service_name, project_id, region):
    """Get the Cloud Run service URL"""
    try:
        cmd = [
            'gcloud', 'run', 'services', 'describe', service_name,
            '--region', region,
            '--project', project_id,
            '--format', 'value(status.url)'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting Cloud Run URL: {e}")
        return None

def update_workflow_file(workflow_file, new_url):
    """Update workflow file with new Cloud Run URL"""
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        # Replace placeholder URLs
        updated_content = content.replace(
            'https://book-extractor-xxx.run.app',
            new_url
        )
        
        with open(workflow_file, 'w') as f:
            f.write(updated_content)
        
        print(f"Updated {workflow_file} with URL: {new_url}")
        return True
    except Exception as e:
        print(f"Error updating workflow file: {e}")
        return False

def main():
    # Configuration
    PROJECT_ID = 'book-qc-cf'
    REGION = 'us-central1'
    SERVICE_NAME = 'book-extractor'
    WORKFLOW_FILE = 'workflows/book_extraction_workflow.yaml'
    
    print(f"Updating book extractor workflow URLs...")
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print(f"Service: {SERVICE_NAME}")
    
    # Get Cloud Run URL
    print("Getting Cloud Run service URL...")
    cloud_run_url = get_cloud_run_url(SERVICE_NAME, PROJECT_ID, REGION)
    
    if not cloud_run_url:
        print("Failed to get Cloud Run URL")
        sys.exit(1)
    
    print(f"Cloud Run URL: {cloud_run_url}")
    
    # Update workflow file
    print("Updating workflow file...")
    if update_workflow_file(WORKFLOW_FILE, cloud_run_url):
        print("Workflow file updated successfully")
    else:
        print("Failed to update workflow file")
        sys.exit(1)
    
    print("Book extractor workflow URL update completed!")

if __name__ == '__main__':
    main()
