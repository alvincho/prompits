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

class OpenAPI:
    """
    Represents an OpenAPI specification that describes an API.
    
    The OpenAPI specification provides a standardized format for API documentation,
    including information about available endpoints, request/response formats,
    authentication methods, and more.
    """
    
    def __init__(self, openapi_spec: dict):
        """
        Initialize an OpenAPI specification.
        
        Args:
            openapi_spec: JSON data containing OpenAPI specification, supports 3.0.0 and above
        """
        self.openapi = openapi_spec.get("openapi", "unknown")
        # if self.openapi is under 3.0.0, raise an error
        if self.openapi < "3.0.0":
            raise ValueError("OpenAPI version must be 3.0.0 or higher")
        self.info = openapi_spec.get("info", {})
        self.servers = openapi_spec.get("servers", [])
        self.paths = openapi_spec.get("paths", {})
        self.components = openapi_spec.get("components", {})
        self.security = openapi_spec.get("security", {})
        self.tags = openapi_spec.get("tags", [])
        self.externalDocs = openapi_spec.get("externalDocs", {})
    
    def ToJson(self):
        """Convert OpenAPI to dictionary"""
        return {
            "openapi": self.openapi,
            "info": self.info,
            "servers": self.servers,
            "paths": self.paths,
            "components": self.components,
            "security": self.security,
            "tags": self.tags,
            "externalDocs": self.externalDocs
        }
    

class APIService(Service):
    """
    Service that provides API functionality through defined endpoints.
    
    APIService is a Pit that allows agents to expose and consume APIs by defining endpoints
    It takes an OpenAPI specification and allows agents to expose and consume APIs by defining endpoints
    Each endpoint is mapped to a practice that can be called by an agent
    """
    # TODO: Implement security schemes
    
    def __init__(self, name: str, description: str = None, openapi_spec: OpenAPI = None):
        """
        Initialize an APIService instance.
        
        Args:
            name: The name of the API service
            description: Optional description of the API service's purpose
        """
        super().__init__(name, description or f"APIService {name}")
        self.endpoints = {}
        self.servers = []
        self.running = False
        self.openapi_spec = openapi_spec

        # map openapi_spec paths to practices
        # operationId is the practice name
        if self.openapi_spec:
            if self.openapi_spec.servers:
                self.servers = self.openapi_spec.servers
            for path, path_item in self.openapi_spec.paths.items():
                for method, method_item in path_item.items():
                    print(f"{path} {method}")
                if "operationId" in method_item:
                    practice_name = method_item.get("operationId", f"{method} {path}")
                else:
                    practice_name = f"{method} {path}"
                if "summary" in method_item:
                    description = method_item.get("summary", "")
                elif "description" in method_item:
                    description = method_item.get("description", "")
                else:
                    description = practice_name
                if method == "get":
                    parameters = method_item.get("parameters", [])
                    input_schema = {}
                    for parameter in parameters:
                        if "$ref" in parameter:
                            schema = self.openapi_spec.components.get("schemas", {}).get(parameter["$ref"].split("/")[-1], {})
                            input_schema[schema["name"]] = schema
                        else:
                            print(f"*** parameter: {parameter}")
                            input_schema[parameter["name"]] = parameter
                elif method == "post":
                    input_schema = method_item.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                    if "callbacks" in input_schema:
                        raise ValueError("Callbacks are not supported")
                    if "$ref" in input_schema:
                        input_schema = self.openapi_spec.components.get("schemas", {}).get(input_schema["$ref"].split("/")[-1], {})
                else:
                    raise ValueError(f"Method {method} is not supported")
                if "servers" in method_item:
                    servers = method_item.get("servers", [])
                else:
                    servers = self.servers
                parameters = {
                    "path": path,
                    "method": method,
                    "servers": servers,
                    "body_required": method_item.get("requestBody", {}).get("required", False),
                    "responses": method_item.get("responses", {})
                }
                print(f"practice_name: {practice_name}\ndescription: {description}\ninput_schema: {input_schema}\nparameters: {parameters}")
                self.AddPractice(Practice(practice_name , self._request, description, input_schema, False, parameters))
        
    def _request(self, body: Dict = None, headers: Dict = None, params: Dict = None,
                 path: str = None, method: str = None, servers: List[Dict] = None,
                 body_required: bool = False, responses: Dict = None):
        """
        Request an endpoint.
        """
        # implement using requests
        if not servers:
            raise ValueError("Server is not set")
        if not path:
            raise ValueError("Path is not set")
        if not method:
            raise ValueError("Method is not set")
        if not servers:
            raise ValueError("Servers are not set")
            
        url = f"{servers[0]['url']}{path}"
        print(f"url: {url}")
        request_body = body if body is not None else {}
        if method == "get":
            response = requests.get(url, headers=headers, params=params)
        elif method == "post":
            response = requests.post(url, json=request_body, headers=headers, params=params)
        else:
            raise ValueError(f"Method {method} is not supported")
        if response.status_code != 200:
            raise ValueError(f"Response status code is not 200: {response.status_code} {response.text}")
        print(f"response: {response}")
        return response.text
    
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
    