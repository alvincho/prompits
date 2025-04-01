# StatusMessage is a message that is used to report the status of an agent

from datetime import datetime
from typing import Dict, Any, Optional
from ..AgentAddress import AgentAddress

class StatusMessage:
    def __init__(self, agent_address: AgentAddress, status: str, timestamp: Optional[datetime] = None):
        self.agent_address = agent_address
        self.status = status
        self.timestamp = timestamp or datetime.now()

    def ToJson(self) -> Dict[str, Any]:
        return {
            "agent_address": self.agent_address.ToJson(),
            "status": self.status,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def FromJson(json_data: Dict[str, Any]) -> 'StatusMessage':
        agent_address = AgentAddress.FromJson(json_data["agent_address"])
        status = json_data["status"]
        timestamp = datetime.fromisoformat(json_data["timestamp"])
        return StatusMessage(agent_address, status, timestamp)