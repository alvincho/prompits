# StatusMessage is a message that is used to report the status of an agent

from datetime import datetime
from typing import Dict, Any, Optional
from ..AgentAddress import AgentAddress

class StatusMessage:
    """
    Message used to report the status of an agent.
    
    StatusMessage contains information about an agent's current state,
    including its address, status value, and the timestamp when the
    status was recorded.
    """
    
    def __init__(self, agent_address: AgentAddress, status: str, timestamp: Optional[datetime] = None):
        """
        Initialize a StatusMessage instance.
        
        Args:
            agent_address: Address of the agent reporting its status
            status: Status value (e.g., "online", "offline", "busy")
            timestamp: Optional timestamp when the status was recorded
                       (defaults to current time)
        """
        self.agent_address = agent_address
        self.status = status
        self.timestamp = timestamp or datetime.now()

    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the status message to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the status message
        """
        return {
            "agent_address": self.agent_address.ToJson(),
            "status": self.status,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'StatusMessage':
        """
        Create a StatusMessage from JSON data.
        
        Args:
            json_data: Dictionary containing serialized status message data
            
        Returns:
            StatusMessage: New instance initialized with the data
        """
        agent_address = AgentAddress.FromJson(json_data["agent_address"])
        status = json_data["status"]
        timestamp = datetime.fromisoformat(json_data["timestamp"])
        return StatusMessage(agent_address, status, timestamp)