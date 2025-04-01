# APIService is a Pit
# APIService can be initialized with a list of endpoints or OpenAPI spec
# APIService is an abstract class
# Has practices: GetEndpoints, GetOpenAPISpec

from typing import List, Dict, Any, Optional, Union
import requests
from ..Pit import Pit
from prompits.Practice import Practice
import json
import threading
import time
import uuid
from datetime import datetime
from .Service import Service
from ..Message import Message
from ..AgentAddress import AgentAddress
from ..LogEvent import LogEvent

class Endpoint:
    def __init__(self, path: str, method: str, handler: callable):
        self.path = path
        self.method = method
        self.handler = handler

class OpenAPI:
    def __init__(self, info: Dict, paths: Dict, components: Dict = None):
        self.info = info
        self.paths = paths
        self.components = components or {}
    
    def to_dict(self):
        """Convert OpenAPI to dictionary"""
        return {
            "info": self.info,
            "paths": self.paths,
            "components": self.components
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create OpenAPI from dictionary"""
        return cls(
            info=data.get("info", {}),
            paths=data.get("paths", {}),
            components=data.get("components", {})
        )

class APIService(Service):
    def __init__(self, name: str, description: str = None):
        super().__init__(name, description or f"APIService {name}")
        self.endpoints = {}
        self.server = None
        self.running = False
        self.AddPractice(Practice("GetEndpoints", self.GetEndpoints))
        self.AddPractice(Practice("GetOpenAPISpec", self.GetOpenAPISpec))
        self.openapi_spec = None
        
    def Request(self, endpoint: Endpoint, body: Dict = None, headers: Dict = None, params: Dict = None):
        """
        Request an endpoint.
        """
        # implement using requests
        if not self.server:
            raise ValueError("Server is not set")
            
        url = f"{self.server}{endpoint.path}"
        request_body = body if body is not None else endpoint.body
        response = requests.request(endpoint.method, url, json=request_body, headers=headers, params=params)
        return response.json()
    
    def ToJson(self):
        """
        Convert the service to a JSON object.
        
        Returns:
            dict: JSON representation of the service
        """
        endpoints_json = []
        for endpoint in self.endpoints.values():
            endpoints_json.append(endpoint.to_dict())
        
        openapi_json = None
        if self.openapi_spec:
            openapi_json = self.openapi_spec.to_dict()
            
        # Get base JSON data from parent which includes practices
        json_data = super().ToJson()
        self.log(f"APIService ToJson start: {json_data}","DEBUG")
        # Ensure practices are included
        if "practices" not in json_data and hasattr(self, "practices"):
            json_data["practices"] = {
                practice.name: practice.ToJson() for practice in self.practices.values()
            }
            
        # Add APIService specific fields
        json_data.update({
            "server": self.server,
            "endpoints": endpoints_json,
            "openapi_spec": openapi_json
        })
        self.log(f"APIService ToJson end: {json_data}","DEBUG")
        return json_data
    
    def FromJson(self, json_data):
        """
        Initialize the service from a JSON object.
        
        Args:
            json_data: JSON object containing service configuration
            
        Returns:
            APIService: The initialized service
        """
        self.name = json_data.get("name", self.name)
        self.description = json_data.get("description", self.description)
        self.server = json_data.get("server", self.server)
        
        # Load endpoints
        if "endpoints" in json_data:
            self.endpoints = {}
            for endpoint_data in json_data["endpoints"]:
                endpoint = Endpoint(endpoint_data["path"], endpoint_data["method"], endpoint_data["handler"])
                self.endpoints[endpoint.path] = endpoint
        
        # Load OpenAPI spec
        if "openapi_spec" in json_data and json_data["openapi_spec"]:
            self.openapi_spec = OpenAPI.from_dict(json_data["openapi_spec"])
        
        return self
    
    def GetEndpoints(self):
        """
        Get the list of endpoints for this API service.
        
        Returns:
            List[Endpoint]: List of endpoints
        """
        return list(self.endpoints.values())

    def GetOpenAPISpec(self):
        """
        Get the OpenAPI specification for this API service.
        
        Returns:
            OpenAPI: OpenAPI specification
        """
        return self.openapi_spec
    
    def AddEndpoint(self, endpoint: Endpoint):
        """
        Add an endpoint to this API service.
        
        Args:
            endpoint (Endpoint): The endpoint to add
            
        Returns:
            bool: True if added successfully
        """
        self.endpoints[endpoint.path] = endpoint
        return True
    
    def RemoveEndpoint(self, path: str):
        """
        Remove an endpoint from this API service.
        
        Args:
            path (str): The path of the endpoint
            
        Returns:
            bool: True if removed successfully, False if not found
        """
        return self.endpoints.pop(path, False)
    
    def SetOpenAPISpec(self, openapi_spec: OpenAPI):
        """
        Set the OpenAPI specification for this API service.
        
        Args:
            openapi_spec (OpenAPI): The OpenAPI specification
            
        Returns:
            bool: True if set successfully
        """
        self.openapi_spec = openapi_spec
        return True
    
    def GenerateOpenAPISpec(self):
        """
        Generate an OpenAPI specification from the endpoints.
        
        Returns:
            OpenAPI: Generated OpenAPI specification
        """
        if not self.endpoints:
            return None
        
        paths = {}
        for endpoint in self.endpoints.values():
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            
            paths[endpoint.path][endpoint.method.lower()] = {
                "description": endpoint.description or "",
                "parameters": endpoint.parameters,
                "responses": endpoint.responses
            }
        
        info = {
            "title": self.name,
            "description": self.description or f"API Service: {self.name}",
            "version": "1.0.0"
        }
        
        self.openapi_spec = OpenAPI(info=info, paths=paths)
        return self.openapi_spec

