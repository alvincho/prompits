# DatabasePool is a pool that can store and retrieve information from a database.
# DatabasePool is a subclass of Pool.
# DatabasePool is an abstract class.
# DatabasePool has practices to Query, Execute, Commit, Rollback, ListTables, ListSchemas, CreateTablee

from abc import ABC, abstractmethod
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..Schema import TableSchema, DataType
from ..Pool import Pool
from ..Practice import Practice

class DatabasePool(Pool, ABC):
    """
    Abstract base class for database-specific pool implementations.
    
    DatabasePool provides a common interface for interacting with different
    database systems. It defines methods for executing queries, managing
    transactions, and performing CRUD operations.
    
    This class should be subclassed to implement specific database adapters.
    """
    
    def __init__(self, name: str, description=None, connectionString=None):
        """
        Initialize a DatabasePool.
        
        Args:
            name: Name of the database pool
            description: Description of the pool's purpose
            connectionString: Connection string for the database
        """
        super().__init__(name, description)
        self.connectionString = connectionString
        # Add practices Query, Execute, Commit, Rollback
        self.AddPractice(Practice("Select", self._Select))
        self.AddPractice(Practice("Execute", self._Execute))
        self.AddPractice(Practice("Commit", self._Commit))
        self.AddPractice(Practice("Rollback", self._Rollback))

    @abstractmethod
    def _Commit(self):
        """
        Commit the current transaction.
        
        This method should be implemented by subclasses to commit any
        pending database changes.
        
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Commit method not implemented")

    @abstractmethod
    def _Select(self, query: str, params: Dict[str, Any]):
        """
        Select data from the database.
        """
        raise NotImplementedError("Select method not implemented")

    @abstractmethod
    def _Execute(self, query: str, params: Dict[str, Any]):
        """
        Execute a query.
        """
        raise NotImplementedError("Execute method not implemented")

    @abstractmethod
    def _Rollback(self):
        """
        Rollback the current transaction.
        
        This method should be implemented by subclasses to revert any
        pending database changes.
        
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Rollback method not implemented")
    
    def connect(self):
        """
        Establish a connection to the database.
        
        This method should be overridden by subclasses to implement
        database-specific connection logic.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Implementation of connect method
            return True
        except Exception as e:
            self.log(f"Error connecting to database: {str(e)}")
            traceback.print_exc()
            return False

    def disconnect(self):
        """
        Close the connection to the database.
        
        This method should be overridden by subclasses to implement
        database-specific disconnection logic.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        try:
            # Implementation of disconnect method
            return True
        except Exception as e:
            self.log(f"Error disconnecting from database: {str(e)}")
            traceback.print_exc()
            return False

    def ToJson(self) -> Dict[str, Any]:
        """Convert DatabasePool to JSON representation."""
        # Get base JSON data from Pit which includes practices
        json_data = super().ToJson()
        
        # Add DatabasePool specific fields
        json_data.update({
            "type": "DatabasePool"
        })
        
        # Add schema if it exists
        if hasattr(self, "schema") and self.schema:
            json_data["schema"] = self.schema.ToJson()
            
        return json_data