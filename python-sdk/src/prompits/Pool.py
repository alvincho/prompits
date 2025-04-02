"""
Pool module for data storage and retrieval.

A Pool is a data storage and retrieval system that can be used by agents.
It provides methods for storing, retrieving, updating, and deleting data.
"""

import uuid
import json
import threading
import time
from abc import abstractmethod, ABC
from typing import Dict, List, Any, Optional, Tuple, Union
from .Pit import Pit
from .Schema import DataType, TableSchema
from .Practice import Practice
from datetime import datetime
from .LogEvent import LogEvent

# DataItem is an abstract class that defines the data item in Pool
class DataItem(ABC):
    """
    Abstract base class for all data items stored in a Pool.
    
    DataItem represents a piece of data with identification, metadata,
    and type information. This class is extended by specific data type
    implementations like TextDataItem, IntegerDataItem, etc.
    """
    
    def __init__(self, id: str, name: str, description: str, data_type: DataType):
        """
        Initialize a DataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data_type: The data type of this item (from DataType enum)
        """
        self.id = id
        self.name = name
        self.description = description
        self.data_type = data_type

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the data item to a dictionary representation.
        
        This method must be implemented by subclasses to provide
        serialization specific to each data type.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the data item
        """
        pass

    @abstractmethod
    def to_json(self) -> str:
        """
        Convert the data item to a JSON string.
        
        This method must be implemented by subclasses to provide
        JSON serialization specific to each data type.
        
        Returns:
            str: JSON string representation of the data item
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataItem':
        """
        Create a data item from a dictionary.
        
        This method must be implemented by subclasses to provide
        deserialization specific to each data type.
        
        Args:
            data: Dictionary containing data item properties
            
        Returns:
            DataItem: New instance initialized with the data
        """
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, json_str: str) -> 'DataItem':
        """
        Create a data item from a JSON string.
        
        This method must be implemented by subclasses to provide
        JSON deserialization specific to each data type.
        
        Args:
            json_str: JSON string containing data item properties
            
        Returns:
            DataItem: New instance initialized with the data
        """
        pass

# TextDataItem is a data item that contains text
class TextDataItem(DataItem):
    """
    DataItem implementation for storing text data.
    
    TextDataItem represents a string value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: str):
        """
        Initialize a TextDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The text string to store
        """
        super().__init__(id, name, description, DataType.STRING)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the text data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the text data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the text data item to a JSON string.
        
        Returns:
            str: JSON string representation of the text data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextDataItem':
        """
        Create a TextDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the text data item properties
            
        Returns:
            TextDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", "")
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'TextDataItem':
        """
        Create a TextDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing text data item properties
            
        Returns:
            TextDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# IntegerDataItem is a data item that contains an integer
class IntegerDataItem(DataItem):
    """
    DataItem implementation for storing integer data.
    
    IntegerDataItem represents an integer value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: int):
        """
        Initialize an IntegerDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The integer value to store
        """
        super().__init__(id, name, description, DataType.INTEGER)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the integer data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the integer data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the integer data item to a JSON string.
        
        Returns:
            str: JSON string representation of the integer data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntegerDataItem':
        """
        Create an IntegerDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the integer data item properties
            
        Returns:
            IntegerDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", 0)
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'IntegerDataItem':
        """
        Create an IntegerDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing integer data item properties
            
        Returns:
            IntegerDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# RealDataItem is a data item that contains a floating point number
class RealDataItem(DataItem):
    """
    DataItem implementation for storing floating-point data.
    
    RealDataItem represents a floating-point value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: float):
        """
        Initialize a RealDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The floating-point value to store
        """
        super().__init__(id, name, description, DataType.REAL)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the real data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the real data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the real data item to a JSON string.
        
        Returns:
            str: JSON string representation of the real data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealDataItem':
        """
        Create a RealDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the real data item properties
            
        Returns:
            RealDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", 0.0)
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'RealDataItem':
        """
        Create a RealDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing real data item properties
            
        Returns:
            RealDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# ObjectDataItem is a data item that contains an object
class ObjectDataItem(DataItem):
    """
    DataItem implementation for storing dictionary/object data.
    
    ObjectDataItem represents a dictionary/object value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: Dict[str, Any]):
        """
        Initialize an ObjectDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The dictionary/object value to store
        """
        super().__init__(id, name, description, DataType.OBJECT)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the object data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the object data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the object data item to a JSON string.
        
        Returns:
            str: JSON string representation of the object data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectDataItem':
        """
        Create an ObjectDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the object data item properties
            
        Returns:
            ObjectDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", {})
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'ObjectDataItem':
        """
        Create an ObjectDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing object data item properties
            
        Returns:
            ObjectDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# BooleanDataItem is a data item that contains a boolean
