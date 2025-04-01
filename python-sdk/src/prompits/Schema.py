# Schema is an abstract class that defines the schema of data in Pool
# it defines data structure of TupleDataItem and JsonDataItem
# it can be used to validate data in Pool

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import jsonschema
from datetime import datetime

# an enum class for data types
class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    REAL = "real"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    JSON = "json"
    OBJECT = "object"
    ARRAY = "array"
    GRAPH = "graph"
    VECTOR = "vector"
    UUID = "uuid"
    NULL = "null"
    
    @classmethod
    def from_string(cls, type_str: str):
        """
        Convert a string to a DataType enum value.
        
        Args:
            type_str: String representation of the data type
            
        Returns:
            DataType: The corresponding DataType enum value
        """
        type_map = {
            "string": cls.STRING,
            "integer": cls.INTEGER,
            "real": cls.FLOAT,
            "number": cls.FLOAT,  # For backward compatibility
            "boolean": cls.BOOLEAN,
            "datetime": cls.DATETIME,
            "json": cls.JSON,
            "object": cls.OBJECT,
            "array": cls.ARRAY,
            "null": cls.NULL,
            "graph": cls.GRAPH,
            "vector": cls.VECTOR
        }
        return type_map.get(type_str.lower(), cls.STRING)
    
    def validate_value(self, value: Any) -> bool:
        """
        Validate a value against this data type.
        
        Args:
            value: Value to validate
            
        Returns:
            bool: True if the value is valid for this data type
        """
        if self == DataType.STRING:
            return isinstance(value, str)
        elif self == DataType.INTEGER:
            return isinstance(value, int)
        elif self == DataType.FLOAT:
            return isinstance(value, float)
        elif self == DataType.BOOLEAN:
            return isinstance(value, bool)
        elif self == DataType.DATETIME:
            return isinstance(value, datetime)
        elif self == DataType.JSON:
            return isinstance(value, (dict, list))
        elif self == DataType.OBJECT:
            return isinstance(value, dict)
        elif self == DataType.ARRAY:
            return isinstance(value, list)
        elif self == DataType.NULL:
            return value is None
        return False

class Schema(ABC):
    def __init__(self, name: str, description: str, schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.schema = schema
        # check schema is a valid json schema 
        try:
            jsonschema.validate(schema, {})
        except Exception as e:
            raise ValueError(f"Invalid schema: {e}")

    @abstractmethod
    def validate(self, data: Any) -> bool:
        pass
    
    def get_field_type(self, field_name: str) -> DataType:
        """
        Get the data type of a field in the schema.
        
        Args:
            field_name: Name of the field
            
        Returns:
            DataType: The data type of the field
        """
        if field_name not in self.schema.get("properties", {}):
            return DataType.STRING
        
        field_schema = self.schema["properties"][field_name]
        type_str = field_schema.get("type", "string")
        return DataType.from_string(type_str)


# TableSchema is a json schema for a table
# contains name, description, primary key, and rowSchema
# rowSchema is a json schema for a row of the table
# Example:
# {
#     "name": "table_name",
#     "description": "description",
#     "primary_key": ["field_name1", "field_name2"],
#     "rowSchema": {
#         "description": "description",
#         "columns": [
#             {
#                 "name": "field1",
#                 "description": "description",
#                 "type": "STRING"
#             },
#             {
#                 "name": "field2",
#                 "description": "description",
#                 "type": "JSON"
#             }
#         ]
#     ]
# }

class TableSchema(Schema):
    def __init__(self, schema: Dict[str, Any]):
        super().__init__(schema["name"], schema["description"], schema)
        self.schema = schema
        self.rowSchema = RowSchema(schema["rowSchema"])
        self.primary_key = schema["primary_key"]
        self.name = schema["name"]
        self.description = schema["description"]
    
    def validate(self, data: Any) -> bool:
        # validate data is a schema for create table
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        if "name" not in data:
            raise ValueError("Data must have name")
        if "tables" not in data:
            raise ValueError("Data must have tables")
        if not isinstance(data["tables"], list):
            raise ValueError("Tables must be a list")
        for table in data["tables"]:
            if not isinstance(table, dict):
                raise ValueError("Table must be a dictionary")
            if "name" not in table:
                raise ValueError("Table must have name")
            if "rowSchema" not in table:
                raise ValueError("Table must have schema")
            # validate rowSchema is a RowSchema
            if not isinstance(table["rowSchema"], RowSchema):
                raise ValueError("RowSchema must be a RowSchema")
            
        return True
    
    def ToJson(self):
        return self.schema

class RowSchema(Schema):
    def __init__(self, schema: Dict[str, Any]):
        super().__init__("row", "datarow", schema)
        self.schema = schema
        self.columns = {key:schema[key] for key in schema.keys()}
        

    # row schema is for data in a row of a table
    # it is a list of data items with type and name
    # the type is a DataType enum
    def validate(self, data: Any) -> bool:
        if not isinstance(data, list):
            raise ValueError("Data must be a list")
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Item must be a dictionary")
            if "type" not in item or "name" not in item:    
                raise ValueError("Item must have type and name")
            
            # Use DataType enum for validation
            data_type = DataType.from_string(item["type"])
            if not data_type.validate_value(item.get("data")):
                raise ValueError(f"Item data must be a valid {data_type.value}")
        return True

class TupleSchema(Schema):
    def __init__(self, schema: Dict[str, Any]):
        super().__init__(schema["name"], schema["description"], schema["schema"])
        self.schema = schema

    def validate(self, data: Any) -> bool:
        if not isinstance(data, tuple):
            raise ValueError("Data must be a tuple")
        
        # Validate each item in the tuple against the schema
        if "items" in self.schema:
            if len(data) != len(self.schema["items"]):
                raise ValueError(f"Tuple length mismatch: expected {len(self.schema['items'])}, got {len(data)}")
            
            for i, (item, item_schema) in enumerate(zip(data, self.schema["items"])):
                data_type = DataType.from_string(item_schema.get("type", "string"))
                if not data_type.validate_value(item):
                    raise ValueError(f"Item at position {i} must be a valid {data_type.value}")
        
        return True

class JsonSchema(Schema):
    def __init__(self, schema: Dict[str, Any]):
        super().__init__(schema["name"], schema["description"], schema["schema"])
        self.schema = schema

    def validate(self, data: Any) -> bool:
        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(f"JSON validation error: {e}")
        except Exception as e:
            raise ValueError(f"Error validating JSON: {e}")
