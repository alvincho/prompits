# Pouch is a service that store pathway and parameters
# It also store the results of posts and the state of the pathway
# It connects to multiple databases and can sync data between them
# It supports JSON and graph databases
# When traversing a graph, it can use a graph traversal algorithm
# PathRun is a running pathway
# PostStep is a running Post in a PathRun
# Pathfinder use Pouch to store and retrieve pathway and parameters
# Pathfinder use Pouch to store the state of a pathway run  
# Pouch is passively updated by Pathfinder
import datetime
import uuid
from enum import Enum
from prompits import AgentAddress, Pathway, Pit
from prompits.Pathway import Pathway, Post
from prompits.Pool import Pool
from prompits.Schema import DataType

class StepState(Enum):
    Pending = 0
    Running = 1
    Completed = 2
    Failed = 3

class StepVariables:
    def __init__(self, inputs: dict, parameters: dict):
        self.inputs = inputs
        self.parameters = parameters
        self.outputs = None


class PostStep:
    # PostStep is a running Post in a PathRun
    # It is created by an agent, and can be taken over by another agent

    def __init__(self, pathrunid: str, post: Post, state: StepState,
                 start_time: datetime, end_time: datetime=None,
                 variables: StepVariables=None,
                 previous_poststep: int=None, poststep_id: int=0):
        self.pathrunid = pathrunid
        self.post = post
        self.state = state
        self.start_time = start_time
        self.end_time = end_time
        self.variables = variables
        self.previous_poststep = previous_poststep
        self.next_poststep = None
        self.poststep_id = poststep_id

class PathRun:
    # PathRun is a running pathway
    # It is created by an agent, and can be taken over by another agent
    
    def __init__(self, pathrunid: str, pathway: Pathway, create_agent: AgentAddress, start_time: datetime=None):
        self.pathrunid = pathrunid
        self.pathway = pathway
        self.create_agent = create_agent
        self.start_time = start_time
        self.end_time = None
        self.poststeps = {} 
        self.running_poststeps = {}
        self.last_poststep_id = 0

    def AddPostStep(self, post: Post, state: StepState,
                    start_time: datetime, end_time: datetime=None,
                    variables: StepVariables=None,
                    previous_poststep: int=None, poststep_id: int=0):
        new_poststep_id = self.last_poststep_id + 1
        self.poststeps[new_poststep_id] = PostStep(self.pathrunid, post, state,
                                                  start_time, end_time, variables,
                                                  previous_poststep, poststep_id)
        self.last_poststep_id = new_poststep_id
        return new_poststep_id
        

