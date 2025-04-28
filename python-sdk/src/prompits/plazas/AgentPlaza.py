"""
Plaza module for agent communication.

A Plaza is a communication channel between agents. It allows agents to advertise
their practices and request services from other agents. It connect to a pool
and store the advertisements in a table in the pool.
"""

import threading
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import traceback
import json

from ..Schema import DataType, TableSchema
from ..Plaza import Plaza
from ..Pool import Pool
from ..pools.DatabasePool import DatabasePool
from ..Practice import Practice
from ..AgentAddress import AgentAddress
from ..LogEvent import LogEvent

class AgentPlaza(Plaza):
    """
    AgentPlaza for agent communication.
    
    A AgentPlaza maintains a list of advertisements from agents and provides
    methods for agents to advertise, search for advertisements, and
    request services from other agents.
    """
    
    def __init__(self, name: str = "AgentPlaza", description: str = None, pool=None, table_name: str="agents", agent=None):
        """
        Initialize an AgentPlaza.
        
        Args:
            name: Name of the plaza
            description: Description of the plaza
            pool: Database pool
            table_name: Name of the table to store agent data
            agent: Reference to the owning agent
        """
        # Create the schema for the agents table
        from ..Schema import DataType
        
        # Define the schema for the agents table
        # contains the following columns:
        # agent_id: string
        # agent_name: string
        # status: string
        # create_time: datetime
        # update_time: datetime
        # stop_time: datetime
        # description: string
        # agent_info: json
        schema_dict = {
            "name": table_name,
            "description": "AgentPlaza",
            "primary_key": ["agent_id"],
            "rowSchema": {
                "agent_name": DataType.STRING,
                "status": DataType.STRING,
                "create_time": DataType.DATETIME,
                "update_time": DataType.DATETIME,
                "stop_time": DataType.DATETIME,
                "description": DataType.STRING,
                "agent_info": DataType.JSON,
                "agent_id": DataType.STRING
            }
        }
        table_schema = TableSchema(schema_dict)
        self.table_name = table_name
        self.agent_table_schema = table_schema
        
        # Initialize the plaza with the pool
        super().__init__(name, description or f"AgentPlaza {name}", table_schema, pool)
        
        # Set up database connection
        self.cleanup_thread = None
        self.running = False
        self.pools = [pool] if pool else []
        
        # Don't Create the table 
        # if self.pool and self.pool.TableExists(self.table_name):
        #     self.pool.DropTable(self.table_name)
            
        # Create the table if needed
        if not self.pool:
            raise ValueError("Pool is not set")
        if self.pool.UsePractice("TableExists", self.table_name):
            self.log(f"Table {self.table_name} already exists", 'DEBUG')
        else:
            self.log(f"Creating table {self.table_name}, schema: {table_schema}", 'DEBUG')
            result = self.pool.UsePractice("CreateTable", self.table_name, table_schema)
            if result:
                self.log(f"Table {self.table_name} created", 'DEBUG')
            else:
                self.log(f"Table {self.table_name} creation failed", 'ERROR')
                raise Exception(f"Agent Table {self.table_name} creation failed")
        
        # Add practices
        self.AddPractice(Practice("SearchAdvertisements", self.search_advertisements))
        self.AddPractice(Practice("Advertise", self.Advertise))
        self.AddPractice(Practice("AddPool", self.add_pool))
        self.AddPractice(Practice("ListActiveAgents", self.list_active_agents))
        
        # Store reference to the owning agent
        self.agent = agent

        # initialize the Library
        # library is a data storage with search and retrieval practices
        # search can be a vector search, graph search, or full text search
        
        
        self.log(f"AgentPlaza {name} initialized", 'INFO')
    
    def ToJson(self):
        """
        Convert the plaza to a JSON object.
        
        Returns:
            dict: JSON representation of the plaza
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": "AgentPlaza",
            "table_name": self.table_name
        }
    
    def list_active_agents(self, name_only=False, active_minutes=1):
        """
        List all active agents.
        
        Args:
            name_only: Whether to return only agent names
            
        Returns:
            list: List of active agents
        """
        try:
            self.log(f"Listing active agents on {self.table_name}", 'DEBUG')
            active_minutes_ago = datetime.now() - timedelta(minutes=active_minutes)
            agents = self.pool.UsePractice("GetTableData", self.table_name, {
                "$and": [
                    {"update_time": {"$gt": active_minutes_ago}},
                    {"stop_time": None}
                ]
            }, table_schema=self.agent_table_schema)
            
            active_agents = []
            for agent in agents:
                if agent.get("stop_time") is None:
                    if name_only:
                        active_agents.append(agent.get("agent_name"))
                    else:
                        active_agents.append({
                            "agent_id": agent.get("agent_id"),
                            "agent_name": agent.get("agent_name"),
                            "create_time": agent.get("create_time"),
                            "update_time": agent.get("update_time"),
                            "description": agent.get("description"),
                            "agent_info": agent.get("agent_info", {})
                        })
            
            self.log(f"Found {len(active_agents)} active agents", 'DEBUG')
            return active_agents
        except Exception as e:
            self.log(f"Error listing active agents: {str(e)}", 'ERROR')
            return []
    
    @classmethod
    def FromJson(cls, json_data: Dict[str, Any], pool=None, agent=None):
        """
        Initialize the plaza from a JSON object.
        
        Args:
            json_data: JSON object containing plaza configuration
            pool: Database pool
            agent: Reference to the owning agent
            
        Returns:
            Plaza: The initialized plaza
        """
        name = json_data.get("name", "AgentPlaza")
        description = json_data.get("description", None)
        table_name = json_data.get("table_name", "agents")
        
        return cls(name, description, pool, table_name, agent)
    
    def Advertise(self, agent_id: str, agent_name: str, description: str = None, agent_info: Dict = None):
        """
        Advertise an agent on the plaza.
        
        Args:
            agent_id: ID of the agent
            agent_name: Name of the agent
            description: Description of the agent
            agent_info: Information about the agent
            
        Returns:
            bool: True if advertised successfully, False otherwise
        """
        try:
            # Check if the agent is already advertised
            existing_agent = self.pool.UsePractice("GetTableData", self.table_name, {"agent_id": agent_id})
            
            # Get the current time
            now = datetime.now()
            
            # Ensure agent_info practices are dictionaries
            if agent_info and "pits" in agent_info:
                for pit_name, pit_info in agent_info["pits"].items():
                    if isinstance(pit_info, dict) and "practices" in pit_info:
                        if isinstance(pit_info["practices"], list):
                            practice_dict = {}
                            for practice in pit_info["practices"]:
                                if isinstance(practice, dict) and "name" in practice:
                                    practice_dict[practice["name"]] = practice
                            pit_info["practices"] = practice_dict
            
            # Create the agent data
            agent_data = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "description": description,
                "agent_info": agent_info,
                "update_time": now,
                "stop_time": None
            }
            
            # Update or insert the agent
            if existing_agent:
                self.pool.UsePractice("Update", self.table_name, agent_data, {"agent_id": agent_id}, self.agent_table_schema)
            else:
                agent_data["create_time"] = now
                self.pool.UsePractice("Insert", self.table_name, agent_data, self.agent_table_schema)
            
            self.log(f"Advertised agent {agent_id} on plaza {self.name}", 'DEBUG')
            return True
        except Exception as e:
            print(f"Error advertising agent: {str(e)}\n{traceback.format_exc()}")
            self.log(f"Error advertising agent: {str(e)}\n{traceback.format_exc()}", 'ERROR')
            return False
    
    def update_agent_stop_time(self, agent_id: str):
        """
        Update the stop time of an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            bool: True if the update was successful, False otherwise
        """
        try:
            now = datetime.now()
            data = {
                "status": "inactive",
                "stop_time": now
            }
            self.pool.UsePractice("Update", self.table_name, data, {"agent_id": agent_id}, self.agent_table_schema)
            self.log(f"Updated stop time for agent {agent_id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error updating agent stop time: {str(e)}\n{traceback.format_exc()}", 'ERROR')
            return False
    
    def start(self):
        """
        Start the plaza.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.log("Plaza is already running", 'WARNING')
            return False
        
        self.running = True
        self.log("Starting plaza", 'INFO')
        
        # Start the cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
        
        return True
    
    def stop(self):
        """
        Stop the plaza.
        """
        self.running = False
        
        # Wait for the cleanup thread to finish
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1)
            self.cleanup_thread = None
    
    def remove_advertisement(self, agent_id: str):
        """
        Remove an advertisement from the plaza.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            bool: True if the removal was successful, False otherwise
        """
        try:
            self.pool.UsePractice("Delete", self.table_name, {"agent_id": agent_id})
            self.log(f"Removed advertisement for agent {agent_id}", 'DEBUG')
            return True
        except Exception as e:
            self.log(f"Error removing advertisement: {str(e)}", 'ERROR')
            return False
    
    def search_advertisements(self, where: Dict = None):
        """
        Search for advertisements on the plaza.
        
        Args:
            where: Search criteria
            
        Returns:
            List[Dict]: List of advertisements matching the criteria
        """
        try:
            results = self.pool.UsePractice("GetTableData", self.table_name, where or {})
            self.log(f"Found {len(results)} advertisements", 'DEBUG')
            return results
        except Exception as e:
            self.log(f"Error searching advertisements: {str(e)}", 'ERROR')
            return []
    def get_agent_info(self, agent_id: str):
        """
        Get agent info from the plaza.
        """
        ad = self.get_advertisement(agent_id)
        if ad:
            self.log(f"Found agent info for {agent_id}", 'DEBUG')
            return ad.get("agent_info", {})
        self.log(f"No agent info found for {agent_id}", 'WARNING')
        return None
    
    def get_advertisement(self, agent_id: str):
        """
        Get an advertisement from the plaza.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dict: Advertisement for the agent
        """
        try:
            where = {"agent_id": agent_id}
            results = self.pool.UsePractice("GetTableData", self.table_name, where)
            if results:
                self.log(f"Found advertisement for agent {agent_id}", 'DEBUG')
                return results[0]
            self.log(f"No advertisement found for agent {agent_id}", 'WARNING')
            return None
        except Exception as e:
            self.log(f"Error getting advertisement: {str(e)}", 'ERROR')
            return None
    
    def _cleanup_loop(self):
        """
        Cleanup loop to remove inactive agents.
        """
        while self.running:
            try:
                time.sleep(60)
                self.log("Running cleanup loop", 'DEBUG')
                # TODO: Implement cleanup logic
            except Exception as e:
                self.log(f"Error in cleanup loop: {str(e)}", 'ERROR')
    
    def add_pool(self, pool):
        """
        Add a pool to the plaza.
        
        Args:
            pool: Pool to add
            
        Returns:
            bool: True if the pool was added successfully, False otherwise
        """
        try:
            if pool not in self.pools:
                self.pools.append(pool)
                self.log(f"Added pool {pool.name} to plaza {self.name}", 'DEBUG')
                
                if hasattr(pool, 'connect_to_plaza'):
                    pool.connect_to_plaza(self)
                    self.log(f"Connected pool {pool.name} to plaza {self.name}", 'DEBUG')
                
                return True
        except Exception as e:
            self.log(f"Error adding pool to plaza: {str(e)}", 'ERROR')
            return False

    # Explicitly inherit these methods to ensure log events are properly forwarded
    def subscribe_to_logs(self, callback):
        """Subscribe to log events and ensure they're propagated from Pit."""
        super().subscribe_to_logs(callback)
        #self.log(f"Subscribed to log events for AgentPlaza {self.name}", 'DEBUG')
        
    def unsubscribe_from_logs(self, callback):
        """Unsubscribe from log events."""
        super().unsubscribe_from_logs(callback)
        #self.log(f"Unsubscribed from log events for AgentPlaza {self.name}", 'DEBUG')
        
    def log(self, message, level='INFO'):
        """
        Log a message and ensure it's properly handled.
        
        This overrides the Pit.log method to ensure proper formatting
        and event propagation in the AgentPlaza context.
        """
        # Call the parent class's log method
        super().log(message, level)

# For backward compatibility
AgentBoard = AgentPlaza 