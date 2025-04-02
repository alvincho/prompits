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

    def execute_query(self, query):
        """
        Execute a SQL query against the database.
        
        This method should be overridden by subclasses to implement
        database-specific query execution.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Any: Query results, or None if an error occurred
        """
        try:
            # Implementation of execute_query method
            return None
        except Exception as e:
            self.log(f"Error executing query: {str(e)}")
            traceback.print_exc()
            return None

    def get_data(self, table_name, data):
        """
        Retrieve data from a specified table.
        
        This method should be overridden by subclasses to implement
        database-specific data retrieval.
        
        Args:
            table_name: Name of the table to query
            data: Dictionary of conditions to filter the results
            
        Returns:
            List: List of retrieved records, or empty list if an error occurred
        """
        try:
            # Implementation of get_data method
            return []
        except Exception as e:
            self.log(f"Error getting data: {str(e)}")
            traceback.print_exc()
            return []

    def insert_data(self, table_name, data):
        """
        Insert data into a specified table.
        
        This method should be overridden by subclasses to implement
        database-specific data insertion.
        
        Args:
            table_name: Name of the table to insert into
            data: Dictionary of column-value pairs to insert
            
        Returns:
            bool: True if inserted successfully, False otherwise
        """
        try:
            # Implementation of insert_data method
            return False
        except Exception as e:
            self.log(f"Error inserting data: {str(e)}")
            traceback.print_exc()
            return False

    def update_data(self, table_name, data):
        """
        Update data in a specified table.
        
        This method should be overridden by subclasses to implement
        database-specific data updates.
        
        Args:
            table_name: Name of the table to update
            data: Dictionary containing update criteria and new values
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            # Implementation of update_data method
            return False
        except Exception as e:
            self.log(f"Error updating data: {str(e)}")
            traceback.print_exc()
            return False

    def delete_data(self, table_name, data):
        """
        Delete data from a specified table.
        
        This method should be overridden by subclasses to implement
        database-specific data deletion.
        
        Args:
            table_name: Name of the table to delete from
            data: Dictionary of conditions to determine what to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Implementation of delete_data method
            return False
        except Exception as e:
            self.log(f"Error deleting data: {str(e)}")
            traceback.print_exc()
            return False

    def TableExists(self, table_name: str) -> bool:
        """Check if a table exists."""
        raise NotImplementedError("TableExists not implemented")

    def CreateTable(self, table_name: str, schema: TableSchema):
        """Create a table with the given schema."""
        raise NotImplementedError("CreateTable not implemented")

    def _convert_to_db_value(self, value: Any, data_type: DataType) -> Any:
        """
        Convert a Python value to its database representation.
        
        This method handles type conversion between Python objects and
        database-specific data formats based on the specified data type.
        
        Args:
            value: Python value to convert
            data_type: Target data type for conversion
            
        Returns:
            Any: The converted value suitable for database storage
        """
        if value is None:
            return None
        if data_type == DataType.DATETIME:
            return value.isoformat() if isinstance(value, datetime) else value
        elif data_type == DataType.JSON:
            return json.dumps(value) if not isinstance(value, str) else value
        return value

    def _convert_from_db_value(self, value: Any, data_type: DataType) -> Any:
        """
        Convert a database value to its Python representation.
        
        This method handles type conversion between database-specific formats
        and Python objects based on the specified data type.
        
        Args:
            value: Database value to convert
            data_type: Source data type for conversion
            
        Returns:
            Any: The converted value as an appropriate Python object
        """
        if value is None:
            return None
        if data_type == DataType.DATETIME:
            return datetime.fromisoformat(value) if isinstance(value, str) else value
        elif data_type == DataType.JSON:
            return json.loads(value) if isinstance(value, str) else value
        elif data_type == DataType.INTEGER:
            return int(value)
        elif data_type == DataType.FLOAT:
            return float(value)
        elif data_type == DataType.BOOLEAN:
            return bool(value)
        return value

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate data against the schema.
        
        This method checks if the provided data conforms to the schema
        defined for this pool, validating data types and constraints.
        
        Args:
            data: Dictionary of field-value pairs to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        row_schema = self.schema.schema.get("rowSchema", {})
        for field, field_schema in row_schema.items():
            if field not in data:
                if not field_schema.get("nullable", True):
                    return False
                continue
            value = data[field]
            if value is None and not field_schema.get("nullable", True):
                return False
            if value is not None:
                data_type = DataType(field_schema["type"])
                if not data_type.validate(value):
                    return False
        return True

    def Store(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store data in the database with the specified key.
        
        Args:
            key: Unique identifier for the data
            data: Dictionary of field-value pairs to store
            
        Returns:
            bool: True if stored successfully, False otherwise
            
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Store method not implemented")

    def Retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from the database by key.
        
        Args:
            key: Unique identifier for the data to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Retrieved data, or None if not found
            
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Retrieve method not implemented")

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for data in the database that matches criteria.
        
        Args:
            where: Dictionary of conditions to filter results
            
        Returns:
            List[Dict[str, Any]]: List of matching records
            
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Search method not implemented")

    def Update(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Update data in the database by key.
        
        Args:
            key: Unique identifier for the data to update
            data: Dictionary of field-value pairs containing new values
            
        Returns:
            bool: True if updated successfully, False otherwise
            
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Update method not implemented")

    def Delete(self, key: str) -> bool:
        """
        Delete data from the database by key.
        
        Args:
            key: Unique identifier for the data to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
            
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Delete method not implemented")

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