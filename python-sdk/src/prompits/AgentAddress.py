"""
AgentAddress module for representing agent addresses.

An AgentAddress is a unique identifier for an agent, consisting of an agent ID and a plaza name.
"""

from typing import Optional, Union, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from .Agent import Agent
    from .Plaza import Plaza

class AgentAddress:
    """
    AgentAddress for representing agent addresses.
    
    An AgentAddress is a unique identifier for an agent, consisting of an agent ID and a plaza name.
    """
    
    def __init__(self, agent_id: Optional[str], plaza_name: Optional[str]):
        """
        Initialize an AgentAddress.
        
        Args:
            agent_id: ID of the agent
            plaza_name: Name of the plaza
        """
        self.agent_id = agent_id
        self.plaza_name = plaza_name
    
    def to_string(self):
        return f"{self.agent_id}@{self.plaza_name}"
    
    # to json
    def ToJson(self):
        return {
            "agent_id": self.agent_id,
            "plaza_name": self.plaza_name
        }
    
    def __str__(self):
        """
        Convert the AgentAddress to a string.
        
        Returns:
            str: String representation of the AgentAddress
        """
        return f"{self.agent_id}@{self.plaza_name}"
    
    def __repr__(self):
        """
        Convert the AgentAddress to a string.
        
        Returns:
            str: String representation of the AgentAddress
        """
        return f"AgentAddress({self.agent_id}, {self.plaza_name})"
    
    def __eq__(self, other):
        """
        Check if two AgentAddresses are equal.
        
        Args:
            other: The other AgentAddress
            
        Returns:
            bool: True if the AgentAddresses are equal, False otherwise
        """
        if isinstance(other, AgentAddress):
            return self.agent_id == other.agent_id and self.plaza_name == other.plaza_name
        return False
    
    def __hash__(self):
        """
        Get the hash of the AgentAddress.
        
        Returns:
            int: Hash of the AgentAddress
        """
        return hash((self.agent_id, self.plaza_name))
    
    def ToJson(self):
        """
        Convert the AgentAddress to a JSON object.
        
        Returns:
            dict: JSON representation of the AgentAddress
        """
        return {
            "agent_id": self.agent_id,
            "plaza_name": self.plaza_name
        }
    
    @classmethod
    def FromJson(cls, json_data):
        """
        Initialize the AgentAddress from a JSON object.
        
        Args:
            json_data: JSON object containing AgentAddress configuration
            
        Returns:
            AgentAddress: The initialized AgentAddress
        """
        agent_id = json_data.get("agent_id")
        plaza_name = json_data.get("plaza_name")
        
        return cls(agent_id, plaza_name)
    
    @classmethod
    def FromAgent(cls, agent):
        """
        Create an AgentAddress from an agent.
        
        Args:
            agent: The agent
            
        Returns:
            AgentAddress: The AgentAddress for the agent
        """
        # Avoid circular imports
        from .Agent import Agent
        
        if isinstance(agent, Agent):
            return cls(agent.agent_id, None)
        else:
            return cls(str(agent), None)
    
    @classmethod
    def FromPlaza(cls, plaza):
        """
        Create an AgentAddress from a plaza.
        
        Args:
            plaza: The plaza
            
        Returns:
            AgentAddress: The AgentAddress for the plaza
        """
        # Avoid circular imports
        from .Plaza import Plaza
        
        if isinstance(plaza, Plaza):
            return cls(None, plaza.name)
        else:
            return cls(None, str(plaza))
