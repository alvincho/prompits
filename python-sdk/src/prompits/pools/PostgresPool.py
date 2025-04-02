# PostgresPool is a DatabasePool that can store and retrieve information from a Postgres database.
# PostgresPool is a subclass of DatabasePool.
# Sample JSON:
# {
#     "name": "PostgresPool1",
#     "description": "PostgresPool1 description",
#     "connectionString": "postgres://user:password@host:port/database"
# }

# Import Schema classes directly from their modules to avoid circular imports
from ..Practice import Practice
from ..Schema import TableSchema, DataType, RowSchema
from .DatabasePool import DatabasePool
#from sqlalchemy import create_engine, MetaData
import psycopg2
from ..Pool import DataItem, JsonDataItem
import uuid
# Import AgentBoard type for type hints but use string for actual type annotation
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
if TYPE_CHECKING:
    from ..boards.AgentBoard import AgentBoard

# Add import for traceback if not already present
import traceback

# Create a reusable DateTimeEncoder class at the module level
import json
from datetime import datetime
import types
from ..LogEvent import LogEvent

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

class PostgresPool(DatabasePool):
    """
    Pool implementation for PostgreSQL databases.
    
    This class provides methods to interact with PostgreSQL databases, including
    connections, transactions, and CRUD operations. It implements the abstract
    methods defined in DatabasePool.
    """
    
    def __init__(self, name: str, host: str, port: int, user: str, password: str, database: str):
        """
        Initialize a PostgresPool.
        
        Args:
            name: Name of the pool (also used as the main table name)
            host: PostgreSQL server hostname or IP address
            port: PostgreSQL server port number
            user: Username for database authentication
            password: Password for database authentication
            database: Database name to connect to
        """
        super().__init__(name)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to the database."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor()
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

    def TableExists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table_name,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            self.log(f"Error checking table existence: {e}", 'ERROR')
            return False

    def CreateTable(self, table_name: str, schema: TableSchema):
        """Create a table with the given schema."""
        try:
            columns = []
            for column_name, column_type in schema.columns.items():
                postgres_type = self._get_postgres_type(column_type)
                columns.append(f"{column_name} {postgres_type}")
            
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id VARCHAR(255) PRIMARY KEY,
                    {', '.join(columns)}
                )
            """
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            return True
        except Exception as e:
            self.log(f"Error creating table: {e}", 'ERROR')
            return False

    def Store(self, id: str, data: Dict[str, Any]):
        """Store data in the database."""
        try:
            columns = list(data.keys()) + ['id']
            values = list(data.values()) + [id]
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            insert_sql = f"""
                INSERT INTO {self.name} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT (id) DO UPDATE
                SET {', '.join(f"{col} = EXCLUDED.{col}" for col in data.keys())}
            """
            self.cursor.execute(insert_sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            self.log(f"Error storing data: {e}", 'ERROR')
            return False

    def Retrieve(self, id: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from the database."""
        try:
            self.cursor.execute(f"SELECT * FROM {self.name} WHERE id = %s", (id,))
            row = self.cursor.fetchone()
            if row:
                columns = [desc[0] for desc in self.cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            self.log(f"Error retrieving data: {e}", 'ERROR')
            return None

    def Update(self, id: str, data: Dict[str, Any]):
        """Update data in the database."""
        try:
            set_values = ', '.join([f"{k} = %s" for k in data.keys()])
            values = list(data.values()) + [id]
            
            update_sql = f"""
                UPDATE {self.name}
                SET {set_values}
                WHERE id = %s
            """
            self.cursor.execute(update_sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            self.log(f"Error updating data: {e}", 'ERROR')
            return False

    def Search(self, where: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search data in the database."""
        try:
            conditions = []
            values = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                values.append(value)
            
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            
            self.cursor.execute(f"SELECT * FROM {self.name} WHERE {where_clause}", values)
            rows = self.cursor.fetchall()
            
            results = []
            columns = [desc[0] for desc in self.cursor.description]
            for row in rows:
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            self.log(f"Error searching data: {e}", 'ERROR')
            return []

    def Delete(self, id: str):
        """Delete data from the database."""
        try:
            self.cursor.execute(f"DELETE FROM {self.name} WHERE id = %s", (id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.log(f"Error deleting data: {e}", 'ERROR')
            return False

    def _get_postgres_type(self, column_type: str) -> str:
        """Convert schema type to PostgreSQL type."""
        type_map = {
            'string': 'VARCHAR(255)',
            'integer': 'INTEGER',
            'float': 'FLOAT',
            'boolean': 'BOOLEAN',
            'datetime': 'TIMESTAMP',
            'json': 'JSONB'
        }
        return type_map.get(column_type.lower(), 'VARCHAR(255)')

    def ToJson(self) -> Dict:
        """Convert pool to JSON representation."""
        return {
            "name": self.name,
            "type": "PostgresPool",
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "database": self.database
        }

    def _IsConnected(self):
        """
        Check if the database connection is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.conn is not None and self.cursor is not None

    def _GetTableSchema(self, table_name):
        """
        Get the schema information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            dict: Schema information for the table
        """
        sql=f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{self.default_schema}' AND table_name = '{table_name}'"
        return self._Query(sql)

    def _GetTableData(self, table_name, id_or_where=None, table_schema=None, max_rows=100):
        """
        Get data from a table with optional filtering.
        
        Args:
            table_name: Name of the table to query
            id_or_where: ID or dictionary of conditions for filtering
            table_schema: Optional schema information for type conversion
            max_rows: Maximum number of rows to return
            
        Returns:
            list: List of rows matching the criteria
        """
        sql=f"SELECT * FROM {self.default_schema}.{table_name}"
        if id_or_where:
            if isinstance(id_or_where, dict):
                sql+=f" WHERE {self._convert_to_sql_clause(id_or_where)}"
            else:
                sql+=f" WHERE {id_or_where}"
        sql+=f" LIMIT {max_rows}"
        return self._Query(sql)

    def _Connect(self):
        """
        Establish a connection to the PostgreSQL database.
        
        This internal method handles the actual connection setup,
        including error handling and connection state management.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor()
            self.log(f"Connected to PostgreSQL database {self.database} at {self.host}:{self.port}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error connecting to PostgreSQL: {str(e)}", 'ERROR')
            traceback.print_exc()
            return False

    def _Disconnect(self):
        """
        Disconnect from the database.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            
            self.cursor = None
            self.conn = None
            print(f"Disconnected from PostgreSQL database with ID {self.id}")
            return True
        except Exception as e:
            print(f"Error disconnecting from PostgreSQL database: {str(e)}")
            traceback.print_exc()
            return False

    def ToJson(self):
        """
        Convert the pool to a JSON object.
        
        Returns:
            dict: JSON representation of the pool
        """
        json_data = super().ToJson()
        json_data.update({
            "connectionString": self.connectionString,
            "default_schema": self.default_schema
        })
        return json_data

    def MapTypeFromDataType(self, data_type: DataType) -> str:
        """
        Map a DataType to a PostgreSQL data type.
        
        Args:
            data_type: DataType to map
            
        Returns:
            str: PostgreSQL data type
        """
        return self._MapTypeFromDataType(data_type)

    def _MapTypeFromDataType(self, data_type: DataType) -> str:
        """
        Convert a DataType enum value to a PostgreSQL data type.
        
        Args:
            data_type: DataType enum value
            
        Returns:
            str: Corresponding PostgreSQL data type
        """
        # loop DataType enum and return the PostgreSQL type
        if data_type == DataType.STRING:
            return "VARCHAR(4096)"
        elif data_type == DataType.INTEGER:
            return "INTEGER"
        elif data_type == DataType.FLOAT:
            return "FLOAT"
        elif data_type == DataType.BOOLEAN:
            return "BOOLEAN"
        elif data_type == DataType.DATETIME:
            return "TIMESTAMP"
        elif data_type == DataType.JSON:
            return "JSONB"
        elif data_type == DataType.BINARY:
            return "BYTEA"
        else:
            return "VARCHAR(4096)"  # Default to string

    def MapTypeToDataType(self, data_type: str) -> DataType:
        """
        Map a PostgreSQL data type to a DataType.
        
        Args:
            data_type: PostgreSQL data type to map
            
        Returns:
            DataType: Mapped DataType
        """
        return self._MapTypeToDataType(data_type)

    def _MapTypeToDataType(self, data_type: str) -> DataType:
        """
        Convert a PostgreSQL data type to a DataType enum value.
        
        Args:
            data_type: PostgreSQL data type
            
        Returns:
            DataType: Corresponding DataType enum value
        """
        # Convert PostgreSQL type to DataType enum
        data_type = data_type.lower()
        if "varchar" in data_type or "text" in data_type or "char" in data_type:
            return DataType.STRING
        elif "int" in data_type:
            return DataType.INTEGER
        elif "float" in data_type or "real" in data_type or "double" in data_type or "numeric" in data_type or "decimal" in data_type:
            return DataType.FLOAT
        elif "bool" in data_type:
            return DataType.BOOLEAN
        elif "timestamp" in data_type or "date" in data_type:
            return DataType.DATETIME
        elif "json" in data_type:
            return DataType.JSON
        elif "bytea" in data_type or "blob" in data_type or "binary" in data_type:
            return DataType.BINARY
        else:
            return DataType.STRING  # Default to string

    # convert a JSON object to a pool
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
        self.connectionString = json_data.get("connectionString", self.connectionString)
        self.default_schema = json_data.get("default_schema", self.default_schema)
        return self

    def _ListTables(self):
        """
        List all tables in the database.
        
        Returns:
            list: List of table names
        """
        try:
            if not self.conn or not self.cursor:
                self._Connect()
            
            # Query to get all tables in the schema
            query = f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{self.default_schema}'
            """
            
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            # Extract table names from results
            tables = [row[0] for row in results]
            return tables
        except Exception as e:
            print(f"Error listing tables: {str(e)}")
            traceback.print_exc()
            return []

    def ListSchemas(self):
        """
        List all schemas in the database.
        
        Returns:
            list: List of schema names
        """
        return self._ListSchemas()

    def _ListSchemas(self):
        """
        List all schemas in the database.
        
        Returns:
            list: List of schema names
        """
        try:
            self.cursor.execute("SELECT schema_name FROM information_schema.schemata")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            self.log(f"Error listing schemas: {str(e)}", 'ERROR')
            return []

    def _ensure_connection(self):
        """
        Ensure the database connection is active and has the correct ID.
        If the connection is closed or has a different ID, reconnect.
        
        Returns:
            bool: True if connection is active, False otherwise
        """
        try:
            # Check if connection is None or closed
            if self.conn is None or self.cursor is None:
                return self._Connect()
            
            # Check if connection is still active
            try:
                # Execute a simple query to check connection
                self.cursor.execute("SELECT 1")
                return True
            except psycopg2.OperationalError:
                # Connection is closed, reconnect
                print(f"Connection lost for PostgreSQL database with ID {self.id}, reconnecting...")
                self._Disconnect()
                return self._Connect()
                
        except Exception as e:
            print(f"Error ensuring connection for PostgreSQL database with ID {self.id}: {str(e)}")
            traceback.print_exc()
            return False
    
    def _Query(self, query, params=None):
        """
        Execute a query and return the results.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            list: Query results
        """
        # Ensure connection is active
        if not self._ensure_connection():
            raise Exception(f"Could not connect to PostgreSQL database with ID {self.id}")
        
        try:
            # Execute the query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # Get the results
            try:
                results = self.cursor.fetchall()
                
                # Get column names
                column_names = [desc[0] for desc in self.cursor.description]
                
                # Convert results to list of dictionaries
                results_dicts = []
                for row in results:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[column_names[i]] = value
                    results_dicts.append(row_dict)
                
                return results_dicts
            except psycopg2.ProgrammingError:
                # No results to fetch
                return []
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            traceback.print_exc()
            return None

    def _CreateSchemaIfNotExists(self):
        """Create the default schema if it doesn't exist"""
        try:
            # Check if the schema exists
            self.cursor.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{self.default_schema}'")
            result = self.cursor.fetchone()
            
            # If the schema doesn't exist, create it
            if not result:
                self.cursor.execute(f"CREATE SCHEMA {self.default_schema}")
                self.conn.commit()
                print(f"Created schema {self.default_schema}")
            
            return True
        except Exception as e:
            print(f"Error creating schema: {str(e)}")
            self.conn.rollback()
            return False

    def _CreateTable(self, table_name, columns):
        """Create a new table in the database"""
        if not self.conn:
            self._Connect()
        
        # Create the schema if it doesn't exist
        self._CreateSchemaIfNotExists()
        
        # Handle TableSchema objects
        if isinstance(columns, TableSchema):
            # Extract column definitions from the TableSchema
            schema_dict = columns.schema
            if "rowSchema" in schema_dict:
                row_schema = schema_dict["rowSchema"]
                column_defs = []
                # if col_type is a dict, it may be a nullable column
                # if col_type is a DataType, it is a non-nullable column
                for col_name, col_type in row_schema.items():
                    # check col_type is a dict
                    if isinstance(col_type, dict):
                        # if col_type is a dict, it may be a nullable column
                        # if col_type is a DataType, it is a non-nullable column
                        pg_type = self.MapTypeFromDataType(col_type.get("type", DataType.STRING))
                        if col_type.get("nullable", False):
                            pg_type += " NULL"
                    else:
                        pg_type = self.MapTypeFromDataType(col_type)
                    column_defs.append(f"{col_name} {pg_type}")
                
                # Add primary key if specified
                if "primary_key" in schema_dict:
                    primary_keys = schema_dict["primary_key"]
                    if primary_keys:
                        primary_key_str = ", ".join(primary_keys)
                        column_defs.append(f"PRIMARY KEY ({primary_key_str})")
                
                columns_str = ", ".join(column_defs)
                query = f"CREATE TABLE IF NOT EXISTS {self.default_schema}.{table_name} ({columns_str})"
                
                try:
                    self.cursor.execute(query)
                    self.conn.commit()
                    return True
                except Exception as e:
                    print(f"Error creating table {table_name}: {str(e)}")
                    self.conn.rollback()
                    return False
            else:
                raise ValueError(f"Invalid TableSchema format: {schema_dict}")
        else:
            # Handle dictionary or list of columns
            column_defs = []
            for col in columns:
                if isinstance(col, dict):
                    name = col.get("name")
                    data_type = col.get("type", "TEXT")
                    constraints = col.get("constraints", "")
                    column_defs.append(f"{name} {data_type} {constraints}")
                else:
                    column_defs.append(col)
            
            columns_str = ", ".join(column_defs)
            query = f"CREATE TABLE IF NOT EXISTS {self.default_schema}.{table_name} ({columns_str})"
            
            try:
                self.cursor.execute(query)
                self.conn.commit()
                return True
            except Exception as e:
                print(f"Error creating table {table_name}: {str(e)}")
                self.conn.rollback()
                return False

    def _DropTable(self, table_name):
        """Drop a table from the database"""
        if not self.conn:
            self._Connect()
        
        query = f"DROP TABLE IF EXISTS {self.default_schema}.{table_name}"
        
        try:
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def _ListDataTypes(self):
        """
        List all data types available in PostgreSQL.
        
        Returns:
            list: List of data type names
        """
        return ["VARCHAR", "INTEGER", "FLOAT", "BOOLEAN", "TIMESTAMP", "JSONB", "BYTEA"]
    
    def _Execute(self, query, params=None):
        """
        Execute a query without returning results.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            bool: True if executed successfully, False otherwise
        """
        # Ensure connection is active
        if not self._ensure_connection():
            raise Exception(f"Could not connect to PostgreSQL database with ID {self.id}")
        
        try:
            # Execute the query
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return True
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            traceback.print_exc()
            return False

    def _Commit(self):
        """
        Commit the current transaction.
        
        Returns:
            bool: True if committed successfully, False otherwise
        """
        # Ensure connection is active
        if not self._ensure_connection():
            raise Exception(f"Could not connect to PostgreSQL database with ID {self.id}")
        
        try:
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error committing transaction: {str(e)}")
            traceback.print_exc()
            return False
    
    def _Rollback(self):
        """
        Rollback the current transaction.
        
        Returns:
            bool: True if rolled back successfully, False otherwise
        """
        # Ensure connection is active
        if not self._ensure_connection():
            raise Exception(f"Could not connect to PostgreSQL database with ID {self.id}")
        
        try:
            self.conn.rollback()
            return True
        except Exception as e:
            print(f"Error rolling back transaction: {str(e)}")
            traceback.print_exc()
            return False
    
    def _ConvertToDataType(self, data_type:DataType, data: Any) -> Any:
        """
        Convert a value to the specified DataType.
        
        Args:
            data_type: Target DataType
            data: Value to convert
            
        Returns:
            Any: Converted value
        """
        return self._convert_to_db_value(data, data_type)

    def _ConvertFromDataType(self, data_type:DataType, data: Any) -> Any:
        """
        Convert a database value to its Python representation.
        
        Args:
            data_type: Source DataType
            data: Value to convert
            
        Returns:
            Any: Converted value
        """
        return self._convert_from_db_value(data, data_type)

    def _TableExists(self, table_name):
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if the table exists, False otherwise
        """
        return self.TableExists(table_name)
    
    def _Insert(self, table_name, data):
        """
        Insert data into a table in the database.
        
        Args:
            table_name: Name of the table
            data: Data to insert (dict or JsonDataItem)
            
        Returns:
            bool: True if inserted successfully, False otherwise
        """
        try:
            if not self.conn:
                self._Connect()
            
            # Create the schema if it doesn't exist
            self._CreateSchemaIfNotExists()
            
            # Handle JsonDataItem
            if hasattr(data, 'data'):
                data_dict = data.data
            else:
                data_dict = data
            
            # Process JSON fields
            processed_data = {}
            placeholders = []
            values = []
            
            for key, value in data_dict.items():
                processed_data[key] = value
                placeholders.append("%s")
                
                # Convert dict/list to JSON string for database storage
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value, cls=DateTimeEncoder))
                else:
                    values.append(value)
            
            # Build the SQL query
            columns = ", ".join(processed_data.keys())
            placeholders_str = ", ".join(placeholders)
            
            sql = f"INSERT INTO {self.default_schema}.{table_name} ({columns}) VALUES ({placeholders_str})"
            
            # Execute the query
            self.cursor.execute(sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting data into {table_name}: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def _Update(self, table_name, data, where_clause, row_schema=None):
        """
        Update data in a table in the database.
        
        Args:
            table_name: Name of the table
            data: Data to update
            where_clause: Where clause for the update
            row_schema: Schema for the row
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            if not self.conn:
                self._Connect()
            
            # Create the schema if it doesn't exist
            self._CreateSchemaIfNotExists()
            
            # Process JSON fields
            set_clauses = []
            values = []
            
            for key, value in data.items():
                # Convert dict/list to JSON string for database storage
                if isinstance(value, (dict, list)):
                    set_clauses.append(f"{key} = %s")
                    values.append(json.dumps(value, cls=DateTimeEncoder))
                else:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            # Build the SQL query
            set_clause_str = ", ".join(set_clauses)
            
            # Add where clause values
            where_values = []
            for key, value in where_clause.items():
                # Convert dict/list to JSON string for database storage
                if isinstance(value, (dict, list)):
                    where_values.append(json.dumps(value, cls=DateTimeEncoder))
                else:
                    where_values.append(value)
            
            # Combine all values
            all_values = values + where_values
            
            # Build where clause string
            where_conditions = []
            for key in where_clause.keys():
                where_conditions.append(f"{key} = %s")
            where_clause_str = " AND ".join(where_conditions)
            
            sql = f"UPDATE {self.default_schema}.{table_name} SET {set_clause_str} WHERE {where_clause_str}"
            
            # Execute the query
            self.cursor.execute(sql, all_values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating data: {str(e)}")
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            return False

    def _Delete(self, table_name, data_key:dict):
        """
        Delete data from a table in the database.
        
        Args:
            table_name: Name of the table
            data_key: Key to identify the data to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if not self.conn:
                self._Connect()
            
            # Create the schema if it doesn't exist
            self._CreateSchemaIfNotExists()
            
            # Build where clause
            where_conditions = []
            values = []
            
            for key, value in data_key.items():
                # Convert dict/list to JSON string for database storage
                if isinstance(value, (dict, list)):
                    where_conditions.append(f"{key} = %s")
                    values.append(json.dumps(value, cls=DateTimeEncoder))
                else:
                    where_conditions.append(f"{key} = %s")
                    values.append(value)
            
            where_clause = " AND ".join(where_conditions)
            sql = f"DELETE FROM {self.default_schema}.{table_name} WHERE {where_clause}"
            
            # Execute the query
            self.cursor.execute(sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting data: {str(e)}")
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            raise e
    def _convert_to_sql_clause(self, where:dict):
        """
        Convert a dictionary to a SQL WHERE clause.
        
        Args:
            where: Dictionary to convert to a SQL WHERE clause
            
        Returns:
            str: SQL WHERE clause
        """
        if not where:
            return "1=1"  # Default to return all records if no where clause
            
        # Handle OR condition
        if "$or" in where:
            or_clauses = []
            for condition in where["$or"]:
                # Handle None values in OR lists
                if condition is None:
                    or_clauses.append("IS NULL")
                elif isinstance(condition, dict):
                    or_clauses.append(f"({self._convert_to_sql_clause(condition)})")
                else:
                    # Handle primitive values in OR lists
                    or_clauses.append(f"= {self._format_value(condition)}")
            
            # If we have a field name before the $or, prepend it to each clause
            field_name = None
            for key in where:
                if key != "$or" and not key.startswith("$"):
                    field_name = key
                    break
                    
            if field_name:
                formatted_clauses = []
                for clause in or_clauses:
                    if clause.startswith("("):
                        # This is already a complete condition
                        formatted_clauses.append(clause)
                    else:
                        # This is a partial condition that needs the field name
                        formatted_clauses.append(f"{field_name} {clause}")
                return " OR ".join(formatted_clauses)
            else:
                return " OR ".join(or_clauses)
            
        # Handle AND condition
        if "$and" in where:
            and_clauses = []
            for condition in where["$and"]:
                if condition is None:
                    and_clauses.append("IS NULL")
                elif isinstance(condition, dict):
                    and_clauses.append(f"({self._convert_to_sql_clause(condition)})")
                else:
                    and_clauses.append(f"= {self._format_value(condition)}")
            
            # If we have a field name before the $and, prepend it to each clause
            field_name = None
            for key in where:
                if key != "$and" and not key.startswith("$"):
                    field_name = key
                    break
                    
            if field_name:
                formatted_clauses = []
                for clause in and_clauses:
                    if clause.startswith("("):
                        # This is already a complete condition
                        formatted_clauses.append(clause)
                    else:
                        # This is a partial condition that needs the field name
                        formatted_clauses.append(f"{field_name} {clause}")
                return " AND ".join(formatted_clauses)
            else:
                return " AND ".join(and_clauses)
            
        # Handle regular conditions
        clauses = []
        for key, value in where.items():
            # Skip special operators
            if key.startswith("$"):
                continue
                
            # Handle NULL values
            if value is None:
                clauses.append(f"{key} IS NULL")
                continue
                
            # Handle dictionary operators
            if isinstance(value, dict):
                # Handle $or within a field
                if "$or" in value:
                    or_conditions = []
                    for item in value["$or"]:
                        if item is None:
                            or_conditions.append(f"{key} IS NULL")
                        else:
                            or_conditions.append(f"{key} = {self._format_value(item)}")
                    clauses.append(f"({' OR '.join(or_conditions)})")
                    continue
                
                # Greater than
                if "$gt" in value:
                    clauses.append(f"{key} > {self._format_value(value['$gt'])}")
                # Less than
                elif "$lt" in value:
                    clauses.append(f"{key} < {self._format_value(value['$lt'])}")
                # Greater than or equal
                elif "$gte" in value:
                    clauses.append(f"{key} >= {self._format_value(value['$gte'])}")
                # Less than or equal
                elif "$lte" in value:
                    clauses.append(f"{key} <= {self._format_value(value['$lte'])}")
                # Not equal
                elif "$ne" in value:
                    clauses.append(f"{key} != {self._format_value(value['$ne'])}")
                # In list
                elif "$in" in value:
                    values = ", ".join([self._format_value(v) for v in value["$in"]])
                    clauses.append(f"{key} IN ({values})")
                # Not in list
                elif "$nin" in value:
                    values = ", ".join([self._format_value(v) for v in value["$nin"]])
                    clauses.append(f"{key} NOT IN ({values})")
                # Like
                elif "$like" in value:
                    clauses.append(f"{key} LIKE {self._format_value(value['$like'])}")
                # Case-insensitive like
                elif "$ilike" in value:
                    clauses.append(f"{key} ILIKE {self._format_value(value['$ilike'])}")
                # Between
                elif "$between" in value:
                    if len(value["$between"]) == 2:
                        clauses.append(f"{key} BETWEEN {self._format_value(value['$between'][0])} AND {self._format_value(value['$between'][1])}")
                # Not operator
                elif "$not" in value:
                    # Handle nested operators within NOT
                    if isinstance(value["$not"], dict):
                        if "$like" in value["$not"]:
                            clauses.append(f"{key} NOT LIKE {self._format_value(value['$not']['$like'])}")
                        elif "$between" in value["$not"]:
                            if len(value["$not"]["$between"]) == 2:
                                clauses.append(f"{key} NOT BETWEEN {self._format_value(value['$not']['$between'][0])} AND {self._format_value(value['$not']['$between'][1])}")
                        elif "$in" in value["$not"]:
                            values = ", ".join([self._format_value(v) for v in value["$not"]["$in"]])
                            clauses.append(f"{key} NOT IN ({values})")
            else:
                # Simple equality
                clauses.append(f"{key} = {self._format_value(value)}")
                
        return " AND ".join(clauses) if clauses else "1=1"
        
    def _format_value(self, value):
        """Format a value for SQL query."""
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, str):
            # Escape single quotes
            return f"'{value.replace('\'', '\'\'')}'"
        elif isinstance(value, (list, tuple)):
            return f"({', '.join([self._format_value(v) for v in value])})"
        elif isinstance(value, dict):
            # Don't try to format dictionaries as SQL literals
            # This should be handled by convert_to_sql_clause
            raise ValueError(f"Cannot format dictionary as SQL value: {value}")
        elif hasattr(value, 'strftime'):  # Handle datetime objects
            # Format datetime as ISO format string
            return f"'{value.isoformat()}'"
        else:
            # For other types, convert to string and quote
            return f"'{str(value)}'"

    def _Search(self, table_name, where:dict):
        """
        Search for data in a table in the database.
        
        Args:
            table_name: Name of the table
            where: Where clause dictionary
                Example:
                where = {"name": "John", "age": 30}
                will be converted to: name = 'John' AND age = 30
                where = {"name": "John", "age": None}
                will be converted to: name = 'John' AND age IS NULL
                where = {"name": "John", "age": {"$gt": 30}}
                will be converted to: name = 'John' AND age > 30
                where = {"name": "John", "age": {"$lt": 30}}
                will be converted to: name = 'John' AND age < 30
                where = {"name": "John", "age": {"$gte": 30}}
                will be converted to: name = 'John' AND age >= 30
                where = {"name": "John", "age": {"$lte": 30}}
                will be converted to: name = 'John' AND age <= 30
                where = {"name": "John", "age": {"$ne": 30}}
                will be converted to: name = 'John' AND age != 30
                where = {"name": "John", "age": {"$in": [30, 40, 50]}}
                will be converted to: name = 'John' AND age IN (30, 40, 50)
                where = {"name": "John", "age": {"$nin": [30, 40, 50]}}
                will be converted to: name = 'John' AND age NOT IN (30, 40, 50)
                where = {"name": "John", "age": {"$like": "%30%"}}
                will be converted to: name = 'John' AND age LIKE '%30%'
                where = {"name": "John", "age": {"$ilike": "%30%"}}
                will be converted to: name = 'John' AND age ILIKE '%30%'
                where = {"name": "John", "age": {"$not": {"$like": "%30%"}}}
                will be converted to: name = 'John' AND age NOT LIKE '%30%'
                where = {"name": "John", "age": {"$between": [30, 50]}}
                will be converted to: name = 'John' AND age BETWEEN 30 AND 50
                where = {"name": "John", "age": {"$not": {"$between": [30, 50]}}}
                will be converted to: name = 'John' AND age NOT BETWEEN 30 AND 50
                where = {"$or": [{"name": "John"}, {"age": {"$gt": 30}}]}
                will be converted to: (name = 'John' OR age > 30)
                where = {"$or": [{"name": "John"}, {"age": {"$lt": 30}}]}
                will be converted to: (name = 'John' OR age < 30)
            
        Returns:
            list: List of data from the table
        """
        try:
            # Ensure connection is active
            self._ensure_connection()
            
            # Create the schema if it doesn't exist
            self._CreateSchemaIfNotExists()
            
            # Check if table exists
            if not self.TableExists(table_name):
                raise ValueError(f"Table {table_name} does not exist")
            
            # Convert the where clause to SQL
            where_clause = self._convert_to_sql_clause(where)
            
            # Build and execute the query
            sql = f"SELECT * FROM {self.default_schema}.{table_name} WHERE {where_clause}"
            #print(f"Executing SQL: {sql}")
            
            # For debugging
            # print(f"Executing SQL: {sql}")
            
            self.cursor.execute(sql)
            
            # Fetch all results
            rows = self.cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in self.cursor.description]
            
            # Convert rows to dictionaries
            results = []
            for row in rows:
                result = {}
                for i, column_name in enumerate(column_names):
                    result[column_name] = row[i]
                results.append(result)
                
            return results
            
        except Exception as e:
            print(f"Error searching data: {str(e)}")
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            raise e

    def _Get(self, table_name, id_or_where=None):
        """
        Get data from a table in the database.
        
        Args:
            table_name: Name of the table
            id_or_where: ID (string) or where clause (dict), if None returns all records
            
        Returns:
            dict or list: Data from the table
        """
        try:
            if not self.conn:
                self._Connect()
            
            # Create the schema if it doesn't exist
            self._CreateSchemaIfNotExists()
            
            # If id_or_where is None, return all records
            if id_or_where is None:
                sql = f"SELECT * FROM {self.default_schema}.{table_name}"
                self.cursor.execute(sql)
                results = self.cursor.fetchall()
                
                if results:
                    # Convert to list of dictionaries
                    columns = [desc[0] for desc in self.cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                return []
            
            # Handle string ID
            if isinstance(id_or_where, str):
                sql = f"SELECT * FROM {self.default_schema}.{table_name} WHERE agent_id = %s"
                self.cursor.execute(sql, (id_or_where,))
                result = self.cursor.fetchone()
                
                if result:
                    # Convert to dictionary
                    columns = [desc[0] for desc in self.cursor.description]
                    return dict(zip(columns, result))
                return None
            
            # Handle dictionary (where clause)
            elif isinstance(id_or_where, dict):
                # If empty dict, return all records
                if not id_or_where:
                    sql = f"SELECT * FROM {self.default_schema}.{table_name}"
                    self.cursor.execute(sql)
                    results = self.cursor.fetchall()
                    
                    if results:
                        # Convert to list of dictionaries
                        columns = [desc[0] for desc in self.cursor.description]
                        return [dict(zip(columns, row)) for row in results]
                    return []
                
                # Build where clause
                where_conditions = []
                values = []
                
                for key, value in id_or_where.items():
                    # Convert dict/list to JSON string for database storage
                    if isinstance(value, (dict, list)):
                        where_conditions.append(f"{key} = %s")
                        values.append(json.dumps(value, cls=DateTimeEncoder))
                    else:
                        where_conditions.append(f"{key} = %s")
                        values.append(value)
                
                where_clause = " AND ".join(where_conditions)
                sql = f"SELECT * FROM {self.default_schema}.{table_name} WHERE {where_clause}"
                print(sql, id_or_where)
                # Execute the query
                self.cursor.execute(sql, values)
                results = self.cursor.fetchall()
                
                if results:
                    # Convert to list of dictionaries
                    columns = [desc[0] for desc in self.cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                return []
            
            else:
                raise ValueError(f"Invalid id_or_where type: {type(id_or_where)}")
                
        except Exception as e:
            print(f"Error getting data from {table_name}: {str(e)}")
            traceback.print_exc()
            return [] if isinstance(id_or_where, dict) else None
    
    def _connect_to_board(self, board: Any):
        """
        Connect the pool to an AgentBoard.
        
        Args:
            board: AgentBoard to connect to
        """
        self.board = board
        self._advertise_practices()
    
    def _advertise_practices(self):
        """
        Advertise the pool's practices on the connected board using AgentBoard's Advertise practice.
        """
        if self.board and hasattr(self.board, "Advertise"):
            # Create advertisements for each practice
            self.board.Advertise({"agent_id": self.id, "practice": "Query", "description": "Execute a query on the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "CreateTable", "description": "Create a table in the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "DropTable", "description": "Drop a table from the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "TableExists", "description": "Check if a table exists in the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "Insert", "description": "Insert data into a table in the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "Update", "description": "Update data in a table in the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "Delete", "description": "Delete data from a table in the PostgreSQL database"})
            self.board.Advertise({"agent_id": self.id, "practice": "Get", "description": "Get data from a table in the PostgreSQL database"})
    
    