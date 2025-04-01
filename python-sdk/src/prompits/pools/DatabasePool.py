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
    def __init__(self, name: str, description=None, connectionString=None):
        super().__init__(name, description)
        self.connectionString = connectionString
        # Add practices Query, Execute, Commit, Rollback
        self.AddPractice(Practice("Execute", self._Execute))
        self.AddPractice(Practice("Commit", self._Commit))
        self.AddPractice(Practice("Rollback", self._Rollback))

    @abstractmethod
    def _Commit(self):
        raise NotImplementedError("Commit method not implemented")

    @abstractmethod
    def _Rollback(self):
        raise NotImplementedError("Rollback method not implemented")
    
    def connect(self):
        try:
            # Implementation of connect method
            return True
        except Exception as e:
            self.log(f"Error connecting to database: {str(e)}")
            traceback.print_exc()
            return False

    def disconnect(self):
        try:
            # Implementation of disconnect method
            return True
        except Exception as e:
            self.log(f"Error disconnecting from database: {str(e)}")
            traceback.print_exc()
            return False

    def execute_query(self, query):
        try:
            # Implementation of execute_query method
            return None
        except Exception as e:
            self.log(f"Error executing query: {str(e)}")
            traceback.print_exc()
            return None

    def get_data(self, table_name, data):
        try:
            # Implementation of get_data method
            return []
        except Exception as e:
            self.log(f"Error getting data: {str(e)}")
            traceback.print_exc()
            return []

    def insert_data(self, table_name, data):
        try:
            # Implementation of insert_data method
            return False
        except Exception as e:
            self.log(f"Error inserting data: {str(e)}")
            traceback.print_exc()
            return False

    def update_data(self, table_name, data):
        try:
            # Implementation of update_data method
            return False
        except Exception as e:
            self.log(f"Error updating data: {str(e)}")
            traceback.print_exc()
            return False

    def delete_data(self, table_name, data):
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
        if value is None:
            return None
        if data_type == DataType.DATETIME:
            return value.isoformat() if isinstance(value, datetime) else value
        elif data_type == DataType.JSON:
            return json.dumps(value) if not isinstance(value, str) else value
        return value

    def _convert_from_db_value(self, value: Any, data_type: DataType) -> Any:
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
        raise NotImplementedError("Store method not implemented")

    def Retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Retrieve method not implemented")

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        raise NotImplementedError("Search method not implemented")

    def Update(self, key: str, data: Dict[str, Any]) -> bool:
        raise NotImplementedError("Update method not implemented")

    def Delete(self, key: str) -> bool:
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