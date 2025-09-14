#!/usr/bin/env python3
"""
Script to update workflow URLs with actual Cloud Run service URL after deployment
"""

import re
import sys
from pathlib import Path

def update_workflow_urls(service_url: str, workflow_file: str = "workflows/pdf_processing_workflow.yaml"):
    """Update workflow file with actual Cloud Run service URL"""
    
    if not service_url.startswith("https://"):
        print(f"Error: Service URL must start with 'https://', got: {service_url}")
        return False
    
    workflow_path = Path(workflow_file)
    if not workflow_path.exists():
        print(f"Error: Workflow file not found: {workflow_file}")
        return False
    
    # Read the workflow file
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # Replace placeholder URLs with actual service URL
    updated_content = re.sub(
        r'https://pdf-processor-xxx\.run\.app',
        service_url,
        content
    )
    
    # Write back the updated content
    with open(workflow_path, 'w') as f:
        f.write(updated_content)
    
    print(f"✅ Updated workflow URLs in {workflow_file}")
    print(f"   Service URL: {service_url}")
    
    return True

def get_service_url_from_gcloud():
    """Get the Cloud Run service URL using gcloud CLI"""
    import subprocess
    
    try:
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'pdf-processor',
            '--project=book-qc-cf',
            '--region=us-central1',
            '--format=value(status.url)'
        ], capture_output=True, text=True, check=True)
        
        url = result.stdout.strip()
        if url and url.startswith('https://'):
            return url
        else:
            print("Error: Could not get valid service URL from gcloud")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running gcloud command: {e}")
        return None
    except FileNotFoundError:
        print("Error: gcloud CLI not found. Please install Google Cloud CLI")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Service URL provided as argument
        service_url = sys.argv[1]
    else:
        # Try to get service URL from gcloud
        print("Getting service URL from gcloud...")
        service_url = get_service_url_from_gcloud()
        if not service_url:
            print("Usage: python3 update_workflow_urls.py <service_url>")
            print("   or: python3 update_workflow_urls.py  # (requires gcloud CLI)")
            sys.exit(1)
    
    success = update_workflow_urls(service_url)
    if success:
        print("🎉 Workflow URLs updated successfully!")
    else:
        sys.exit(1)
