#!/usr/bin/env python3
"""
Deployment script for PDF processing microservice
Deploys Cloud Run service and Workflow
"""

import os
import sys
import argparse
import logging
from typing import Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.gcp.cloud_run_manager import CloudRunManager
from utils.gcp.workflow_manager import WorkflowManager
from utils.gcp.bucket_manager import BucketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deploy_cloud_run_service(
    project_id: str,
    region: str,
    service_name: str,
    image_uri: str,
    bucket_name: str
) -> bool:
    """Deploy Cloud Run service"""
    try:
        cloud_run_manager = CloudRunManager(project_id, region)
        
        env_vars = {
            'PROJECT_ID': project_id,
            'BUCKET_NAME': bucket_name,
            'REGION': region
        }
        
        success = cloud_run_manager.deploy_service(
            service_name=service_name,
            image_uri=image_uri,
            port=8080,
            memory="2Gi",
            cpu="2",
            max_instances=10,
            min_instances=0,
            env_vars=env_vars,
            timeout=600
        )
        
        if success:
            service_url = cloud_run_manager.get_service_url(service_name)
            logger.info(f"Cloud Run service deployed successfully: {service_url}")
            return True
        else:
            logger.error("Failed to deploy Cloud Run service")
            return False
            
    except Exception as e:
        logger.error(f"Error deploying Cloud Run service: {str(e)}")
        return False

def deploy_workflow(
    project_id: str,
    region: str,
    workflow_name: str,
    workflow_file: str
) -> bool:
    """Deploy Workflow"""
    try:
        workflow_manager = WorkflowManager(project_id, region)
        
        # Read workflow definition
        with open(workflow_file, 'r') as f:
            workflow_definition = f.read()
        
        success = workflow_manager.create_workflow(
            workflow_name=workflow_name,
            workflow_definition=workflow_definition,
            description="PDF processing workflow: analyze and split PDFs"
        )
        
        if success:
            logger.info(f"Workflow deployed successfully: {workflow_name}")
            return True
        else:
            logger.error("Failed to deploy workflow")
            return False
            
    except Exception as e:
        logger.error(f"Error deploying workflow: {str(e)}")
        return False

def test_service(service_url: str) -> bool:
    """Test the deployed service"""
    try:
        import requests
        
        # Test health endpoint
        health_url = f"{service_url}/health"
        response = requests.get(health_url, timeout=30)
        
        if response.status_code == 200:
            logger.info("Service health check passed")
            return True
        else:
            logger.error(f"Service health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing service: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Deploy PDF processing microservice')
    parser.add_argument('--project-id', required=True, help='GCP Project ID')
    parser.add_argument('--region', default='us-central1', help='GCP Region')
    parser.add_argument('--service-name', default='pdf-processor', help='Cloud Run service name')
    parser.add_argument('--workflow-name', default='pdf-processing-workflow', help='Workflow name')
    parser.add_argument('--image-uri', required=True, help='Container image URI')
    parser.add_argument('--bucket-name', required=True, help='GCS bucket name')
    parser.add_argument('--workflow-file', default='workflows/pdf_processing_workflow.yaml', help='Workflow YAML file')
    parser.add_argument('--test-only', action='store_true', help='Only test existing deployment')
    parser.add_argument('--skip-workflow', action='store_true', help='Skip workflow deployment')
    
    args = parser.parse_args()
    
    if args.test_only:
        # Test existing deployment
        cloud_run_manager = CloudRunManager(args.project_id, args.region)
        service_url = cloud_run_manager.get_service_url(args.service_name)
        
        if service_url:
            success = test_service(service_url)
            sys.exit(0 if success else 1)
        else:
            logger.error("Service not found")
            sys.exit(1)
    
    # Deploy Cloud Run service
    logger.info("Deploying Cloud Run service...")
    service_success = deploy_cloud_run_service(
        project_id=args.project_id,
        region=args.region,
        service_name=args.service_name,
        image_uri=args.image_uri,
        bucket_name=args.bucket_name
    )
    
    if not service_success:
        logger.error("Cloud Run deployment failed")
        sys.exit(1)
    
    # Test service
    cloud_run_manager = CloudRunManager(args.project_id, args.region)
    service_url = cloud_run_manager.get_service_url(args.service_name)
    
    if service_url:
        logger.info("Testing deployed service...")
        test_success = test_service(service_url)
        if not test_success:
            logger.warning("Service test failed, but deployment completed")
    else:
        logger.error("Could not get service URL")
        sys.exit(1)
    
    # Deploy workflow (optional)
    if not args.skip_workflow:
        logger.info("Deploying workflow...")
        workflow_success = deploy_workflow(
            project_id=args.project_id,
            region=args.region,
            workflow_name=args.workflow_name,
            workflow_file=args.workflow_file
        )
        
        if not workflow_success:
            logger.warning("Workflow deployment failed, but service is deployed")
    
    logger.info("Deployment completed successfully!")
    logger.info(f"Service URL: {service_url}")
    logger.info(f"Health check: {service_url}/health")

if __name__ == '__main__':
    main()
