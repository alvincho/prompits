"""
Plug module for communication between agents.

A Plug is a communication channel that allows agents to communicate with each other.
It provides methods for sending and receiving messages.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import threading
import time
import uuid

from .Message import Message
from .Practice import Practice
from .AgentAddress import AgentAddress
from .LogEvent import LogEvent
from .Pit import Pit

class Plug(Pit):
    """
    Abstract base class for plugs.
    
    A Plug is a communication channel that allows agents to communicate with each other.
    It provides methods for sending and receiving messages.
    Plug is a Pit, so it can have practices.
    Plug defined in the agent's info is a server to be connected by other agents.
    Agent can have multiple plugs, and each plug can have multiple connections.
    Other agents can connect to the plug by using the connect practice.
    """
    
    def __init__(self, name: str, description: str = None):
        """
        Initialize a Plug.
        
        Args:
            name: Name of the plug
            description: Description of the plug
        """
        super().__init__(name, description or f"Plug {name}")
        
        # Add practices
        self.AddPractice(Practice("SendMessage", self.SendMessage))
        self.AddPractice(Practice("ReceiveMessage", self.ReceiveMessage))
        self.AddPractice(Practice("Echo", self._Echo))
        self.AddPractice(Practice("ConnectToAgent", self._ConnectToAgent))
        self.AddPractice(Practice("DisconnectFromAgent", self._DisconnectFromAgent))

        # remote_agent is a dictionary of agent addresses and connections status
        # key is the agent address, value is a dictionary with the connection status and the plug
        self.remote_agent={}
        
    def _ConnectToAgent(self, agent:AgentAddress, plugs_info:Dict[str, Any]):
        """
        Connect to an agent.
        """
        # call the _Connect method of the subclass
        self.remote_agent[agent] = self._Connect(agent, plugs_info)
    def _DisconnectFromAgent(self):
        """
        Disconnect from an agent.
        """
        self._remove_agent()
        
    def ToJson(self):
        """
        Convert the plug to a JSON object.
        
        Returns:
            dict: JSON representation of the plug
        """
        # Create the JSON object directly instead of using super().ToJson()
        json_data = {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }
        
        # Add practices if they exist
        if hasattr(self, "practices") and self.practices:
            json_data["practices"] = {}
            for name, practice in self.practices.items():
                if hasattr(practice, "ToJson"):
                    json_data["practices"][name] = practice.ToJson()
                else:
                    json_data["practices"][name] = {
                        "name": practice.name,
                        "description": practice.description
                    }
                    
        return json_data
    
    def FromJson(self, json_data):
        """
        Initialize the plug from a JSON object.
        
        Args:
            json_data: JSON object containing plug configuration
            
        Returns:
            Plug: The initialized plug
        """
        self.name = json_data.get("name", self.name)
        self.description = json_data.get("description", self.description)
        return self

    @abstractmethod
    def _Listen(self, plugs_info:Dict[str, Any]):
        """
        Listen to the plug.
        Args:
            plugs_info: Dictionary of plugs info
        
        Returns:
            bool: True if listening successfully, False otherwise
        """
        raise NotImplementedError("Listen method must be implemented by the subclass")


    @abstractmethod

    def _Connect(self, agent:AgentAddress, plugs_info:Dict[str, Any]):
        """
        Connect the plug.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        raise NotImplementedError("Connect method must be implemented by the subclass")
    
    @abstractmethod
    def _Disconnect(self, agent:AgentAddress, plugs_info:Dict[str, Any]):
        """
        Disconnect the plug.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        raise NotImplementedError("Disconnect method must be implemented by the subclass")
    
    @abstractmethod
    def SendMessage(self, agent:AgentAddress, message: Message, plugs_info:Dict[str, Any]):
        """
        Send a message.

        Args:
            message: Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        raise NotImplementedError("SendMessage method must be implemented by the subclass")
    
    @abstractmethod
    def ReceiveMessage(self, agent:AgentAddress=None) -> Optional[Message]:
        """
        Receive a message.
        
        Returns:
            Message: Received message, or None if no message is available
        """
        raise NotImplementedError("ReceiveMessage method must be implemented by the subclass")
    
    @abstractmethod
    def _IsConnected(self) -> bool:
        """
        Check if the plug is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        raise NotImplementedError("IsConnected method must be implemented by the subclass")
    
    def _NotifyAgent(self, message: Message):
        """
        Notify the agent that a message has been received.
        
        Args:
            message: The received message
        
        Returns:
            bool: True if notification was successful, False otherwise
        """
        if hasattr(self, 'agent') and self.agent:
            try:
                self.agent.receive_message(message)
                return True
            except Exception as e:
                self.log(f"Error notifying agent: {str(e)}", 'ERROR')
                return False
        return False 
    
    def _add_agent(self, agent):
        """
        Add an agent to the plug.
        """
        self.agent = agent
        
    def _remove_agent(self):
        """
        Remove the agent from the plug.
        """
        self.agent = None
        
        