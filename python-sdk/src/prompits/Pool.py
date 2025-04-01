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
    def __init__(self, id: str, name: str, description: str, data_type: DataType):
        self.id = id
        self.name = name
        self.description = description
        self.data_type = data_type

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def to_json(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataItem':
        pass

    @classmethod
    @abstractmethod
    def from_json(cls, json_str: str) -> 'DataItem':
        pass

# TextDataItem is a data item that contains text
class TextDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: str):
        super().__init__(id, name, description, DataType.STRING)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", "")
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'TextDataItem':
        return cls.from_dict(json.loads(json_str))

# IntegerDataItem is a data item that contains an integer
class IntegerDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: int):
        super().__init__(id, name, description, DataType.INTEGER)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntegerDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", 0)
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'IntegerDataItem':
        return cls.from_dict(json.loads(json_str))

# RealDataItem is a data item that contains a floating point number
class RealDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: float):
        super().__init__(id, name, description, DataType.REAL)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", 0.0)
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'RealDataItem':
        return cls.from_dict(json.loads(json_str))

# ObjectDataItem is a data item that contains an object
class ObjectDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: Dict[str, Any]):
        super().__init__(id, name, description, DataType.OBJECT)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", {})
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'ObjectDataItem':
        return cls.from_dict(json.loads(json_str))

# BooleanDataItem is a data item that contains a boolean
class BooleanDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: bool):
        super().__init__(id, name, description, DataType.BOOLEAN)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BooleanDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", False)
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'BooleanDataItem':
        return cls.from_dict(json.loads(json_str))

# DateTimeDataItem is a data item that contains a datetime
class DateTimeDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: float):
        super().__init__(id, name, description, DataType.DATETIME)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DateTimeDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", time.time())
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'DateTimeDataItem':
        return cls.from_dict(json.loads(json_str))

# TupleDataItem is a data item that contains a tuple
class TupleDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: Tuple):
        super().__init__(id, name, description, DataType.ARRAY)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": list(self.data)
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TupleDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=tuple(data.get("data", ()))
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'TupleDataItem':
        return cls.from_dict(json.loads(json_str))

# JsonDataItem is a data item that contains a json object
class JsonDataItem(DataItem):
    def __init__(self, id: str, name: str, description: str, data: Union[Dict[str, Any], List[Any]]):
        super().__init__(id, name, description, DataType.JSON)
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.data_type.value,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JsonDataItem':
        item = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            data=data.get("data", {})
        )
        return item

    @classmethod
    def from_json(cls, json_str: str) -> 'JsonDataItem':
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
