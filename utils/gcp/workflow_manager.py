"""
GCP Workflows Manager
Handles Workflow pipeline orchestration
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from google.cloud import workflows_v1
from google.cloud.workflows_v1.types import workflow, execution
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages GCP Workflows for pipeline orchestration"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        """
        Initialize Workflow manager
        
        Args:
            project_id: GCP project ID
            region: GCP region for Workflows
        """
        self.project_id = project_id
        self.region = region
        self.client = workflows_v1.WorkflowsClient()
        self.executions_client = workflows_v1.ExecutionsClient()
        self.parent = f"projects/{project_id}/locations/{region}"
    
    def create_workflow(
        self,
        workflow_name: str,
        workflow_definition: str,
        description: str = ""
    ) -> bool:
        """
        Create a new workflow
        
        Args:
            workflow_name: Name of the workflow
            workflow_definition: YAML definition of the workflow
            description: Description of the workflow
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            workflow_obj = workflow.Workflow(
                name=f"{self.parent}/workflows/{workflow_name}",
                source_contents=workflow_definition,
                description=description
            )
            
            operation = self.client.create_workflow(
                parent=self.parent,
                workflow=workflow_obj,
                workflow_id=workflow_name
            )
            
            result = operation.result(timeout=600)  # 10 minutes timeout
            logger.info(f"Successfully created workflow {workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create workflow {workflow_name}: {str(e)}")
            return False
    
    def update_workflow(
        self,
        workflow_name: str,
        workflow_definition: str,
        description: str = ""
    ) -> bool:
        """
        Update an existing workflow
        
        Args:
            workflow_name: Name of the workflow
            workflow_definition: YAML definition of the workflow
            description: Description of the workflow
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            workflow_path = f"{self.parent}/workflows/{workflow_name}"
            
            # Get existing workflow
            existing_workflow = self.client.get_workflow(name=workflow_path)
            
            # Update workflow
            existing_workflow.source_contents = workflow_definition
            existing_workflow.description = description
            
            operation = self.client.update_workflow(workflow=existing_workflow)
            result = operation.result(timeout=600)  # 10 minutes timeout
            logger.info(f"Successfully updated workflow {workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_name}: {str(e)}")
            return False
    
    def execute_workflow(
        self,
        workflow_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Execute a workflow
        
        Args:
            workflow_name: Name of the workflow
            arguments: Arguments to pass to the workflow
            
        Returns:
            str: Execution ID or None if failed
        """
        try:
            workflow_path = f"{self.parent}/workflows/{workflow_name}"
            
            execution_obj = execution.Execution(
                argument=json.dumps(arguments) if arguments else "{}"
            )
            
            operation = self.executions_client.create_execution(
                parent=workflow_path,
                execution=execution_obj
            )
            
            result = operation.result(timeout=300)  # 5 minutes timeout
            execution_id = result.name.split('/')[-1]
            logger.info(f"Successfully started execution {execution_id} for workflow {workflow_name}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_name}: {str(e)}")
            return None
    
    def get_execution_status(self, workflow_name: str, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a workflow execution
        
        Args:
            workflow_name: Name of the workflow
            execution_id: ID of the execution
            
        Returns:
            Dict with execution status or None if failed
        """
        try:
            execution_path = f"{self.parent}/workflows/{workflow_name}/executions/{execution_id}"
            execution_obj = self.executions_client.get_execution(name=execution_path)
            
            status = {
                "name": execution_obj.name,
                "state": execution_obj.state.name,
                "start_time": execution_obj.start_time.isoformat() if execution_obj.start_time else None,
                "end_time": execution_obj.end_time.isoformat() if execution_obj.end_time else None,
                "result": execution_obj.result if execution_obj.result else None,
                "error": execution_obj.error.message if execution_obj.error else None
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get execution status for {execution_id}: {str(e)}")
            return None
    
    def wait_for_completion(
        self,
        workflow_name: str,
        execution_id: str,
        timeout: int = 3600,
        poll_interval: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for workflow execution to complete
        
        Args:
            workflow_name: Name of the workflow
            execution_id: ID of the execution
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Final execution status or None if failed
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_execution_status(workflow_name, execution_id)
            if not status:
                return None
            
            state = status["state"]
            if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                logger.info(f"Execution {execution_id} completed with state: {state}")
                return status
            
            logger.info(f"Execution {execution_id} is {state}, waiting...")
            time.sleep(poll_interval)
        
        logger.error(f"Execution {execution_id} timed out after {timeout} seconds")
        return None
    
    def list_workflows(self) -> List[str]:
        """
        List all workflows
        
        Returns:
            List of workflow names
        """
        try:
            workflows = self.client.list_workflows(parent=self.parent)
            return [workflow.name.split('/')[-1] for workflow in workflows]
        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            return []
    
    def delete_workflow(self, workflow_name: str) -> bool:
        """
        Delete a workflow
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            workflow_path = f"{self.parent}/workflows/{workflow_name}"
            operation = self.client.delete_workflow(name=workflow_path)
            operation.result(timeout=300)  # 5 minutes timeout
            logger.info(f"Successfully deleted workflow {workflow_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_name}: {str(e)}")
            return False
    
    def create_pdf_processing_workflow(self, workflow_name: str) -> bool:
        """
        Create a predefined PDF processing workflow
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            bool: True if successful, False otherwise
        """
        workflow_definition = f"""
main:
  steps:
    - analyze_pdf:
        call: http.post
        args:
          url: "${{env.PDF_ANALYZER_URL}}"
          headers:
            Content-Type: "application/json"
          body:
            pdf_path: "${{pdf_path}}"
            bucket_name: "${{env.BUCKET_NAME}}"
        result: analysis_result
    
    - upload_analysis:
        call: http.post
        args:
          url: "${{env.BUCKET_MANAGER_URL}}"
          headers:
            Content-Type: "application/json"
          body:
            operation: "upload_json"
            bucket_name: "${{env.BUCKET_NAME}}"
            gcs_path: "${{pdf_path}}_analysis.json"
            data: "${{analysis_result}}"
        result: upload_result
    
    - split_pdf:
        call: http.post
        args:
          url: "${{env.PDF_SPLITTER_URL}}"
          headers:
            Content-Type: "application/json"
          body:
            pdf_path: "${{pdf_path}}"
            analysis_path: "${{pdf_path}}_analysis.json"
            bucket_name: "${{env.BUCKET_NAME}}"
        result: split_result
    
    - return_result:
        return:
          analysis_result: "${{analysis_result}}"
          split_result: "${{split_result}}"
"""
        
        return self.create_workflow(
            workflow_name=workflow_name,
            workflow_definition=workflow_definition,
            description="PDF processing workflow: analyze and split PDFs"
        )
