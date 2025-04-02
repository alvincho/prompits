# Service is a Pit that can be used by agents to perform actions
# Service has an owner, who is the agent that created the service
# Service may have a pool, which is the pool of agents that can use the service
# Service may have tables, which are the tables of the service

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..Pit import Pit
from ..Practice import Practice

class Service(Pit, ABC):
    """
    Service is a specialized abstract Pit that provides functionality to agents.
    
    A Service is owned by the agent that created it and can be used by other agents
    depending on access permissions. Services can provide various capabilities like
    API access, job scheduling, or data processing.
    """
    
    def __init__(self, name: str, description: str = None):
        """
        Initialize a Service instance.
        
        Args:
            name: The name of the service
            description: Optional description of the service's purpose
        """
        super().__init__(name, description or f"Service {name}")

    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the Service to a JSON-serializable dictionary.
        
        This method extends the base Pit.ToJson method to include service-specific
        fields in the serialized representation.
        
        Returns:
            Dict[str, Any]: A dictionary representation of the Service
        """
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
        """
        Create a Service instance from a JSON dictionary.
        
        This class method deserializes a JSON dictionary into a Service instance.
        
        Args:
            json_data: Dictionary containing the serialized Service data
            
        Returns:
            Service: A new Service instance initialized with the provided data
        """
        return cls(
            name=json_data["name"],
            description=json_data.get("description")
        )
 

