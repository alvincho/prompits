# gRPCPlug is a plug that uses gRPC to communicate with other agents
# gRPC is a high-performance, open-source and general RPC framework that puts mobile and HTTP/2 first

from datetime import datetime
import json
import traceback
import threading
import time
import uuid
import grpc
from concurrent import futures
from typing import Dict, Any, Optional, List, Union, Callable
import logging

from ..Plug import Plug
from ..Practice import Practice
from ..Message import Message, Attachment
from ..AgentAddress import AgentAddress
from ..LogEvent import LogEvent

# Setup logging
logger = logging.getLogger(__name__)

# Import the generated gRPC code
# Note: You'll need to generate these files from your .proto definitions
try:
    from prompits.plugs.protos import agent_pb2
    from prompits.plugs.protos import agent_pb2_grpc
except ImportError:
    # Placeholder for when protos aren't generated yet
    class agent_pb2:
        class Message:
            def __init__(self):
                self.id = ""
                self.type = ""
                self.content = ""
                self.timestamp = 0
                
        class AgentInfo:
            def __init__(self):
                self.agent_id = ""
                self.agent_name = ""
                
    class agent_pb2_grpc:
        class AgentServicer:
            pass
            
        class AgentStub:
            def __init__(self, channel):
                self.channel = channel
            
        def add_AgentServicer_to_server(servicer, server):
            pass

# Define the gRPC service
class AgentServicer(agent_pb2_grpc.AgentServicer):
    def __init__(self, grpc_plug):
        super().__init__()
        self.grpc_plug = grpc_plug
        
    def SendMessage(self, request, context):
        # Convert protobuf message to dict
        message = {
            'id': request.id,
            'type': request.type,
            'content': request.content,
            'timestamp': request.timestamp
        }
        
        # Trigger message event
        self.grpc_plug.trigger_event('message', message=message)
        
        # Add to message queue
        with self.grpc_plug.message_lock:
            self.grpc_plug.message_queue.append(message)
        
        # Return response
        return agent_pb2.MessageResponse(success=True, message="Message received")
    
    def Echo(self, request, context):
        # Echo the message back
        response = agent_pb2.Message()
        response.id = request.id
        response.type = "echo_response"
        response.content = request.content
        response.timestamp = int(time.time())
        return response
        
    def GetAgentInfo(self, request, context):
        # Get agent information from the plug's agent
        agent = self.grpc_plug.agent if hasattr(self.grpc_plug, 'agent') else None
        
        if not agent:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Agent information not available")
            return agent_pb2.AgentInfo()
            
        # Get capabilities (practices)
        capabilities = []
        if hasattr(agent, 'practices'):
            capabilities.extend(agent.practices.keys())
            
        # Create and return agent info
        return agent_pb2.AgentInfo(
            agent_id=getattr(agent, 'agent_id', str(uuid.uuid4())),
            agent_name=getattr(agent, 'name', "Unknown"),
            description=getattr(agent, 'description', ""),
            capabilities=capabilities
        )
    
    def ListPractices(self, request, context):
        # Get agent
        agent = self.grpc_plug.agent if hasattr(self.grpc_plug, 'agent') else None
        
        if not agent:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Agent not available")
            return agent_pb2.PracticeList()
            
        # Get practices
        practice_list = []
        
        # Add agent practices
        if hasattr(agent, 'practices'):
            for name, practice in agent.practices.items():
                # Get practice info
                practice_info = agent_pb2.Practice(
                    name=name,
                    description=practice.__doc__ if hasattr(practice, '__doc__') and practice.__doc__ else ""
                )
                
                # Add parameters if available
                if hasattr(practice, '__code__'):
                    for i, param_name in enumerate(practice.__code__.co_varnames[:practice.__code__.co_argcount]):
                        if param_name == 'self':
                            continue
                            
                        # Create parameter
                        param = agent_pb2.Parameter(
                            name=param_name,
                            type="unknown",
                            required=i >= (practice.__code__.co_argcount - len(practice.__defaults__ or []))
                        )
                        
                        # Add default value if available
                        if not param.required and practice.__defaults__:
                            default_idx = i - (practice.__code__.co_argcount - len(practice.__defaults__))
                            if default_idx >= 0:
                                param.default_value = str(practice.__defaults__[default_idx])
                                
                        # Add parameter to practice
                        practice_info.parameters.append(param)
                        
                # Add practice to list
                practice_list.append(practice_info)
                
        # Return practice list
        return agent_pb2.PracticeList(practices=practice_list)
        
    def ExecutePractice(self, request, context):
        # Get agent
        agent = self.grpc_plug.agent if hasattr(self.grpc_plug, 'agent') else None
        
        if not agent:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Agent not available")
            return agent_pb2.PracticeResponse(success=False, error="Agent not available")
            
        # Get practice name
        practice_name = request.practice_name
        
        # Check if practice exists
        if not hasattr(agent, 'UsePractice'):
            return agent_pb2.PracticeResponse(
                success=False,
                error="Agent does not support UsePractice method"
            )
            
        # Convert parameters
        params = {}
        for key, value in request.parameters.items():
            # Try to convert to appropriate type
            try:
                # Try as JSON first
                params[key] = json.loads(value)
            except json.JSONDecodeError:
                # Use as string
                params[key] = value
                
        # Execute practice
        try:
            result = agent.UsePractice(practice_name, **params)
            
            # Convert result to string if needed
            if not isinstance(result, str):
                try:
                    result = json.dumps(result)
                except:
                    result = str(result)
                    
            return agent_pb2.PracticeResponse(
                success=True,
                result=result
            )
        except Exception as e:
            return agent_pb2.PracticeResponse(
                success=False,
                error=str(e)
            )

