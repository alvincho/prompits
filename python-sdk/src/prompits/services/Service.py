# Service is a Pit that can be used by agents to perform actions
# Service has an owner, who is the agent that created the service
# Service may have a pool, which is the pool of agents that can use the service
# Service may have tables, which are the tables of the service

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..Pit import Pit
from ..Practice import Practice

class Service(Pit):
    def __init__(self, name: str, description: str = None):
        super().__init__(name, description or f"Service {name}")

    def ToJson(self) -> Dict[str, Any]:
        # Get base JSON data from parent which includes practices
        json_data = super().ToJson()
        
        # Make sure to preserve existing data while adding/updating service-specific fields
        json_data.update({
            "name": self.name,
            "type": "Service",
            "description": self.description
        })
        
        return json_data

    @classmethod
    def FromJson(cls, json_data: Dict[str, Any]) -> 'Service':
        return cls(
            name=json_data["name"],
            description=json_data.get("description")
        )
 