class Pouch(Pit):
    """
    !!! This is a work in progress !!!
    
    Pouch is a service that store pathway and parameters
    It also store the results of posts and the state of the pathway
    It connects to multiple databases and can sync data between them
    It supports JSON and graph databases, built-in syncing between them
    When traversing a graph, it can use a graph traversal algorithm
    """
    def __init__(self, name: str, description: str, json_table_prefix: str="pouch_", graph_table_prefix: str="pouch_"):
        super().__init__(name, description)

        self.AddPractice("CreatePathRun", CreatePathRun)
        self.AddPractice("GetPathRun", GetPathRun)
        self.AddPractice("ListPathRuns", ListPathRuns)
        self.AddPractice("AddPostStep", AddPostStep)
        self.AddPractice("UpdatePostStep", UpdatePostStep)
        self.AddPractice("StopPathRun", StopPathRun)
        self.AddPractice("CreatePathway", CreatePathway)
        self.AddPractice("GetPathway", GetPathway)
        self.AddPractice("ListPathways", ListPathways)
        self.AddPractice("UpdatePathway", UpdatePathway)
        self.AddPractice("DeletePathway", DeletePathway)

        self.json_table_prefix = json_table_prefix
        self.graph_table_prefix = graph_table_prefix
        # Create a new table in the JSON pool
        self.json_pathrun_table_schema = {
            "name": self.json_table_prefix + "pathrun",
            "description": "PathRun",
            "schema": {
                "primary_key": ["pathrun_id"],
                "rowSchema": {
                    "pathrun_id": DataType.UUID,
                    "owner_agent_address": DataType.STRING,
                    "status": DataType.STRING,
                    "create_time": DataType.DATETIME,
                    "update_time": DataType.DATETIME,
                    "stop_time": { "type": DataType.DATETIME, "nullable": True },
                    "description": DataType.STRING,
                    "can_take_over": DataType.BOOLEAN,
                    "pathway": DataType.JSON
                }
            }
        }

        self.json_poststep_table_schema = {
            "name": self.json_table_prefix + "poststep",
            "description": "PostStep",
            "schema": {
                "primary_key": ["pathrun_id", "poststep_id"],
                "rowSchema": {
                    "pathrun_id": DataType.UUID,
                    "poststep_id": DataType.INTEGER,
                    "owner_agent_address": DataType.STRING,
                    "pathway_id": DataType.UUID,
                    "post_id": DataType.STRING,
                    "state": DataType.JSON,
                    "start_time": DataType.DATETIME,
                    "end_time": { "type": DataType.DATETIME, "nullable": True },
                    "variables": DataType.JSON,
                    "previous_poststep": { "type": DataType.INTEGER, "nullable": True },
                    "next_poststep": { "type": DataType.INTEGER, "nullable": True }
                }
            }
        }

        self.pathway_table_schema = {
            "name": self.json_table_prefix + "pathway",
            "description": "Pathway",
            "schema": {
                "primary_key": ["pathway_id","version"],
                "rowSchema": {
                    "pathway_id": DataType.UUID,
                    "version": DataType.REAL,
                    "name": DataType.STRING,
                    "description": DataType.STRING,
                    "owner_agent_address": DataType.STRING,
                    "create_time": DataType.DATETIME,
                    "update_time": DataType.DATETIME,
                    "status": DataType.STRING,
                    "pathway_json": DataType.JSON
                }
            }
        }

        # if tables already exist, don't create them
        if not self.json_pool.UsePractice("TableExists", self.json_pathrun_table_schema["name"]):
            self.json_pool.UsePractice("CreateTable", self.json_pathrun_table_schema)
        if not self.json_pool.UsePractice("TableExists", self.json_poststep_table_schema["name"]):
            self.json_pool.UsePractice("CreateTable", self.json_poststep_table_schema)
        if not self.json_pool.UsePractice("TableExists", self.pathway_table_schema["name"]):
            self.json_pool.UsePractice("CreateTable", self.pathway_table_schema)
            

    
    def set_json_pool(self, json_pool: Pool, table_prefix: str=None):
        self.json_pool = json_pool
        if table_prefix is not None:
            self.json_table_prefix = table_prefix

    def set_graph_pool(self, graph_pool: Pool, table_prefix: str=None):
        self.graph_pool = graph_pool
        if table_prefix is not None:
            self.graph_table_prefix = table_prefix

    # Create a new pathway run
    # PathRun is created by an agent, and can be taken over by another agent
    # returns the PathRunID
    def CreatePathRun(self, agent: AgentAddress, pathway: Pathway, can_take_over: bool = True, description: str = None):
        # insert into json_pathrun table
        pathrunid = str(uuid.uuid4())
        if description is None:
            description = pathway.description
        self.json_pool.UsePractice("Insert", self.json_pathrun_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "owner_agent_address": agent, 
                                    "pathway": pathway, "can_take_over": can_take_over,
                                    "create_time": datetime.datetime.now(),
                                    "update_time": datetime.datetime.now(),
                                    "status": "running",
                                    "description": description})
        return pathrunid

    # Get a pathway run
    # returns the PathRunID
    def GetPathRun(self, pathrunid: str):
        # select from json_pathrun table
        self.json_pool.UsePractice("Select", self.json_pathrun_table_schema["name"], 
                                   {"pathrun_id": pathrunid})

    # List all pathway runs
    # returns a list of PathRun objects
    def ListPathRuns(self):
        # select from json_pathrun table
        self.json_pool.UsePractice("Select", self.json_pathrun_table_schema["name"], {})
        return self.json_pool.UsePractice("Select", self.json_pathrun_table_schema["name"], {})

    # Update a pathway run
    # returns the PathRunID
    def UpdatePathRun(self, pathrunid: str, description: str = None):
        # update json_pathrun table
        self.json_pool.UsePractice("Update", self.json_pathrun_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "description": description})

    # Stop a pathway run
    # returns the PathRunID
    def StopPathRun(self, pathrunid: str):
        # update json_pathrun table
        self.json_pool.UsePractice("Update", self.json_pathrun_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "status": "stopped"})

    # Create a new pathway
    # returns the PathwayID
    def CreatePathway(self, pathway: Pathway):
        # insert into json_pathway table
        pathwayid = str(uuid.uuid4())
        self.json_pool.UsePractice("Insert", self.json_pathway_table_schema["name"], 
                                   {"pathway_id": pathwayid, "pathway": pathway})
        return pathwayid

    # Get a pathway
    # returns the PathwayID
    def GetPathway(self, pathwayid: str):
        # select from json_pathway table
        self.json_pool.UsePractice("Select", self.json_pathway_table_schema["name"], 
                                   {"pathway_id": pathwayid})

    # List all pathways
    # returns a list of Pathway objects
    def ListPathways(self):
        # select from json_pathway table
        self.json_pool.UsePractice("Select", self.json_pathway_table_schema["name"], {})
        return self.json_pool.UsePractice("Select", self.json_pathway_table_schema["name"], {})

    # Update a pathway
    # returns the PathwayID
    def UpdatePathway(self, pathwayid: str, pathway: Pathway):
        # update json_pathway table
        self.json_pool.UsePractice("Update", self.json_pathway_table_schema["name"], 
                                   {"pathway_id": pathwayid, "pathway": pathway})

    # Delete a pathway
    # returns the PathwayID     
    def DeletePathway(self, pathwayid: str):
        # delete from json_pathway table
        self.json_pool.UsePractice("Delete", self.json_pathway_table_schema["name"], 
                                   {"pathway_id": pathwayid})

    # Add a post step to a pathway run
    # returns the PostStepID
    def AddPostStep(self, pathrunid: str, post: Post):
        # insert into json_poststep table
        poststepid = str(uuid.uuid4())
        self.json_pool.UsePractice("Insert", self.json_poststep_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "poststep_id": poststepid, 
                                    "post_id": post.post_id, "state": post.state,
                                    "start_time": datetime.datetime.now(),
                                    "end_time": None,
                                    "variables": post.variables,
                                    "previous_poststep": None,
                                    "next_poststep": None}) 
        return poststepid

    # Update a post step
    # returns the PostStepID
    def UpdatePostStep(self, pathrunid: str, poststepid: str, post: Post):
        # update json_poststep table
        self.json_pool.UsePractice("Update", self.json_poststep_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "poststep_id": poststepid, 
                                    "post_id": post.post_id, "state": post.state,
                                    "start_time": datetime.datetime.now(),
                                    "end_time": None,
                                    "variables": post.variables,
                                    "previous_poststep": None,
                                    "next_poststep": None})
        return poststepid

    # Delete a post step
    # returns the PostStepID    
    def DeletePostStep(self, pathrunid: str, poststepid: str):
        # delete from json_poststep table
        self.json_pool.UsePractice("Delete", self.json_poststep_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "poststep_id": poststepid})

    # List all post steps
    # returns a list of PostStep objects
    def ListPostSteps(self, pathrunid: str):
        # select from json_poststep table
        self.json_pool.UsePractice("Select", self.json_poststep_table_schema["name"], 
                                   {"pathrun_id": pathrunid})

    def GetPostStep(self, pathrunid: str, poststepid: str):
        # select from json_poststep table
        self.json_pool.UsePractice("Select", self.json_poststep_table_schema["name"], 
                                   {"pathrun_id": pathrunid, "poststep_id": poststepid})
