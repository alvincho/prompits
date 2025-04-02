# Plaza is a service provide agents to store and retrieve data
# it is a Pit and abstract class
# it has predefiineed schema for the data that can be stored
# it has StoreAd, RetrieveAd, UpdateAd, SearchAd, DeleteAd practices

from datetime import datetime
import json
from typing import Dict, Any, List, Optional
from .Schema import TableSchema
from .Practice import Practice
from .LogEvent import LogEvent
from .Pool import Pool
from .pools.DatabasePool import DatabasePool
from .Pit import Pit

class Ad:
    """
    Represents an advertisement stored in a Plaza.
    
    An Ad contains an identifier and associated data that can be stored,
    retrieved, updated, and deleted from a Plaza's database pool.
    """
    
    def __init__(self, id: str, data: dict):
        """
        Initialize an Ad instance.
        
        Args:
            id: Unique identifier for the advertisement
            data: Dictionary containing the advertisement data
        """
        self.id = id
        self.data = data

class Plaza(Pit):
    """
    Service that provides storage and retrieval capabilities for agents.
    
    Plaza acts as a central marketplace where agents can store, retrieve, update,
    search, and delete data. It works with a database pool to persist data and
    uses a predefined schema to validate and structure the data being stored.
    """
    
    def __init__(self, name: str, description: str, table_schema: TableSchema, pool: DatabasePool):
        """
        Initialize a Plaza instance.
        
        Args:
            name: The name of the plaza
            description: Description of the plaza's purpose
            table_schema: Schema defining the structure of data that can be stored
            pool: Database pool for storing and retrieving data
        """
        super().__init__(name, description or f"Plaza {name}")
        self.set_schema(table_schema)
        self.pool = pool

    def ToJson(self):
        """
        Convert the Plaza to a JSON-serializable dictionary.
        
        Returns:
            dict: Dictionary representation of the Plaza
        """
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.schema.ToJson(),
            "pool": self.pool.ToJson()
        }
    
    def FromJson(self, json: dict):
        """
        Initialize the Plaza from a JSON dictionary.
        
        Args:
            json: Dictionary containing the serialized Plaza data
            
        Returns:
            Plaza: Self reference for method chaining
        """
        self.name = json["name"]
        self.description = json["description"]
        self.schema = TableSchema.FromJson(json["schema"])
        self.pool = DatabasePool.FromJson(json["pool"])
        return self
        
    def set_schema(self, schema: dict):
        """
        Set the schema for the Plaza.
        
        Args:
            schema: Table schema defining the structure of data that can be stored
        """
        self.schema = schema

    # Store an ad in the plaza's pool
    def StoreAd(self, table_name: str, ad: Ad):
        """
        Store an advertisement in the plaza's pool.
        
        Args:
            table_name: Name of the table to store the ad in
            ad: The Advertisement object to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.pool.Store(ad.id, ad.data)

    def RetrieveAd(self, table_name: str, id: str):
        """
        Retrieve an advertisement from the plaza's pool.
        
        Args:
            table_name: Name of the table to retrieve from
            id: ID of the advertisement to retrieve
            
        Returns:
            Optional[Dict]: The retrieved advertisement data, or None if not found
        """
        return self.pool.Retrieve(id)

    def UpdateAd(self, table_name: str, id: str, data: dict):
        """
        Update an advertisement in the plaza's pool.
        
        Args:
            table_name: Name of the table containing the ad
            id: ID of the advertisement to update
            data: New data to update the advertisement with
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.pool.Update(table_name, id, data)

    def SearchAd(self, table_name: str, where: dict):
        """
        Search for advertisements in the plaza's pool.
        
        Args:
            table_name: Name of the table to search in
            where: Dictionary of conditions for the search
            
        Returns:
            List[Dict]: List of matching advertisements
        """
        return self.pool.Search(table_name, where)

    def DeleteAd(self, id: str):
        """
        Delete an advertisement from the plaza's pool.
        
        Args:
            id: ID of the advertisement to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.pool.Delete(id)

    def Store(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data in the plaza using the specified key.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            key: Unique identifier for the data
            data: Data to store
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        raise NotImplementedError("Store method not implemented")

    def Retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from the plaza using the specified key.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            key: Unique identifier for the data to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The retrieved data, or None if not found
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        raise NotImplementedError("Retrieve method not implemented")

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for data in the plaza matching the specified conditions.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            where: Dictionary of conditions for the search
            
        Returns:
            List[Dict[str, Any]]: List of matching data items
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        raise NotImplementedError("Search method not implemented")

    def Update(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Update data in the plaza using the specified key.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            key: Unique identifier for the data to update
            data: New data to update with
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        raise NotImplementedError("Update method not implemented")

    def Delete(self, key: str) -> bool:
        """
        Delete data from the plaza using the specified key.
        
        This is an abstract method that must be implemented by subclasses.
        
        Args:
            key: Unique identifier for the data to delete
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass
        """
        raise NotImplementedError("Delete method not implemented")

    def ToJson(self) -> Dict[str, Any]:
        """
        Convert the Plaza to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the Plaza
        """
        return {
            "name": self.name,
            "type": "Plaza",
            "pool": self.pool.ToJson() if self.pool else None,
            "schema": self.schema.ToJson() if self.schema else None
        }
