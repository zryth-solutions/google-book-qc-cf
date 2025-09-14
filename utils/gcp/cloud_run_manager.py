"""
GCP Cloud Run Manager
Handles Cloud Run service deployment and management
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from google.cloud import run_v2
from google.cloud.run_v2.types import service, container, env_vars
import logging

logger = logging.getLogger(__name__)

class CloudRunManager:
    """Manages GCP Cloud Run services"""
    
    def __init__(self, project_id: str, region: str = "us-central1"):
        """
        Initialize Cloud Run manager
        
        Args:
            project_id: GCP project ID
            region: GCP region for Cloud Run services
        """
        self.project_id = project_id
        self.region = region
        self.client = run_v2.ServicesClient()
        self.parent = f"projects/{project_id}/locations/{region}"
    
    def deploy_service(
        self,
        service_name: str,
        image_uri: str,
        port: int = 8080,
        memory: str = "1Gi",
        cpu: str = "1",
        max_instances: int = 10,
        min_instances: int = 0,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = 300
    ) -> bool:
        """
        Deploy a Cloud Run service
        
        Args:
            service_name: Name of the service
            image_uri: Container image URI
            port: Port to expose
            memory: Memory allocation
            cpu: CPU allocation
            max_instances: Maximum number of instances
            min_instances: Minimum number of instances
            env_vars: Environment variables
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if service exists
            service_path = f"{self.parent}/services/{service_name}"
            
            try:
                existing_service = self.client.get_service(name=service_path)
                logger.info(f"Service {service_name} exists, updating...")
                return self._update_service(
                    service_name, image_uri, port, memory, cpu, 
                    max_instances, min_instances, env_vars, timeout
                )
            except Exception:
                logger.info(f"Service {service_name} does not exist, creating...")
                return self._create_service(
                    service_name, image_uri, port, memory, cpu, 
                    max_instances, min_instances, env_vars, timeout
                )
                
        except Exception as e:
            logger.error(f"Failed to deploy service {service_name}: {str(e)}")
            return False
    
    def _create_service(
        self,
        service_name: str,
        image_uri: str,
        port: int,
        memory: str,
        cpu: str,
        max_instances: int,
        min_instances: int,
        env_vars: Optional[Dict[str, str]],
        timeout: int
    ) -> bool:
        """Create a new Cloud Run service"""
        try:
            # Prepare environment variables
            env_variables = []
            if env_vars:
                for key, value in env_vars.items():
                    env_variables.append(
                        env_vars.EnvVar(name=key, value=value)
                    )
            
            # Create service configuration
            service_config = service.Service(
                template=service.RevisionTemplate(
                    containers=[
                        container.Container(
                            image=image_uri,
                            ports=[container.ContainerPort(container_port=port)],
                            resources=container.ResourceRequirements(
                                limits={
                                    "memory": memory,
                                    "cpu": cpu
                                }
                            ),
                            env=env_variables
                        )
                    ],
                    timeout=f"{timeout}s",
                    scaling=service.RevisionScaling(
                        min_instance_count=min_instances,
                        max_instance_count=max_instances
                    )
                )
            )
            
            # Create the service
            service_path = f"{self.parent}/services/{service_name}"
            operation = self.client.create_service(
                parent=self.parent,
                service=service_config,
                service_id=service_name
            )
            
            # Wait for operation to complete
            result = operation.result(timeout=600)  # 10 minutes timeout
            logger.info(f"Successfully created service {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create service {service_name}: {str(e)}")
            return False
    
    def _update_service(
        self,
        service_name: str,
        image_uri: str,
        port: int,
        memory: str,
        cpu: str,
        max_instances: int,
        min_instances: int,
        env_vars: Optional[Dict[str, str]],
        timeout: int
    ) -> bool:
        """Update an existing Cloud Run service"""
        try:
            service_path = f"{self.parent}/services/{service_name}"
            
            # Get existing service
            existing_service = self.client.get_service(name=service_path)
            
            # Prepare environment variables
            env_variables = []
            if env_vars:
                for key, value in env_vars.items():
                    env_variables.append(
                        env_vars.EnvVar(name=key, value=value)
                    )
            
            # Update container configuration
            existing_service.template.containers[0].image = image_uri
            existing_service.template.containers[0].resources.limits = {
                "memory": memory,
                "cpu": cpu
            }
            existing_service.template.containers[0].env = env_variables
            existing_service.template.timeout = f"{timeout}s"
            existing_service.template.scaling.min_instance_count = min_instances
            existing_service.template.scaling.max_instance_count = max_instances
            
            # Update the service
            operation = self.client.update_service(service=existing_service)
            result = operation.result(timeout=600)  # 10 minutes timeout
            logger.info(f"Successfully updated service {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update service {service_name}: {str(e)}")
            return False
    
    def get_service_url(self, service_name: str) -> Optional[str]:
        """
        Get the URL of a Cloud Run service
        
        Args:
            service_name: Name of the service
            
        Returns:
            str: Service URL or None if not found
        """
        try:
            service_path = f"{self.parent}/services/{service_name}"
            service_obj = self.client.get_service(name=service_path)
            return service_obj.uri
        except Exception as e:
            logger.error(f"Failed to get service URL for {service_name}: {str(e)}")
            return None
    
    def delete_service(self, service_name: str) -> bool:
        """
        Delete a Cloud Run service
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            service_path = f"{self.parent}/services/{service_name}"
            operation = self.client.delete_service(name=service_path)
            operation.result(timeout=300)  # 5 minutes timeout
            logger.info(f"Successfully deleted service {service_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete service {service_name}: {str(e)}")
            return False
    
    def list_services(self) -> List[str]:
        """
        List all Cloud Run services
        
        Returns:
            List of service names
        """
        try:
            services = self.client.list_services(parent=self.parent)
            return [service.name.split('/')[-1] for service in services]
        except Exception as e:
            logger.error(f"Failed to list services: {str(e)}")
            return []
    
    def invoke_service(
        self,
        service_name: str,
        data: Dict[str, Any],
        timeout: int = 300
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke a Cloud Run service with data
        
        Args:
            service_name: Name of the service
            data: Data to send to the service
            timeout: Request timeout in seconds
            
        Returns:
            Response data or None if failed
        """
        try:
            import requests
            
            service_url = self.get_service_url(service_name)
            if not service_url:
                logger.error(f"Could not get URL for service {service_name}")
                return None
            
            response = requests.post(
                service_url,
                json=data,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to invoke service {service_name}: {str(e)}")
            return None
