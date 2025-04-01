""""
!!! This is not implemented yet.

HTTP Plug module for communication between agents over HTTP.

An HTTP Plug allows agents to communicate with each other over HTTP.
It provides methods for sending and receiving HTTP requests and responses.
"""

import json
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import requests

from ..Plug import Plug
from ..Practice import Practice
from ..Message import Message
from ..AgentAddress import AgentAddress
from ..LogEvent import LogEvent

class HTTPPlug(Plug):
    """
    HTTP Plug for communication between agents.
    
    An HTTP Plug allows agents to communicate with each other over HTTP.
    It provides methods for sending HTTP requests and receiving responses.
    """
    
    def __init__(self, name: str, description: str = None, host: str = "localhost", port: int = 8000, base_path: str = "", use_https: bool = False):
        """
        Initialize an HTTP Plug.
        
        Args:
            name: Name of the plug
            description: Description of the plug
            host: Host to connect to
            port: Port to connect to
            base_path: Base path for API endpoints
            use_https: Whether to use HTTPS
        """
        super().__init__(name, description or f"HTTP Plug {name}")
        self.host = host
        self.port = port
        self.base_path = base_path.strip('/')
        self.use_https = use_https
        self.connected = False
        self.session = None
        self.message_queue = []
        self.message_lock = threading.Lock()
        
        # Add HTTP-specific practices
        self.AddPractice(Practice("Connect", self.connect))
        self.AddPractice(Practice("Disconnect", self.disconnect))
        self.AddPractice(Practice("Send", self.send))
        self.AddPractice(Practice("Receive", self.receive))
        self.AddPractice(Practice("IsConnected", self.is_connected))
        self.AddPractice(Practice("Get", self.get))
        self.AddPractice(Practice("Post", self.post))
        self.AddPractice(Practice("Put", self.put))
        self.AddPractice(Practice("Delete", self.delete))
        self.AddPractice(Practice("SetHeaders", self.set_headers))
        self.AddPractice(Practice("SetAuth", self.set_auth))
        self.AddPractice(Practice("Echo", self.echo))
        
    def ToJson(self):
        """
        Convert the HTTP plug to a JSON object.
        
        Returns:
            dict: JSON representation of the HTTP plug
        """
        json_data = super().ToJson()
        json_data.update({
            "host": self.host,
            "port": self.port,
            "base_path": self.base_path,
            "use_https": self.use_https
        })
        return json_data
    
    def FromJson(self, json_data):
        """
        Initialize the HTTP plug from a JSON object.
        
        Args:
            json_data: JSON object containing HTTP plug configuration
            
        Returns:
            HTTPPlug: The initialized HTTP plug
        """
        super().FromJson(json_data)
        self.host = json_data.get("host", self.host)
        self.port = json_data.get("port", self.port)
        self.base_path = json_data.get("base_path", self.base_path)
        self.use_https = json_data.get("use_https", self.use_https)
        return self
    
    def connect(self):
        """
        Connect the HTTP plug.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.connected:
            print(f"HTTP Plug {self.name} is already connected")
            return True
        
        try:
            # Create a new session
            self.session = requests.Session()
            
            # Start the HTTP server
            self.server = HTTPServer(self.host, self.port, self.base_path)
            
            # Add a route for handling messages
            self.server.add_route("POST", "message", self._handle_message)
            
            # Start the server
            if self.server.start():
                self.connected = True
                print(f"Connected HTTP Plug {self.name} to {self._build_url()}")
                return True
            else:
                print(f"Failed to start HTTP server for {self.name}")
                self.session = None
                return False
        except Exception as e:
            print(f"Error connecting HTTP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            self.session = None
            return False
    
    def disconnect(self):
        """
        Disconnect the HTTP plug.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        if not self.connected:
            print(f"HTTP Plug {self.name} is not connected")
            return True
        
        try:
            # Close the session
            if self.session:
                self.session.close()
                self.session = None
            
            # Stop the server
            if hasattr(self, 'server') and self.server:
                self.server.stop()
                self.server = None
            
            self.connected = False
            print(f"Disconnected HTTP Plug {self.name}")
            return True
        except Exception as e:
            print(f"Error disconnecting HTTP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            return False
    
    def send(self, message: Dict[str, Any]):
        """
        Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.connected:
            print(f"HTTP Plug {self.name} is not connected")
            return False
        
        try:
            # Extract message details
            method = message.get("method", "GET").upper()
            endpoint = message.get("endpoint", "")
            data = message.get("data")
            params = message.get("params")
            headers = message.get("headers", {})
            
            # Build the URL
            url = self._build_url(endpoint)
            
            # Send the request
            if method == "GET":
                response = self.session.get(url, params=params, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, params=params, headers=headers)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, headers=headers)
            else:
                print(f"Unsupported HTTP method: {method}")
                return False
            
            # Store the response in the message queue
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "timestamp": time.time(),
                "request": {
                    "method": method,
                    "url": url,
                    "data": data,
                    "params": params
                }
            }
            
            # Try to parse JSON response
            try:
                response_data["json"] = response.json()
            except:
                pass
            
            with self.message_lock:
                self.message_queue.append(response_data)
            
            # Notify the agent about the received message
            self.notify_agent(response_data)
            
            print(f"Sent {method} request to {url}")
            return True
        except Exception as e:
            print(f"Error sending message via HTTP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            return False
    
    def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message.
        
        Returns:
            dict: Received message, or None if no message is available
        """
        with self.message_lock:
            if not self.message_queue:
                return None
            
            # Get the oldest message
            return self.message_queue.pop(0)
    
    def is_connected(self) -> bool:
        """
        Check if the HTTP plug is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def get(self, endpoint: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """
        Send a GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            
        Returns:
            dict: Response data
        """
        message = {
            "method": "GET",
            "endpoint": endpoint,
            "params": params,
            "headers": headers
        }
        
        if self.send(message):
            return self.receive()
        return None
    
    def post(self, endpoint: str, data: Any = None, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """
        Send a POST request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            headers: Request headers
            
        Returns:
            dict: Response data
        """
        message = {
            "method": "POST",
            "endpoint": endpoint,
            "data": data,
            "params": params,
            "headers": headers
        }
        
        if self.send(message):
            return self.receive()
        return None
    
    def put(self, endpoint: str, data: Any = None, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """
        Send a PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            headers: Request headers
            
        Returns:
            dict: Response data
        """
        message = {
            "method": "PUT",
            "endpoint": endpoint,
            "data": data,
            "params": params,
            "headers": headers
        }
        
        if self.send(message):
            return self.receive()
        return None
    
    def delete(self, endpoint: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None):
        """
        Send a DELETE request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            
        Returns:
            dict: Response data
        """
        message = {
            "method": "DELETE",
            "endpoint": endpoint,
            "params": params,
            "headers": headers
        }
        
        if self.send(message):
            return self.receive()
        return None
    
    def set_headers(self, headers: Dict[str, str]):
        """
        Set default headers for all requests.
        
        Args:
            headers: Headers to set
            
        Returns:
            bool: True if headers were set successfully
        """
        if not self.connected or not self.session:
            print(f"HTTP Plug {self.name} is not connected")
            return False
        
        self.session.headers.update(headers)
        print(f"Set headers for HTTP Plug {self.name}")
        return True
    
    def set_auth(self, auth_type: str, credentials: Union[str, Dict[str, str], List[str]]):
        """
        Set authentication for all requests.
        
        Args:
            auth_type: Type of authentication (basic, bearer, api_key)
            credentials: Authentication credentials
            
        Returns:
            bool: True if authentication was set successfully
        """
        if not self.connected or not self.session:
            print(f"HTTP Plug {self.name} is not connected")
            return False
        
        try:
            if auth_type.lower() == "basic":
                # For basic auth, credentials should be [username, password]
                if isinstance(credentials, list) and len(credentials) == 2:
                    self.session.auth = (credentials[0], credentials[1])
                else:
                    print("Basic authentication requires a list with username and password")
                    return False
            elif auth_type.lower() == "bearer":
                # For bearer auth, credentials should be the token string
                if isinstance(credentials, str):
                    self.session.headers.update({"Authorization": f"Bearer {credentials}"})
                else:
                    print("Bearer authentication requires a token string")
                    return False
            elif auth_type.lower() == "api_key":
                # For API key, credentials should be {header_name: key} or {param_name: key}
                if isinstance(credentials, dict) and len(credentials) == 1:
                    key_name, key_value = next(iter(credentials.items()))
                    self.session.headers.update({key_name: key_value})
                else:
                    print("API key authentication requires a dictionary with one key-value pair")
                    return False
            else:
                print(f"Unsupported authentication type: {auth_type}")
                return False
            
            print(f"Set {auth_type} authentication for HTTP Plug {self.name}")
            return True
        except Exception as e:
            print(f"Error setting authentication for HTTP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            return False
    
    def _build_url(self, endpoint: str = ""):
        """
        Build a URL for the given endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            str: Full URL
        """
        # Remove leading/trailing slashes from endpoint
        endpoint = endpoint.strip('/')
        
        # Build the base URL
        protocol = "https" if self.use_https else "http"
        base_url = f"{protocol}://{self.host}:{self.port}"
        
        # Add base path if specified
        if self.base_path:
            base_url = f"{base_url}/{self.base_path}"
        
        # Add endpoint if specified
        if endpoint:
            return f"{base_url}/{endpoint}"
        
        return base_url
    
    def echo(self, message):
        """
        Echo a message back to the sender.
        
        Args:
            message: Message to echo
            
        Returns:
            dict: The message
        """
        print(f"Echoing message: {message}")
        return {"echo": message}
    
    def _handle_message(self, request):
        """
        Handle an incoming message.
        
        Args:
            request: The HTTP request
            
        Returns:
            dict: Response to the request
        """
        try:
            # Parse the message
            message = request.get("json", {})
            
            # Add the message to the queue
            with self.message_lock:
                self.message_queue.append(message)
            
            # Notify the agent about the received message
            self.notify_agent(message)
            
            print(f"Received message on HTTP Plug {self.name}: {message}")
            
            # Return a success response
            return {
                "status": "success",
                "message": "Message received"
            }
        except Exception as e:
            print(f"Error handling message on HTTP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e)
            }

class HTTPServer:
    """
    HTTP Server for handling incoming HTTP requests.
    
    This class provides a simple HTTP server that can be used to receive
    incoming HTTP requests and route them to the appropriate handlers.
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000, base_path: str = ""):
        """
        Initialize an HTTP Server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            base_path: Base path for API endpoints
        """
        self.host = host
        self.port = port
        self.base_path = base_path.strip('/')
        self.routes = {}
        self.running = False
        self.server_thread = None
        
    def add_route(self, method: str, endpoint: str, handler):
        """
        Add a route to the server.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            handler: Function to handle the request
            
        Returns:
            bool: True if the route was added successfully
        """
        method = method.upper()
        
        # Remove leading/trailing slashes from endpoint
        endpoint = endpoint.strip('/')
        
        # Add base path if specified
        if self.base_path:
            endpoint = f"{self.base_path}/{endpoint}"
        
        # Create route key
        route_key = f"{method}:{endpoint}"
        
        # Add the route
        self.routes[route_key] = handler
        print(f"Added route {method} /{endpoint}")
        return True
    
    def remove_route(self, method: str, endpoint: str):
        """
        Remove a route from the server.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            
        Returns:
            bool: True if the route was removed successfully
        """
        method = method.upper()
        
        # Remove leading/trailing slashes from endpoint
        endpoint = endpoint.strip('/')
        
        # Add base path if specified
        if self.base_path:
            endpoint = f"{self.base_path}/{endpoint}"
        
        # Create route key
        route_key = f"{method}:{endpoint}"
        
        # Remove the route
        if route_key in self.routes:
            del self.routes[route_key]
            print(f"Removed route {method} /{endpoint}")
            return True
        
        print(f"Route {method} /{endpoint} not found")
        return False
    
    def start(self):
        """
        Start the HTTP server.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            print(f"HTTP Server is already running on {self.host}:{self.port}")
            return True
        
        try:
            # In a real implementation, this would start a web server
            # For now, we'll just simulate it with a thread
            self.running = True
            self.server_thread = threading.Thread(
                target=self._server_loop,
                daemon=True
            )
            self.server_thread.start()
            
            print(f"Started HTTP Server on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error starting HTTP Server: {str(e)}")
            traceback.print_exc()
            self.running = False
            return False
    
    def stop(self):
        """
        Stop the HTTP server.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            print("HTTP Server is not running")
            return True
        
        try:
            # In a real implementation, this would stop the web server
            # For now, we'll just simulate it
            self.running = False
            
            # Wait for the server thread to finish
            if self.server_thread:
                self.server_thread.join(timeout=1)
                self.server_thread = None
            
            print("Stopped HTTP Server")
            return True
        except Exception as e:
            print(f"Error stopping HTTP Server: {str(e)}")
            traceback.print_exc()
            return False
    
    def _server_loop(self):
        """
        Main server loop.
        
        This method simulates a server loop that would handle incoming requests.
        In a real implementation, this would be replaced with a proper web server.
        """
        print(f"HTTP Server running on {self.host}:{self.port}")
        
        while self.running:
            # In a real implementation, this would handle incoming requests
            # For now, we'll just sleep to simulate the server running
            time.sleep(1)
        
        print("HTTP Server loop stopped") 