class BooleanDataItem(DataItem):
    """
    DataItem implementation for storing boolean data.
    
    BooleanDataItem represents a boolean value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: bool):
        """
        Initialize a BooleanDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The boolean value to store
        """
        super().__init__(id, name, description, DataType.BOOLEAN)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the boolean data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the boolean data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the boolean data item to a JSON string.
        
        Returns:
            str: JSON string representation of the boolean data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BooleanDataItem':
        """
        Create a BooleanDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the boolean data item properties
            
        Returns:
            BooleanDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", False)
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'BooleanDataItem':
        """
        Create a BooleanDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing boolean data item properties
            
        Returns:
            BooleanDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# DateTimeDataItem is a data item that contains a datetime
class DateTimeDataItem(DataItem):
    """
    DataItem implementation for storing datetime data.
    
    DateTimeDataItem represents a datetime value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: datetime):
        """
        Initialize a DateTimeDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The datetime value to store
        """
        super().__init__(id, name, description, DataType.DATETIME)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the datetime data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the datetime data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data.isoformat()
        }

    def to_json(self) -> str:
        """
        Convert the datetime data item to a JSON string.
        
        Returns:
            str: JSON string representation of the datetime data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DateTimeDataItem':
        """
        Create a DateTimeDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the datetime data item properties
            
        Returns:
            DateTimeDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=datetime.fromisoformat(data.get("data", datetime.now().isoformat()))
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'DateTimeDataItem':
        """
        Create a DateTimeDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing datetime data item properties
            
        Returns:
            DateTimeDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# TupleDataItem is a data item that contains a tuple
class TupleDataItem(DataItem):
    """
    DataItem implementation for storing tuple data.
    
    TupleDataItem represents a tuple value stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: Tuple):
        """
        Initialize a TupleDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The tuple value to store
        """
        super().__init__(id, name, description, DataType.TUPLE)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tuple data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the tuple data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": list(self.data)  # Convert tuple to list for JSON serialization
        }

    def to_json(self) -> str:
        """
        Convert the tuple data item to a JSON string.
        
        Returns:
            str: JSON string representation of the tuple data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TupleDataItem':
        """
        Create a TupleDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the tuple data item properties
            
        Returns:
            TupleDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=tuple(data.get("data", []))  # Convert list back to tuple
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'TupleDataItem':
        """
        Create a TupleDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing tuple data item properties
            
        Returns:
            TupleDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# JsonDataItem is a data item that contains JSON data
class JsonDataItem(DataItem):
    """
    DataItem implementation for storing JSON data.
    
    JsonDataItem represents JSON data stored in a Pool, with
    associated metadata and serialization/deserialization capabilities.
    """
    
    def __init__(self, id: str, name: str, description: str, data: Union[Dict[str, Any], List, str]):
        """
        Initialize a JsonDataItem.
        
        Args:
            id: Unique identifier for the data item
            name: Name or label for the data item
            description: Description of the data item's purpose or content
            data: The JSON data to store (dictionary, list, or JSON string)
        """
        super().__init__(id, name, description, DataType.JSON)
        # If data is a string, parse it as JSON
        if isinstance(data, str):
            try:
                self.data = json.loads(data)
            except json.JSONDecodeError:
                self.data = data  # Keep as string if not valid JSON
        else:
            self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the JSON data item to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary containing all properties of the JSON data item
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the JSON data item to a JSON string.
        
        Returns:
            str: JSON string representation of the JSON data item
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JsonDataItem':
        """
        Create a JsonDataItem from a dictionary.
        
        Args:
            data: Dictionary containing the JSON data item properties
            
        Returns:
            JsonDataItem: New instance initialized with the data
        """
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", {})
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'JsonDataItem':
        """
        Create a JsonDataItem from a JSON string.
        
        Args:
            json_str: JSON string containing JSON data item properties
            
        Returns:
            JsonDataItem: New instance initialized with the data
        """
        return cls.from_dict(json.loads(json_str))

# Pool is a class that stores data items
class Pool(Pit):
    """
    A pool for storing data items.
    """
    
    def __init__(self, name: str, description: str = None):
        """
        Initialize a Pool.
        
        Args:
            name: Name of the pool
            description: Description of the pool
        """
        super().__init__(name, description or f"Pool {name}")
        self.data = {}
        self.lock = threading.Lock()
        self.board = None
        self.AddPractice(Practice("MapTypeFromDataType", self._MapTypeFromDataType))
        self.AddPractice(Practice("MapTypeToDataType", self._MapTypeToDataType))
        self.is_connected=False
        self.AddPractice(Practice("Connect", self._Connect))
        self.AddPractice(Practice("Disconnect", self._Disconnect))
        self.AddPractice(Practice("IsConnected", self._IsConnected))
        self.AddPractice(Practice("CreateTable", self._CreateTable))
        self.AddPractice(Practice("DropTable", self._DropTable))
        self.AddPractice(Practice("ListTables", self._ListTables))
        self.AddPractice(Practice("GetTableSchema", self._GetTableSchema))
        self.AddPractice(Practice("Insert", self._Insert))
        self.AddPractice(Practice("Update", self._Update))
        self.AddPractice(Practice("Delete", self._Delete))
        self.AddPractice(Practice("Query", self._Query))
        self.AddPractice(Practice("GetTableData", self._GetTableData))
        self.AddPractice(Practice("ConvertToDataType", self._ConvertToDataType))
        self.AddPractice(Practice("ConvertFromDataType", self._ConvertFromDataType))
        self.AddPractice(Practice("SupportedDataType", self._SupportedDataType))
        self.AddPractice(Practice("TableExists", self._TableExists))
        self.log_subscribers = []

    @abstractmethod
    def _CreateTable(self, table_name: str, schema: TableSchema):
        """
        Create a table in the pool.
        """
        raise NotImplementedError("CreateTable not implemented")

    @abstractmethod
    def _DropTable(self, table_name: str):
        """
        Drop a table in the pool.
        """
        raise NotImplementedError("DropTable not implemented")

    @abstractmethod
    def _ListTables(self) -> List[str]:
        """
        List all tables in the pool.
        """
        raise NotImplementedError("ListTables not implemented")

    @abstractmethod
    def _GetTableSchema(self, table_name: str) -> TableSchema:
        """
        Get the schema of a table in the pool.
        """
        raise NotImplementedError("GetTableSchema not implemented")

    @abstractmethod
    def _Insert(self, table_name: str, data: dict[str, Any], table_schema: TableSchema):
        """
        Insert data into a table in the pool.
        """
        raise NotImplementedError("Insert not implemented")

    @abstractmethod
    def _Update(self, table_name: str, data: dict[str, Any], where_clause: str, table_schema: TableSchema):
        """
        Update data in a table in the pool.
        """
        raise NotImplementedError("Update not implemented")

    @abstractmethod
    def _Delete(self, table_name: str, where_clause: str, table_schema: TableSchema):
        """
        Delete data from a table in the pool.
        """
        raise NotImplementedError("Delete not implemented")

    @abstractmethod
    def _Query(self, table_name: str, query: str, params: dict[str, Any]):
        """
        Query data from a table in the pool.
        """
        raise NotImplementedError("Query not implemented")

    @abstractmethod
    def _GetTableData(self, table_name: str, key: str) -> dict[str, Any]:
        """
        Get data from a table in the pool.
        """
        raise NotImplementedError("GetTableData not implemented")

    @abstractmethod
    def _TableExists(self, table_name: str) -> bool:
        """
        Check if a table exists in the pool.
        """
        raise NotImplementedError("TableExists not implemented")

    @abstractmethod
    def _Connect(self):
        """
        Connect to the pool.
        """
        raise NotImplementedError("Connect not implemented")
    
    @abstractmethod
    def _Disconnect(self):
        """
        Disconnect from the pool.
        """
        raise NotImplementedError("Disconnect not implemented") 

    @abstractmethod
    def _IsConnected(self) -> bool:
        """
        Check if the pool is connected.
        """
        return self.is_connected    
    
    @abstractmethod
    def _MapTypeFromDataType(self, data_type: DataType) -> str:
        """
        Map a DataType to pool's data type.
        """
        raise NotImplementedError("MapTypeFromDataType not implemented")

    @abstractmethod
    def _MapTypeToDataType(self, data_type: str) -> DataType:
        """
        Map a pool's data type to a DataType.
        """
        raise NotImplementedError("MapTypeToDataType not implemented")

    @abstractmethod
    def _ConvertToDataType(self, data_type: DataType, data: Any) -> Any:
        """
        Convert data to a DataType.
        """
        raise NotImplementedError("ConvertToDataType not implemented")

    @abstractmethod
    def _ConvertFromDataType(self, data_type: DataType, data: Any) -> Any:
        """
        Convert data from a DataType to a Python object.
        """
        raise NotImplementedError("ConvertFromDataType not implemented")

    def _SupportedDataType(self) -> List[DataType]:
        """
        Return a list of supported DataType by checking MapTypeFromDataType.
        
        Returns:
            List[DataType]: List of supported DataType
        """
        supported_types = []
        for data_type in DataType:
            try:
                self.MapTypeFromDataType(data_type)
                supported_types.append(data_type)
            except NotImplementedError:
                pass
            except ValueError:
                pass
        return supported_types

    @abstractmethod
    def ToJson(self):
        """
        Convert the pool to a JSON object.
        
        Returns:
            dict: JSON representation of the pool
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }

    @abstractmethod
    def FromJson(self, json_data):
        """
        Initialize the pool from a JSON object.
        
        Args:
            json_data: JSON object containing pool configuration
            
        Returns:
            Pool: The initialized pool
        """
        self.name = json_data.get("name", self.name)
        self.description = json_data.get("description", self.description)
        return self
    
    def subscribe_to_logs(self, callback):
        """Subscribe to log events."""
        self.log_subscribers.append(callback)

    def unsubscribe_from_logs(self, callback):
        """Unsubscribe from log events."""
        if callback in self.log_subscribers:
            self.log_subscribers.remove(callback)

    def log(self, message: str, level: str = 'INFO'):
        """Log a message and trigger log events."""
        # Call the parent class log method to ensure proper event creation and propagation
        super().log(message, level)

    def connect(self):
        """Connect to the pool."""
        raise NotImplementedError("connect not implemented")

    def disconnect(self):
        """Disconnect from the pool."""
        raise NotImplementedError("disconnect not implemented")

    def Store(self, id: str, data: Dict[str, Any]):
        """Store data in the pool."""
        raise NotImplementedError("Store not implemented")

    def Retrieve(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the pool."""
        raise NotImplementedError("Retrieve not implemented")

    def Update(self, id: str, data: Dict[str, Any]):
        """Update data in the pool."""
        raise NotImplementedError("Update not implemented")

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search data in the pool."""
        raise NotImplementedError("Search not implemented")

    def Delete(self, id: str):
        """Delete data from the pool."""
        raise NotImplementedError("Delete not implemented")

    def ToJson(self) -> Dict:
        """Convert pool to JSON representation."""
        return {
            "name": self.name,
            "type": "Pool"
        }

class MemoryPool(Pool):
    """A pool that stores data in memory."""
    def __init__(self, name: str):
        """
        Initialize a MemoryPool.
        
        Args:
            name: Name of the memory pool
        """
        super().__init__(name)
        self.data = {}

    def connect(self):
        """Connect to the pool (no-op for memory pool)."""
        return True

    def disconnect(self):
        """Disconnect from the pool (no-op for memory pool)."""
        return True

    def Store(self, id: str, data: Dict[str, Any]):
        """Store data in memory."""
        try:
            self.data[id] = data.copy()
            self.log(f"Stored data with id {id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error storing data: {e}", 'ERROR')
            return False

    def Retrieve(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from memory."""
        try:
            if id in self.data:
                self.log(f"Retrieved data with id {id}", 'DEBUG')
                return self.data[id].copy()
            self.log(f"Data with id {id} not found", 'WARNING')
            return None
        except Exception as e:
            self.log(f"Error retrieving data: {e}", 'ERROR')
            return None

    def Update(self, id: str, data: Dict[str, Any]):
        """Update data in memory."""
        try:
            if id in self.data:
                self.data[id].update(data)
                self.log(f"Updated data with id {id}", 'DEBUG')
                return True
            self.log(f"Data with id {id} not found", 'WARNING')
            return False
        except Exception as e:
            self.log(f"Error updating data: {e}", 'ERROR')
            return False

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search data in memory."""
        try:
            results = []
            for id, data in self.data.items():
                match = True
                for key, value in where.items():
                    if key not in data or data[key] != value:
                        match = False
                        break
                if match:
                    results.append(data.copy())
            self.log(f"Found {len(results)} matching records", 'DEBUG')
            return results
        except Exception as e:
            self.log(f"Error searching data: {e}", 'ERROR')
            return []

    def Delete(self, id: str):
        """Delete data from memory."""
        try:
            if id in self.data:
                del self.data[id]
                self.log(f"Deleted data with id {id}", 'DEBUG')
                return True
            self.log(f"Data with id {id} not found", 'WARNING')
            return False
        except Exception as e:
            self.log(f"Error deleting data: {e}", 'ERROR')
            return False

    def ToJson(self) -> Dict:
        """Convert pool to JSON representation."""
        return {
            "name": self.name,
            "type": "MemoryPool",
            "data_count": len(self.data)
        }