class gRPCPlug(Plug):
    def __init__(self, name: str, description: str = None, host: str = "localhost", port: int = 9000, is_server: bool = False):
        """Initialize the gRPC plug
        
        Args:
            name: Name of the plug
            description: Description of the plug
            host: Host to connect to
            port: Port to connect to
            is_server: Whether this plug is a server
        """
        super().__init__(name, description)
        self._host = host
        self._port = port
        self.is_server = is_server
        self.server = None
        self.channel = None
        self.stub = None
        self.running = False
        self.connected = False
        self.message_queue = []
        self.message_lock = threading.Lock()
        self.event_handlers = {}
        
        if self.is_server:
            self._Listen({})

    def SendMessage(self, agent:AgentAddress, message: Message, plug_info:Dict[str, Any]= {}):
        """
        Send a message to an agent via gRPC
        
        Args:
            agent: AgentAddress
            message: Message
            plug_info: Dictionary with connection information
                {
                    "host": str,
                    "port": int
                }
                
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Format address
            agent_id = agent.agent_id
            server_address = None
            
            self.log(f"Sending message to {agent.ToJson()}", 'DEBUG')
            if plug_info and plug_info.get('host') and plug_info.get('port'):
                server_address = f"{plug_info.get('host')}:{plug_info.get('port')}"
                self.log(f"Connecting to {server_address} via gRPC Plug {self.name}", 'INFO')
                
                # Create a channel
                channel = grpc.insecure_channel(server_address)
                
                # Create a stub
                stub = agent_pb2_grpc.AgentStub(channel)
                
                # Convert message to JSON string
                timestamp = int(time.time())
                # Handle special cases in the message
                if isinstance(message, dict) and isinstance(message.get('content'), dict):
                    message['content'] = message['content'].ToJson()
                    msg_type = message.get('type', 'Message')
                    msg_str = json.dumps(message.ToJson(), default=vars)
                elif isinstance(message, Message):
                    msg_json = message.ToJson()
                    msg_str = json.dumps(msg_json, default=vars)
                    msg_type = 'Message'
                else:
                    msg_str = message
                    msg_type = 'Message'
                
                # Create message
                msg = agent_pb2.Message()
                msg.id = str(uuid.uuid4())
                msg.type = msg_type
                msg.content = msg_str
                msg.timestamp = timestamp
                
                self.log(LogEvent('DEBUG', 'GRPC_SEND_MESSAGE', f"Message: {msg}"))
                stub.SendMessage(msg)
                self.log(LogEvent('DEBUG', 'GRPC_SEND_MESSAGE', "Message sent"))
                return True
            else:
                self.log(f"No connection info for agent {agent}, skipping", 'WARNING')
                return False
        except Exception as e:
            print(f"Error sending message: {str(e)}\n{traceback.format_exc()}")
            self.log(LogEvent('ERROR', 'GRPC_SEND_MESSAGE', f"Error sending message: {str(e)}\n{traceback.format_exc()}"))
            return False

    def _Listen(self, plugs_info:Dict[str, Any]):
        """Listen for incoming connections
        
        Args:
            plugs_info: Dictionary with connection information
            
        Returns:
            bool: True if listening successfully, False otherwise
        """
        if not self.is_server:
            self.log(f"gRPC Plug {self.name} is not a server", 'WARNING')
            return False
            
        try:
            # Create a server
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Add the servicer to the server
            agent_pb2_grpc.add_AgentServicer_to_server(AgentServicer(self), self.server)
            
            # Add a secure port
            # if self.port is 0, try to find an open port, starting at 9000
            if self._port == 0:
                for port in range(9000, 9100):
                    try:
                        server_address = f"{self._host}:{port}"
                        self.server.add_insecure_port(server_address)
                        self._port = port
                        break
                    except Exception as e:
                        self.log(f"Error adding insecure port {port}: {str(e)}", 'ERROR')
                        continue
            else:
                server_address = f"{self._host}:{self._port}"
                self.server.add_insecure_port(server_address)
            
            # Start the server
            self.server.start()
            self.log(f"gRPC server {self.name} listening on {server_address}", 'INFO')
            
            self.running = True
            return True
        except Exception as e:
            self.log(f"Error starting gRPC server {self.name}: {str(e)}\n{traceback.format_exc()}", 'ERROR')
            return False
    # connect to remote agent
    def _Connect(self, agent:AgentAddress, plugs_info:Dict[str, Any]):
        """Connect to an agent via gRPC
        
        Args:
            agent: AgentAddress
            plugs_info: Dictionary with connection information
                {
                    "host": str,
                    "port": int
                }
                
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # if self.port is 0, try to find an open port, starting at 9000
            if self._port == 0:
                for port in range(9000, 9100):
                    try:
                        self.channel = grpc.insecure_channel(f"{self._host}:{port}")
                        self.stub = agent_pb2_grpc.AgentStub(self.channel)
                        self.connected = True
                        self._port = port
                        break
                    except Exception as e:
                        self.log(f"Error connecting to port {port}: {str(e)}", 'ERROR')
                        continue
            else:
                host = plugs_info.get('host', self._host)
                port = plugs_info.get('port', self._port)
                server_address = f"{host}:{port}"
            self.log(f"Connecting to {server_address} via gRPC Plug {self.name}", 'INFO')
            
            # Create a channel
            self.channel = grpc.insecure_channel(server_address)
            
            # Create a stub
            self.stub = agent_pb2_grpc.AgentStub(self.channel)
            
            # Set connected flag
            self.connected = True
            
            self.log(f"Connected to {server_address} via gRPC Plug {self.name}", 'INFO')
            return True
        except Exception as e:
            self.log(f"Error connecting to agent via gRPC Plug {self.name}: {str(e)}\n{traceback.format_exc()}", 'ERROR')
            self.connected = False
            return False
    
    def Connect(self):
        """Connect to the gRPC server or start a server"""
        if self.is_server:
            return self._Listen({})
        else:
            # Client mode - will connect when needed
            return True
            
    def Disconnect(self):
        """Disconnect the gRPC plug"""
        try:
            if self.server:
                self.server.stop(0)
                self.server = None
                
            self.connected = False
            self.log(f"gRPC Plug {self.name} disconnected", 'INFO')
            return True
        except Exception as e:
            self.log(f"Error disconnecting gRPC Plug {self.name}: {str(e)}", 'ERROR')
            return False

    def _Send(self, message: Dict[str, Any]):
        """Send a message via gRPC
        
        Args:
            message: Message dictionary
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self._IsConnected():
            self.log(f"gRPC Plug {self.name} is not connected", 'WARNING')
            return False
            
        if self.is_server:
            self.log(f"gRPC Plug {self.name} is a server and cannot send messages directly", 'WARNING')
            return False
            
        # Send message
        try:
            response = self.stub.Echo(agent_pb2.Message(
                content=json.dumps(message)
            ))
            self.log(f"Sent message via gRPC Plug {self.name}: {response.message}", 'INFO')
            return True
        except Exception as e:
            self.log(f"Error sending message via gRPC Plug {self.name}: {str(e)}", 'ERROR')
            return False
            
    def _send(self, message: Dict[str, Any]):
        """Alias for _Send"""
        return self._Send(message)

    def _IsConnected(self) -> bool:
        """Check if the gRPC plug is connected
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected and self.channel is not None

    def _SendMessage(self, message):
        """Send a message (can be a Message object or dict)"""
        if isinstance(message, Message):
            return self.send(message.ToJson())
        else:
            return self.send(message)

    def ReceiveMessage(self, msg_count: int = 0):
        """Receive a message via gRPC
        
        Args:
            msg_count: Number of messages to receive
            
        Returns:
            Message: Received message, or None if no message is available
        """
        # Receive message
        print(f"gRPCPlug {self.name} ReceiveMessage")
        try:
            msg = self.message_queue.pop(0)
            #print(f"Received message: {msg}")
            self.log(f"Received message: {msg}", 'DEBUG')
            return msg
        except Exception as e:
            self.log(f"Error receiving message via gRPC Plug {self.name}: {str(e)}", 'DEBUG')
            return None
    
    def _Echo(self, message: str):
        """Echo a message back
        
        Args:
            message: Message to echo
            
        Returns:
            str: Echoed message
        """
        if self.is_server:
            self.log(f"gRPC Plug {self.name} cannot echo messages", 'WARNING')
            return None
            
        try:
            # Send an echo request
            msg = agent_pb2.Message()
            msg.id = str(uuid.uuid4())
            msg.type = "echo"
            msg.content = message
            msg.timestamp = int(time.time())
            
            response = self.stub.Echo(msg)
            
            # Return the response
            return response.content
        except Exception as e:
            self.log(f"Error echoing message via gRPC Plug {self.name}: {str(e)}", 'ERROR')
            return None
    
    def register_event_handler(self, event_type: str, handler_func: Callable):
        """Register an event handler
        
        Args:
            event_type: Type of event to register for
            handler_func: Function to call when event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        self.event_handlers[event_type].append(handler_func)
        self.log(f"Registered event handler for {event_type} events in gRPC Plug {self.name}", 'INFO')
    
    def unregister_event_handler(self, event_type: str, handler_func: Optional[Callable] = None):
        """Unregister an event handler
        
        Args:
            event_type: Type of event to unregister for
            handler_func: Function to unregister, or None to unregister all
        """
        if event_type not in self.event_handlers:
            self.log(f"No handlers registered for {event_type} events in gRPC Plug {self.name}", 'WARNING')
            return
            
        if handler_func is None:
            self.event_handlers[event_type] = []
            self.log(f"Unregistered all handlers for {event_type} events in gRPC Plug {self.name}", 'INFO')
        else:
            if handler_func in self.event_handlers[event_type]:
                self.event_handlers[event_type].remove(handler_func)
                self.log(f"Unregistered handler for {event_type} events in gRPC Plug {self.name}", 'INFO')
            else:
                self.log(f"Handler not found for {event_type} events in gRPC Plug {self.name}", 'WARNING')
    
    def trigger_event(self, event_type: str, **event_data):
        """Trigger an event
        
        Args:
            event_type: Type of event to trigger
            **event_data: Data to pass to event handlers
        """
        if event_type in self.event_handlers:
            self.log(f"Triggering event {event_type} with data: {event_data}", 'DEBUG')
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_type, **event_data)
                except Exception as e:
                    self.log(f"Error in event handler for {event_type} event: {str(e)}\n{traceback.format_exc()}", 'ERROR')
    
    def start(self):
        """Start the gRPC plug"""
        return self.Connect()

    def stop(self):
        """Stop the server"""
        if self.server:
            self.server.stop(0)
            self.server = None
            self.log(f"gRPC server {self.name} stopped", 'INFO')
            return True
        return False

    def ToJson(self):
        """Convert the gRPC plug to a JSON object"""
        json_data = super().ToJson()
        json_data.update({
            "host": self._host,
            "port": self._port,
            "type": "gRPCPlug",
            "is_server": self.is_server
        })
        return json_data

    def FromJson(self, json_data):
        """Initialize the gRPC plug from a JSON object"""
        super().FromJson(json_data)
        self._host = json_data.get("host", self._host)
        self._port = json_data.get("port", self._port)
        self.is_server = json_data.get("is_server", self.is_server)
        return self
        
    def set_agent(self, agent):
        """Set the agent reference for this plug"""
        self.agent = agent
        return self

    def _Disconnect(self, agent:AgentAddress, plugs_info:Dict[str, Any]):
        """Disconnect from an agent
        
        Args:
            agent: AgentAddress
            plugs_info: Dictionary with connection information
                
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        try:
            # Close the channel
            if hasattr(self, 'channel') and self.channel:
                self.channel.close()
                self.channel = None
                self.stub = None
                self.connected = False
                
            self.log(f"Disconnected from agent via gRPC Plug {self.name}", 'INFO')
            return True
        except Exception as e:
            self.log(f"Error disconnecting from agent via gRPC Plug {self.name}: {str(e)}", 'ERROR')
            return False


