# SQLite is a pool of connections to a SQLite database.

import sqlite3
import json
from datetime import datetime
import os
import traceback
from typing import Dict, Any, List, Optional
import types
import uuid
from ..Pool import JsonDataItem
from ..Schema import TableSchema, DataType
from .DatabasePool import DatabasePool
from ..Practice import Practice


class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles datetime objects and other non-serializable types.
    
    This encoder extends the standard JSONEncoder to properly serialize:
    - datetime objects (converted to ISO format strings)
    - methods and functions (converted to string representations)
    - custom objects (converted to dictionaries of their public attributes)
    """
    
    def default(self, obj):
        """
        Convert Python objects to JSON-serializable types.
        
        Args:
            obj: The object to convert
            
        Returns:
            A JSON-serializable representation of the object
            
        Raises:
            TypeError: If the object cannot be serialized
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (types.MethodType, types.FunctionType)):
            return str(obj)  # Convert methods/functions to string representation
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return {key: value for key, value in obj.__dict__.items() 
                   if not key.startswith('_') and not callable(value)}
        try:
            # Try to convert to a basic type
            return str(obj)
        except:
            # Fall back to default behavior
            return super().default(obj)


class SQLitePool(DatabasePool):
    """
    Pool implementation for SQLite databases.
    
    This class provides methods to interact with SQLite databases, including
    connections, transactions, and CRUD operations. It implements the abstract
    methods defined in DatabasePool.
    """
    
    def __init__(self, name: str, description: str, db_path: str):
        """
        Initialize an SQLitePool.
        
        Args:
            name: Name of the pool (also used as the main table name)
            description: Description of the pool's purpose
            db_path: Path to the SQLite database file
        """
        super().__init__(name, description)
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.is_connected = False
        self.connect()

    def connect(self):
        """Connect to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.log(f"Connected to SQLite database: {self.db_path}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error connecting to database: {e}", 'ERROR')
            return False

    def disconnect(self):
        """Disconnect from the database."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None
        self.log("Disconnected from database", 'DEBUG')

    def _TableExists(self, table_name: str) -> bool:
        """Check if a table exists."""
        self.log(f"Checking if table {table_name} exists", 'DEBUG') 
        try:
            self.cursor.execute("""
                SELECT name FROM sqlite_master  
                WHERE type='table' AND name=?
            """, (table_name,))
            return bool(self.cursor.fetchone())
        except Exception as e:
            self.log(f"Error checking table existence: {e}", 'ERROR')
            return False

    def _CreateTable(self, table_name: str, schema: TableSchema):
        """Create a table with the given schema."""
        try:
            columns = []
            for column_name, column_type in schema.rowSchema.columns.items():
                sqlite_type = self._get_sqlite_type(column_type)
                columns.append(f"{column_name} {sqlite_type}")
            
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    {', '.join(columns)}
                )
            """
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            # check if the table exists
            if not self._TableExists(table_name):
                self.log(f"Table {table_name} does not exist", 'ERROR')
                return False
            self.log(f"Created table {table_name}", 'DEBUG')
            #print(f"**** DIRECT PRINT: Created table {table_name}")
            return True
        except Exception as e:
            self.log(f"Error creating table: {e}\n{traceback.format_exc()}", 'ERROR')
            #print(f"**** DIRECT PRINT: Error creating table: {e}\n{traceback.format_exc()}")
            return False

    def _Store(self, id: str, data: Dict[str, Any]):
        """Store data in the database."""
        try:
            columns = list(data.keys()) + ['id']
            values = list(data.values()) + [id]
            placeholders = ', '.join(['?' * len(columns)])
            columns_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT OR REPLACE INTO {self.name} ({columns_str})
                VALUES ({placeholders})
            """
            self.cursor.execute(insert_sql, values)
            self.conn.commit()
            self.log(f"Stored data with id {id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error storing data: {e}\n{traceback.format_exc()}", 'ERROR')
            return False

    def _Execute(self, query: str, params: List[Any]=None):
        """Execute a query."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            self.log(f"Error executing query: {e}", 'ERROR')
            return []
        
    def _Retrieve(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the database."""
        try:
            self.cursor.execute(f"SELECT * FROM {self.name} WHERE id = ?", (id,))
            row = self.cursor.fetchone()
            if row:
                columns = [desc[0] for desc in self.cursor.description]
                self.log(f"Retrieved data with id {id}", 'DEBUG')
                return dict(zip(columns, row))
            self.log(f"No data found with id {id}", 'WARNING')
            return None
        except Exception as e:
            self.log(f"Error retrieving data: {e}\n{traceback.format_exc()}", 'ERROR')
            return None

    def _Update(self, id: str, data: Dict[str, Any]):
        """Update data in the database."""
        try:
            set_values = ', '.join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [id]
            
            update_sql = f"""
                UPDATE {self.name}
                SET {set_values}
                WHERE id = ?
            """
            self.cursor.execute(update_sql, values)
            self.conn.commit()
            self.log(f"Updated data with id {id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error updating data: {e}\n{traceback.format_exc()}", 'ERROR')
            return False

    def _Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search data in the database."""
        try:
            conditions = []
            values = []
            for key, value in where.items():
                conditions.append(f"{key} = ?")
                values.append(value)
            
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            
            self.cursor.execute(f"SELECT * FROM {self.name} WHERE {where_clause}", values)
            rows = self.cursor.fetchall()
            
            results = []
            columns = [desc[0] for desc in self.cursor.description]
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            self.log(f"Found {len(results)} matching records", 'DEBUG')
            return results
        except Exception as e:
            self.log(f"Error searching data: {e}\n{traceback.format_exc()}", 'ERROR')
            return []

    def _Delete(self, id: str):
        """Delete data from the database."""
        try:
            self.cursor.execute(f"DELETE FROM {self.name} WHERE id = ?", (id,))
            self.conn.commit()
            self.log(f"Deleted data with id {id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error deleting data: {e}\n{traceback.format_exc()}", 'ERROR')
            return False

    def _get_sqlite_type(self, column_type: DataType) -> str:
        """Convert schema type to SQLite type."""
        type_map = {
            DataType.STRING: 'TEXT',
            DataType.INTEGER: 'INTEGER',
            DataType.FLOAT: 'REAL',
            DataType.BOOLEAN: 'INTEGER',  # SQLite doesn't have a boolean type
            DataType.DATETIME: 'TIMESTAMP',
            DataType.JSON: 'TEXT'  # Store JSON as text in SQLite
        }
        return type_map.get(column_type, 'TEXT')

    def ToJson(self) -> Dict:
        """Convert pool to JSON representation."""
        # Get base JSON data from parent which includes practices
        json_data = super().ToJson()
        
        # Ensure practices are explicitly included if missing
        if "practices" not in json_data and hasattr(self, "practices"):
            json_data["practices"] = {
                practice.name: practice.ToJson() for practice in self.practices.values()
            }
        
        # Update with SQLitePool specific fields
        json_data.update({
            "name": self.name,
            "type": "SQLitePool",
            "database": self.db_path
        })
        
        return json_data

    def _ensure_connection(self):
        """Ensure that the connection is established."""
        if not hasattr(self, 'conn') or self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
    
    def _Connect(self):
        """
        Connect to the SQLite database.
        
        Returns:
            bool: True if connected successfully
        """
        try:
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(os.path.abspath(self.db_path))
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                
            # Connect to database
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            self.is_connected = True
            return True
        except Exception as e:
            raise sqlite3.DatabaseError(f"Error connecting to SQLite database: {str(e)}")
    
    def _Disconnect(self):
        """
        Disconnect from the database.
        
        Returns:
            bool: True if disconnected successfully
        """
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                self.conn = None
                self.cursor = None
                self.is_connected = False
            return True
        except Exception as e:
            raise sqlite3.DatabaseError(f"Error disconnecting from SQLite database: {str(e)}")
    
    def _IsConnected(self) -> bool:
        """
        Check if the pool is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return hasattr(self, 'conn') and self.conn is not None
            
    def _MapTypeFromDataType(self, data_type):
        """
        Map a DataType to a SQLite data type.
        
        Args:
            data_type: DataType to map
            
        Returns:
            str: SQLite data type
        """
        type_map = {
            DataType.INTEGER: "INTEGER",
            DataType.REAL: "REAL",
            DataType.STRING: "TEXT",
            DataType.BOOLEAN: "INTEGER",  # SQLite doesn't have a boolean type
            DataType.DATETIME: "TEXT",    # Store datetimes as ISO format strings
            DataType.JSON: "TEXT",        # Store JSON as text
            DataType.UUID: "TEXT",        # Store UUIDs as text
            DataType.ARRAY: "TEXT"       # Store arrays as JSON text
        }
        
        sqlite_type = type_map.get(data_type)
        if sqlite_type is None:
            raise NotImplementedError(f"DataType {data_type} not supported")
        return sqlite_type
    
    def _MapTypeToDataType(self, data_type):
        """
        Map a SQLite data type to a DataType.
        
        Args:
            data_type: SQLite data type to map
            
        Returns:
            DataType: Mapped DataType
        """
        # Convert to uppercase and clean up any modifiers
        clean_type = data_type.upper().split('(')[0].strip()
        
        type_map = {
            "INTEGER": DataType.INTEGER,
            "INT": DataType.INTEGER,
            "BIGINT": DataType.INTEGER,
            "REAL": DataType.FLOAT,
            "FLOAT": DataType.FLOAT,
            "DOUBLE": DataType.FLOAT,
            "TEXT": DataType.STRING,
            "VARCHAR": DataType.STRING,
            "CHAR": DataType.STRING,
            "BLOB": DataType.BINARY,
            "BOOLEAN": DataType.BOOLEAN,
            "DATE": DataType.DATE,
            "DATETIME": DataType.DATETIME,
            "TIMESTAMP": DataType.DATETIME,
        }
        
        data_type = type_map.get(clean_type)
        if data_type is None:
            raise NotImplementedError(f"SQLite type {clean_type} not supported")
        return data_type
    
    def FromJson(self, json_data):
        """
        Initialize pool from a JSON object.
        
        Args:
            json_data: JSON data to initialize from
            
        Returns:
            Pool: The initialized pool
        """
        self.name = json_data.get("name", self.name)
        self.description = json_data.get("description", self.description)
        self.db_path = json_data.get("database_path", self.db_path)
        return self
    
    def _ConvertToDataType(self, data_type, value):
        """
        Convert a Python value to the format needed for the given DataType.
        
        Args:
            value: Value to convert
            data_type: Target DataType
            
        Returns:
            The converted value
        """
        #print(f"Converting value {value} to {data_type}")
        self.log(f"Converting value {value} to {data_type}", 'DEBUG')
        if value is None:
            return None
            
        if data_type == DataType.INTEGER:
            return int(value)
        elif data_type == DataType.FLOAT:
            return float(value)
        elif data_type == DataType.BOOLEAN:
            return 1 if value else 0  # SQLite doesn't have a boolean type
        elif data_type == DataType.DATE or data_type == DataType.DATETIME:
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        elif data_type == DataType.JSON:
            if isinstance(value, dict):
                return json.dumps(value,default=str)
            #print(f"*** value: {value}")
            return str(value)
        elif data_type == DataType.ARRAY:
            if isinstance(value, list):
                return json.dumps(value, cls=DateTimeEncoder)
            return str(value)
        elif data_type == DataType.UUID:
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(uuid.UUID(value))
        elif data_type == DataType.DATE:
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d')
            return str(value)
        elif data_type == DataType.TIME:
            if isinstance(value, datetime):
                return value.strftime('%H:%M:%S')
        elif data_type == DataType.STRING:
            return str(value)
        else:
            raise NotImplementedError(f"Conversion to DataType {data_type} not supported")
    
    def _ConvertFromDataType(self, data_type, value):
        """
        Convert a value from a given DataType to the appropriate SQLite type.
        
        Args:
            data_type: DataType of the value
            value: Value to convert
            
        Returns:
            The converted value
        """
        if value is None:
            return None
            
        if data_type == DataType.INTEGER:
            return int(value)
        elif data_type == DataType.REAL:
            return float(value)
        elif data_type == DataType.BOOLEAN:
            return bool(int(value))
        elif data_type == DataType.DATETIME:
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except:
                    return value
            return value
        elif data_type == DataType.JSON:
            if isinstance(value, str):
                return json.loads(value)
            return value
        elif data_type == DataType.ARRAY:
            if isinstance(value, str):
                return json.loads(value)
            return value
        elif data_type == DataType.UUID:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value
        elif data_type == DataType.STRING:
            return str(value)
        elif data_type == DataType.DATE:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d')
            return value
        elif data_type == DataType.TIME:
            if isinstance(value, str):
                return datetime.strptime(value, '%H:%M:%S')
            return value
        else:
            raise NotImplementedError(f"Conversion from DataType {data_type} not supported")
    
    def _GetTableData(self, table_name: str, id_or_where: str=None, table_schema: TableSchema=None) -> dict[str, Any]:
        """
        Get data from a table.
        
        Args:
            table_name: Name of the table
            key: Key to identify the data
            
        Returns:
            dict: Data from the table
        """
        try:
            self._ensure_connection()
            
            # Assume key is a primary key value unless it's a dict
            if id_or_where and isinstance(id_or_where, dict):
                where_sql, where_values = self._build_where_clause(id_or_where)
                select_sql = f"SELECT * FROM {table_name} WHERE {where_sql}"
                values = where_values
            elif id_or_where:
                select_sql = f"SELECT * FROM {table_name} WHERE id = ?"
                values = [id_or_where]
            else:
                select_sql = f"SELECT * FROM {table_name}"
                values = []
            #self.log(f"SQLitePool._GetTableData: {select_sql}, \nvalues:{values}", 'DEBUG')
            self.cursor.execute(select_sql, values)
            
            # Get column names
            column_names = [description[0] for description in self.cursor.description]
            
            # Fetch and convert row to dictionary
            # Fetch all rows
            rows = []
            while True:
                row = self.cursor.fetchone()
                if not row:
                    break
                rows.append(row)
            
            rows_dict = []
            for row in rows:
                row_dict = {column_names[i]: row[i] for i in range(len(column_names))}
                for key, value in row_dict.items():
                    if isinstance(value, str):
                        # convert value to the correct data type
                        if table_schema is not None:
                            row_dict[key] = self._ConvertFromDataType(table_schema.rowSchema.columns[key], value)
                        else:
                            try:
                                # Try to parse as JSON
                                if value.startswith('{') or value.startswith('['):
                                    row_dict[key] = json.loads(value)
                            except:
                                pass
                rows_dict.append(row_dict)

            # Parse JSON fields
            #print(f"SQLitePool._GetTableData: {rows_dict}")
            return rows_dict
        except Exception as e:
            raise sqlite3.DatabaseError(f"Error getting data from {table_name}: {str(e)}")
    
    def _build_where_clause(self, where):
        """
        Build a WHERE clause from a dictionary.
        
        Args:
            where: Where clause dictionary
            
        Returns:
            tuple: (where_sql, where_values)
        """
        if not where:
            return "1=1", []
        
        clauses = []
        values = []
        
        # Handle $or operator at the top level
        # both or and and are supported

        if "$or" in where:
            or_clauses = []
            for or_condition in where["$or"]:
                or_sql, or_values = self._build_where_clause(or_condition)
                or_clauses.append(f"({or_sql})")
                values.extend(or_values)
            return " OR ".join(or_clauses), values

        if "$and" in where:
            and_clauses = []
            for and_condition in where["$and"]:
                and_sql, and_values = self._build_where_clause(and_condition)
                and_clauses.append(f"({and_sql})")
                values.extend(and_values)
            return " AND ".join(and_clauses), values
        
        # Handle regular field conditions
        for field, condition in where.items():
            if field.startswith("$"):
                continue  # Skip special operators like $or already handled
                
            if condition is None:
                clauses.append(f"{field} IS NULL")
                
            elif isinstance(condition, dict):
                # Handle operators like $gt, $lt, etc.
                for op, value in condition.items():
                    if op == "$gt":
                        clauses.append(f"{field} > ?")
                        values.append(value)
                    elif op == "$lt":
                        clauses.append(f"{field} < ?")
                        values.append(value)
                    elif op == "$gte":
                        clauses.append(f"{field} >= ?")
                        values.append(value)
                    elif op == "$lte":
                        clauses.append(f"{field} <= ?")
                        values.append(value)
                    elif op == "$ne":
                        clauses.append(f"{field} != ?")
                        values.append(value)
                    elif op == "$in":
                        placeholders = ", ".join("?" for _ in value)
                        clauses.append(f"{field} IN ({placeholders})")
                        values.extend(value)
                    elif op == "$nin":
                        placeholders = ", ".join("?" for _ in value)
                        clauses.append(f"{field} NOT IN ({placeholders})")
                        values.extend(value)
                    elif op == "$like":
                        clauses.append(f"{field} LIKE ?")
                        values.append(value)
                    elif op == "$ilike":  # SQLite doesn't have ILIKE, use LIKE with COLLATE NOCASE
                        clauses.append(f"{field} LIKE ? COLLATE NOCASE")
                        values.append(value)
                    elif op == "$between":
                        clauses.append(f"{field} BETWEEN ? AND ?")
                        values.append(value[0])
                        values.append(value[1])
                    elif op == "$not":
                        # Handle nested not conditions
                        not_sql, not_values = self._build_not_condition(field, value)
                        clauses.append(not_sql)
                        values.extend(not_values)
                    elif op == "$is":
                        # Handle is condition
                        clauses.append(f"{field} IS ?")
                        values.append(value)
            else:
                clauses.append(f"{field} = ?")
                values.append(condition)
        
        return " AND ".join(clauses), values
    
    def _build_not_condition(self, field, condition):
        """
        Build a NOT condition clause.
        
        Args:
            field: Field name
            condition: Condition dict with operators
            
        Returns:
            tuple: (not_sql, not_values)
        """
        not_clauses = []
        not_values = []
        
        for op, value in condition.items():
            if op == "$like":
                not_clauses.append(f"{field} NOT LIKE ?")
                not_values.append(value)
            elif op == "$ilike":  # SQLite doesn't have ILIKE, use LIKE with COLLATE NOCASE
                not_clauses.append(f"{field} NOT LIKE ? COLLATE NOCASE")
                not_values.append(value)
            elif op == "$in":
                placeholders = ", ".join("?" for _ in value)
                not_clauses.append(f"{field} NOT IN ({placeholders})")
                not_values.extend(value)
            elif op == "$between":
                not_clauses.append(f"{field} NOT BETWEEN ? AND ?")
                not_values.append(value[0])
                not_values.append(value[1])
            elif op == "$eq":
                not_clauses.append(f"{field} != ?")
                not_values.append(value)
            elif op == "$gt":
                not_clauses.append(f"{field} <= ?")
                not_values.append(value)
            elif op == "$lt":
                not_clauses.append(f"{field} >= ?")
                not_values.append(value)
        
        return " AND ".join(not_clauses), not_values
            
    def _TableExists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return bool(self.cursor.fetchone())
        except Exception as e:
            self.log(f"Error checking table existence: {e}", 'ERROR')
            return False
        
    def _CreateTable(self, table_name: str, schema: TableSchema):
        """Create a table with the given schema."""
        try:
            create_table_sql = ""
            columns = []
            self.log(f"Creating table {table_name}, schema: {schema}", 'DEBUG')
            for column_name, column_type in schema.rowSchema.columns.items():
                self.log(f"Mapping column: {column_name}, type: {column_type}", 'DEBUG')
                sqlite_type = self._get_sqlite_type(column_type)
                self.log(f"sqlite_type: {sqlite_type}", 'DEBUG')
                columns.append(f"{column_name} {sqlite_type}")
                
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    {', '.join(columns)}
                )
            """
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            self.log(f"Created table {table_name}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error creating table {table_name}: sql: {create_table_sql}\n{e}\n{traceback.format_exc()}", 'ERROR')
            return False
        
    def _Store(self, id: str, data: Dict[str, Any]):
        """Store data in the database."""
        try:
            columns = list(data.keys()) + ['id']
            values = list(data.values()) + [id]
            placeholders = ', '.join(['?' * len(columns)])
            columns_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT OR REPLACE INTO {self.name} ({columns_str})
                VALUES ({placeholders})
            """
            self.cursor.execute(insert_sql, values)
            self.conn.commit()
            self.log(f"Stored data with id {id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error storing data: {e}", 'ERROR')
            return False
        
    def _Retrieve(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the database."""
        try:
            self.cursor.execute(f"SELECT * FROM {self.name} WHERE id = ?", (id,))
            row = self.cursor.fetchone()
            if row:
                columns = [desc[0] for desc in self.cursor.description]
                self.log(f"Retrieved data with id {id}", 'DEBUG')
                return dict(zip(columns, row))
            self.log(f"No data found with id {id}", 'WARNING')
            return None
        except Exception as e:
            self.log(f"Error retrieving data: {e}", 'ERROR')
            return None
        
    def _Update(self, table_name: str, data: Dict[str, Any], where_clause: str, table_schema: TableSchema):
        """Update data in the database."""
        try:
            # map each of the data to the correct data types using _ConvertToDataType
            for key, value in data.items():
                data[key] = self._ConvertToDataType(table_schema.rowSchema.columns[key], value)
            set_values = ', '.join([f"{k} = ?" for k in data.keys()])
            values = list(data.values())
            for key, value in where_clause.items():
                values.append(self._ConvertToDataType(table_schema.rowSchema.columns[key], value))
            
            # Build where clause string
            where_conditions = []
            for key in where_clause.keys():
                where_conditions.append(f"{key} = ?")
            where_clause_str = " AND ".join(where_conditions)
            update_sql = f"""
                UPDATE {table_name} SET {set_values} WHERE {where_clause_str}
            """
            #print(f"*** where_clause: {where_clause}")
            #print(f"*** update_sql: {update_sql}, \nvalues: {values}")
            #self.log(f"update_sql: {update_sql}", 'DEBUG')
            #self.log(f"values: {values}", 'DEBUG')
            self.cursor.execute(update_sql, values)
            self.conn.commit()
            #self.log(f"Updated data with {values}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error updating data: {e}\n{update_sql}\n{traceback.format_exc()}", 'ERROR')
            return False
        
    def _Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search data in the database."""
        try:
            where_sql, where_values = self._build_where_clause(where)
            select_sql = f"SELECT * FROM {self.name} WHERE {where_sql}"
            self.cursor.execute(select_sql, where_values)
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
            self.log(f"Found {len(results)} results", 'DEBUG')
            return results
        except Exception as e:
            self.log(f"Error searching data: {e}", 'ERROR')
            return []
        
    def _Delete(self, id: str):
        """Delete data from the database."""
        try:
            self.cursor.execute(f"DELETE FROM {self.name} WHERE id = ?", (id,))
            self.conn.commit()
            self.log(f"Deleted data with id {id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error deleting data: {e}", 'ERROR')
            return False
        
    def _GetTableData(self, table_name: str, id_or_where: str=None, table_schema: TableSchema=None) -> dict[str, Any]:
        """
        Get data from a table.
        
        Args:
            table_name: Name of the table
            id_or_where: ID or WHERE clause
            table_schema: Table schema

        Returns:
            dict: Data from the table
        """
        try:
            # Assume key is a primary key value unless it's a dict
            if id_or_where and isinstance(id_or_where, dict):
                where_sql, where_values = self._build_where_clause(id_or_where)
                select_sql = f"SELECT * FROM {table_name} WHERE {where_sql}"
                values = where_values
            elif id_or_where:
                select_sql = f"SELECT * FROM {table_name} WHERE id = ?"
                values = [id_or_where]
            else:
                select_sql = f"SELECT * FROM {table_name}"
                values = []
            
            # check if cursor is connected, if not, reconnect
            if not self.cursor:
                self.log("SQLitePool: Cursor is not connected, reconnecting", 'ERROR')
                self.connect()
            self.cursor.execute(select_sql, values)
            
            # Get column names
            column_names = [description[0] for description in self.cursor.description]
            
            # Fetch and convert row to dictionary
            rows = []
            while True:
                row = self.cursor.fetchone()
                
                if row is None:
                    break
                
                row_dict = {column_names[i]: row[i] for i in range(len(column_names))}
                for key, value in row_dict.items():
                    if isinstance(value, str):
                        # convert value to the correct data type
                        if table_schema is not None:
                            row_dict[key] = self._ConvertFromDataType(table_schema.rowSchema.columns[key], value)
                        else:
                            try:
                                # Try to parse as JSON
                                if value.startswith('{') or value.startswith('['):
                                    row_dict[key] = json.loads(value)
                            except:
                                pass
                rows.append(row_dict)
            
            return rows
        except Exception as e:
            self.log(f"Error getting table data: {e}\n{select_sql}\n{traceback.format_exc()}", 'ERROR')
            return []
        
    def _DropTable(self, table_name: str):
        """Drop a table."""
        try:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.commit()
            self.log(f"Dropped table {table_name}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error dropping table: {e}", 'ERROR')
            return False
        
    def _Commit(self):
        """Commit the current transaction."""
        try:
            self.conn.commit()
            self.log("Committed transaction", 'DEBUG')
        except Exception as e:
            self.log(f"Error committing transaction: {e}", 'ERROR')
            
    def _Rollback(self):
        """Rollback the current transaction."""
        try:
            self.conn.rollback()
            self.log("Rolled back transaction", 'DEBUG')
        except Exception as e:
            self.log(f"Error rolling back transaction: {e}", 'ERROR')

    def _GetLastInsertId(self):
        """Get the last inserted ID."""
        try:
            self.cursor.execute("SELECT last_insert_rowid()")
            return self.cursor.fetchone()[0]
        except Exception as e:
            self.log(f"Error getting last inserted ID: {e}", 'ERROR')
            return None
    
    def _Insert(self, table_name: str, data: Dict[str, Any], table_schema: TableSchema):
        """
        Insert data into a specified table.
        
        This method validates and inserts data into the specified table,
        converting values to appropriate SQLite types based on the table schema.
        
        Args:
            table_name: Name of the table to insert into
            data: Dictionary of column-value pairs to insert
            table_schema: Schema definition for the table
            
        Returns:
            bool: True if inserted successfully, False otherwise
        """
        # check if the table exists
        if not self._TableExists(table_name):
            self.log(f"Table {table_name} does not exist", 'ERROR')
            return False
        # insert the data
        try:    
            # map each of the data to the correct data types using _ConvertToDataType
            for key, value in data.items():
                data[key] = self._ConvertToDataType(table_schema.rowSchema.columns[key], value)
            self.cursor.execute(f"INSERT INTO {table_name} ({', '.join(data.keys())}) VALUES ({', '.join(['?' for _ in data])})", list(data.values()))
            self.conn.commit()
            self.log(f"Inserted data into table {table_name}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error inserting data into table {table_name}: {e}\n{traceback.format_exc()}", 'ERROR')
            return False
    def _Query(self, query: str, params: List[Any]=None):
        """Query the database."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            self.log(f"Error querying database: {e}", 'ERROR')
            return []
        
    def _Rollback(self):
        """Rollback the current transaction."""
        try:
            self.conn.rollback()
            self.log("Rolled back transaction", 'DEBUG')
        except Exception as e:
            self.log(f"Error rolling back transaction: {e}", 'ERROR')

    def _GetTableSchema(self, table_name: str) -> TableSchema:
        """Get the schema of a table."""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            return TableSchema(self.cursor.fetchall())
        except Exception as e:
            self.log(f"Error getting table schema: {e}", 'ERROR')
            return None
    def _ListTables(self) -> List[str]:
        """List all tables in the database."""
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            self.log(f"Error listing tables: {e}", 'ERROR')
            return []
    
    