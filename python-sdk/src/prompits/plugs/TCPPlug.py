"""
!!! This is not implemented yet.

TCP Plug module for communication between agents over TCP sockets.

A TCP Plug allows agents to communicate with each other over TCP sockets.
It provides methods for sending and receiving TCP messages.
"""

import json
import traceback

import threading
import time
import socket
import uuid
import struct
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

from prompits.Practice import Practice

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ..Plug import Plug
    from ..Message import Message
    from ..AgentAddress import AgentAddress
else:
    # Import the base classes directly
    from ..Plug import Plug
    from ..Message import Message
    from ..Practice import Practice
class TCPPlug(Plug):
    """
    TCP Plug for communication between agents.
    
    A TCP Plug allows agents to communicate with each other over TCP sockets.
    It provides methods for sending and receiving TCP messages.
    """
    
    def __init__(self, name: str, description: str = None, host: str = "localhost", port: int = 9000, is_server: bool = False):
        """
        Initialize a TCP Plug.
        
        Args:
            name: Name of the plug
            description: Description of the plug
            host: Host to connect to (for client) or bind to (for server)
            port: Port to connect to (for client) or bind to (for server)
            is_server: Whether this plug is a server or client
        """
        super().__init__(name, description or f"TCP Plug {name}")
        # if host is *, then use all ip addresses of the machine
        if host == "*":
            self.host = "0.0.0.0"
        else:
            self.host = host
        # if port =0, then use a random port, try starting at 9000 and incrementing by 1
        if port == 0:
            self.port = 9000
            while True:
                try:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.bind((self.host, self.port))    
                    break
                except Exception as e:
                    self.port += 1
        else:   
            self.port = port
        self.is_server = is_server
        self.connected = False
        self.socket = None
        self.server_socket = None
        self.client_sockets = []
        self.message_queue = []
        self.message_lock = threading.Lock()
        self.running = False
        self.server_thread = None
        self.receiver_thread = None
        self.event_handlers = {}  # Dictionary to store event handlers
        
        # Add TCP-specific practices
        
    def ToJson(self):
        """
        Convert the TCP plug to a JSON object.
        
        Returns:
            dict: JSON representation of the TCP plug
        """
        #print("Practices:",[practice for practice in self.practices.keys()])
        json_data = super().ToJson()
        #print(json_data," from super()")
        # host is all the ip addresses of the machine not hostname
        host_info = socket.gethostbyname_ex(socket.gethostname())
        json_data.update({
            "host": host_info[2],
            "port": self.port,
            "is_server": self.is_server
        })
        #print(json_data," from ToJson")
        return json_data
    
    def FromJson(self, json_data):
        """
        Initialize the TCP plug from a JSON object.
        
        Args:
            json_data: JSON object containing TCP plug configuration
            
        Returns:
            TCPPlug: The initialized TCP plug
        """
        super().FromJson(json_data)
        self.host = json_data.get("host", self.host)
        self.port = json_data.get("port", self.port)
        self.is_server = json_data.get("is_server", self.is_server)
        return self
    
    def connect(self):
        """
        Connect the TCP plug.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.connected:
            print(f"TCP Plug {self.name} is already connected")
            return True
        print(f"Connecting TCP Plug {self.name} to {self.host}:{self.port}")
        try:
            if self.is_server:
                # Create a server socket
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(5)
                
                # Start the server thread
                self.running = True
                self.server_thread = threading.Thread(
                    target=self._server_loop,
                    daemon=True
                )
                self.server_thread.start()
                
                print(f"TCP Plug {self.name} listening on {self.host}:{self.port}")
                self.connected = True
                return True
            else:
                # Create a client socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                
                # Start the receiver thread
                self.running = True
                self.receiver_thread = threading.Thread(
                    target=self._receiver_loop,
                    daemon=True
                )
                self.receiver_thread.start()
                
                print(f"TCP Plug {self.name} connected to {self.host}:{self.port}")
                self.connected = True
                return True
        except Exception as e:
            print(f"Error connecting TCP Plug {self.host}:{self.port}: {str(e)} (test)")
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            if self.socket:
                self.socket.close()
                self.socket = None
            traceback.print_exc()
            return False
    
    def disconnect(self):
        """
        Disconnect the TCP plug.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        if not self.connected:
            print(f"TCP Plug {self.name} is not connected")
            return True
        
        try:
            # Stop the threads
            self.running = False
            
            # Close the sockets
            if self.is_server:
                if self.server_socket:
                    self.server_socket.close()
                    self.server_socket = None
                
                # Close all client sockets
                for client_socket in self.client_sockets:
                    try:
                        client_socket.close()
                    except:
                        pass
                self.client_sockets = []
            else:
                if self.socket:
                    self.socket.close()
                    self.socket = None
            
            # Wait for threads to finish
            if self.server_thread:
                self.server_thread.join(timeout=1)
                self.server_thread = None
            
            if self.receiver_thread:
                self.receiver_thread.join(timeout=1)
                self.receiver_thread = None
            
            self.connected = False
            print(f"Disconnected TCP Plug {self.name}")
            return True
        except Exception as e:
            print(f"Error disconnecting TCP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            return False
    
    def _send(self, message: Dict[str, Any]):
        """
        Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.connected:
            print(f"TCP Plug {self.name} is not connected")
            return False
        
        try:
            # Convert message to JSON
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            # Prefix the message with its length
            message_length = len(message_bytes)
            length_prefix = struct.pack('!I', message_length)
            
            if self.is_server:
                # Send to all connected clients
                for client_socket in self.client_sockets:
                    try:
                        client_socket.sendall(length_prefix + message_bytes)
                    except:
                        # Remove the client if sending fails
                        try:
                            client_socket.close()
                        except:
                            pass
                        self.client_sockets.remove(client_socket)
            else:
                # Send to the server
                self.socket.sendall(length_prefix + message_bytes)
            
            print(f"Sent message via TCP Plug {self.name}")
            return True
        except Exception as e:
            print(f"Error sending message via TCP Plug {self.name}: {str(e)}")
            traceback.print_exc()
            return False
    
    def receive(self) -> Optional[Message]:
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
        Check if the TCP plug is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def send_message(self, message):
        """
        Send a message.
        
        Args:
            message: Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Lazy import to avoid circular imports
        from ..Message import Message
        
        if isinstance(message, Message):
            return self._send(message.ToJson())
        else:
            return self._send(message)
    
    def receive_message(self):
        """
        Receive a message.
        
        Returns:
            dict: Received message, or None if no message is available
        """
        return self.receive()
    
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
    
    def register_event_handler(self, event_type: str, handler_func):
        """
        Register an event handler for a specific event type.
        
        Args:
            event_type: Type of event to handle (e.g., 'connection', 'message')
            handler_func: Function to call when the event occurs
            
        Returns:
            bool: True if registered successfully, False otherwise
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler_func)
        print(f"Registered event handler for {event_type} events in TCP Plug {self.name}")
        return True
    
    def unregister_event_handler(self, event_type: str, handler_func=None):
        """
        Unregister an event handler.
        
        Args:
            event_type: Type of event
            handler_func: Function to unregister. If None, unregister all handlers for this event type.
            
        Returns:
            bool: True if unregistered successfully, False otherwise
        """
        if event_type not in self.event_handlers:
            print(f"No handlers registered for {event_type} events in TCP Plug {self.name}")
            return False
        
        if handler_func is None:
            # Unregister all handlers for this event type
            self.event_handlers[event_type] = []
            print(f"Unregistered all handlers for {event_type} events in TCP Plug {self.name}")
            return True
        
        if handler_func in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler_func)
            print(f"Unregistered handler for {event_type} events in TCP Plug {self.name}")
            return True
        
        print(f"Handler not found for {event_type} events in TCP Plug {self.name}")
        return False
    
    def trigger_event(self, event_type: str, **event_data):
        """
        Trigger an event and call all registered handlers.
        
        Args:
            event_type: Type of event
            **event_data: Data to pass to the handlers
            
        Returns:
            bool: True if any handlers were called, False otherwise
        """
        print(f"Triggering event {event_type} with data {event_data}")
        if event_type not in self.event_handlers or not self.event_handlers[event_type]:
            return False
        
        for handler in self.event_handlers[event_type]:
            try:
                handler(self, **event_data)
            except Exception as e:
                print(f"TCPPlug.trigger_event: Error in event handler for {event_type} event: {str(e)}")
                print(f"TCPPlug.trigger_event: Event data: {event_data}")
                # print the stack trace
                traceback.print_exc()
        
        return True
    
    def _server_loop(self):
        """
        Server loop for accepting client connections.
        """
        print(f"TCP Plug {self.name} server loop started")
        
        while self.running:
            try:
                # Accept a client connection
                client_socket, client_address = self.server_socket.accept()
                print(f"TCP Plug {self.name} accepted connection from {client_address}")
                
                # Add the client socket to the list
                self.client_sockets.append(client_socket)
                
                # Trigger connection event
                self.trigger_event('connection', client_socket=client_socket, client_address=client_address)
                
                # Start a receiver thread for this client
                client_thread = threading.Thread(
                    target=self._client_receiver_loop,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting client connection: {str(e)}")
                    traceback.print_exc()
                    time.sleep(1)
        
        print(f"TCP Plug {self.name} server loop stopped")
    
    def _client_receiver_loop(self, client_socket, client_address):
        """
        Receiver loop for a client connection.
        
        Args:
            client_socket: Client socket
            client_address: Client address
        """
        print(f"TCP Plug {self.name} client receiver loop started for {client_address}")
        
        while self.running:
            try:
                # Receive the message length prefix
                length_prefix = client_socket.recv(4)
                if not length_prefix:
                    # Connection closed
                    break
                
                # Unpack the message length
                message_length = struct.unpack('!I', length_prefix)[0]
                
                # Receive the message
                message_bytes = b''
                bytes_received = 0
                
                while bytes_received < message_length:
                    chunk = client_socket.recv(min(4096, message_length - bytes_received))
                    if not chunk:
                        # Connection closed
                        break
                    message_bytes += chunk
                    bytes_received += len(chunk)
                
                if bytes_received < message_length:
                    # Connection closed before receiving the full message
                    break
                
                # Decode the message
                message_json = message_bytes.decode('utf-8')
                message = json.loads(message_json)
                
                # Add the message to the queue
                with self.message_lock:
                    self.message_queue.append(message)
                
                print(f"Received message from {client_address} via TCP Plug {self.name}")
                
                # Trigger message event
                self.trigger_event('message', message=message, client_socket=client_socket, client_address=client_address)
                
                # Notify the agent about the received message
                self.notify_agent(message)
            except Exception as e:
                if self.running:
                    print(f"Error receiving message from {client_address}: {str(e)}")
                    traceback.print_exc()
                    break
        
        # Remove the client socket from the list
        if client_socket in self.client_sockets:
            self.client_sockets.remove(client_socket)
        
        # Close the client socket
        try:
            client_socket.close()
        except:
            pass
        
        print(f"TCP Plug {self.name} client receiver loop stopped for {client_address}")
    
    def _receiver_loop(self):
        """
        Receiver loop for client mode.
        """
        print(f"TCP Plug {self.name} receiver loop started")
        
        while self.running:
            try:
                # Receive the message length prefix
                length_prefix = self.socket.recv(4)
                if not length_prefix:
                    # Connection closed
                    break
                
                # Unpack the message length
                message_length = struct.unpack('!I', length_prefix)[0]
                
                # Receive the message
                message_bytes = b''
                bytes_received = 0
                
                while bytes_received < message_length:
                    chunk = self.socket.recv(min(4096, message_length - bytes_received))
                    if not chunk:
                        # Connection closed
                        break
                    message_bytes += chunk
                    bytes_received += len(chunk)
                
                if bytes_received < message_length:
                    # Connection closed before receiving the full message
                    break
                
                # Decode the message
                message_json = message_bytes.decode('utf-8')
                message = json.loads(message_json)
                
                # Add the message to the queue
                with self.message_lock:
                    self.message_queue.append(message)
                
                print(f"Received message via TCP Plug {self.name}")
                
                # Trigger message event
                self.trigger_event('message', message=message, client_socket=self.socket, client_address=None)
                
                # Notify the agent about the received message
                self.notify_agent(message)
            except Exception as e:
                if self.running:
                    print(f"Error receiving message: {str(e)}")
                    traceback.print_exc()
                    break
        
        print(f"TCP Plug {self.name} receiver loop stopped") 