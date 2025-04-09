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
from prompits.Schema import DataType, TableSchema
from prompits.Pit import Pit, Practice

class RunState(Enum):
    PENDING = 0
    RUNNING = 1
    COMPLETED = 2
    STOPPED = 3
    FAILED = 4

class StepVariables:
    def __init__(self, inputs: dict, parameters: dict):
        self.inputs = inputs
        self.parameters = parameters
        self.outputs = None
    def ToJson(self):
        return {
            "inputs": self.inputs,
            "parameters": self.parameters,
            "outputs": self.outputs
        }
        


class PostStep:
    # PostStep is a running Post in a PathRun
    # It is created by an agent, and can be taken over by another agent

    def __init__(self, pathrunid: str, post: Post, state: RunState,
                 start_time: datetime, stop_time: datetime=None,
                 variables: dict={},
                 last_poststep: int=None, poststep_id: int=0,
                 status_msg: str=None):
        self.pathrunid = pathrunid
        self.post = post
        self.state = state
        self.start_time = start_time
        self.stop_time = stop_time
        self.variables = variables
        self.last_poststep = last_poststep
        self.next_poststep = None
        self.poststep_id = poststep_id
        self.status_msg = status_msg

class PathRun:
    # PathRun is a running pathway
    # It is created by an agent, and can be taken over by another agent
    
    def __init__(self, pathrun_id: str, pathway: Pathway, 
                 create_agent_id: str, create_time: datetime=None,
                 update_time: datetime=None,
                 state: RunState=RunState.PENDING,
                 description: str=None,
                 days_to_live: int=0,
                 status_msg: str="",
                 inputs: dict={}):
        self.pathrun_id = pathrun_id
        self.pathway = pathway
        self.create_agent_id = create_agent_id
        self.create_time = create_time
        self.update_time = update_time
        self.state = state
        self.description = description
        self.days_to_live = days_to_live
        self.inputs = inputs
        self.poststeps = {} 
        self.running_poststeps = {}
        self.last_poststep_id = 0
        self.status_msg = status_msg
        

class Pouch(Pit):
    """
    !!! This is a work in progress !!!
    
    Pouch is a service that store pathway and parameters
    It also store the results of posts and the state of the pathway
    It connects to multiple databases and can sync data between them
    It supports JSON and graph databases, built-in syncing between them
    When traversing a graph, it can use a graph traversal algorithm
    """
    # TODO: OpenTelemetry tracing
    
    def __init__(self, name: str, description: str, 
                 json_pool: Pool=None,
                 graph_pool: Pool=None,
                 json_table_prefix: str="pouch_", 
                 graph_table_prefix: str="pouch_"):
        super().__init__(name, description)

        self.AddPractice(Practice("CreatePathRun", self._CreatePathRun))
        self.AddPractice(Practice("GetPathRun", self._GetPathRun))
        self.AddPractice(Practice("ListPathRuns", self._ListPathRuns))
        self.AddPractice(Practice("AddPostStep", self._AddPostStep))
        self.AddPractice(Practice("ListPostSteps", self._ListPostSteps))
        self.AddPractice(Practice("GetPostStep", self._GetPostStep))
        self.AddPractice(Practice("UpdatePostStep", self._UpdatePostStep))
        self.AddPractice(Practice("StopPathRun", self._StopPathRun))
        self.AddPractice(Practice("CompletePathRun", self._CompletePathRun))
        self.AddPractice(Practice("UpdatePathRun", self._UpdatePathRun))
        self.AddPractice(Practice("CreatePathway", self._CreatePathway))
        self.AddPractice(Practice("GetPathway", self._GetPathway))
        self.AddPractice(Practice("ListPathways", self._ListPathways))
        self.AddPractice(Practice("UpdatePathway", self._UpdatePathway))
        self.AddPractice(Practice("DeletePathway", self._DeletePathway))

        self.json_table_prefix = json_table_prefix
        self.graph_table_prefix = graph_table_prefix
        # Create a new table in the JSON pool
        self.json_pathrun_table_schema = TableSchema({
            "name": self.json_table_prefix + "pathrun",
            "description": "PathRun",
                "primary_key": ["pathrun_id"],
                "rowSchema": {
                    "pathrun_id": DataType.UUID,
                    "owner_agent_id": DataType.STRING,
                    "state": DataType.STRING,
                    "create_time": DataType.DATETIME,
                    "update_time": DataType.DATETIME,
                    "stop_time": { "type": DataType.DATETIME, "nullable": True },
                    "description": DataType.STRING,
                    "can_take_over": DataType.BOOLEAN,
                    "pathway_id": DataType.UUID,
                    "pathway": DataType.JSON,
                    "inputs": DataType.JSON,
                    "status_msg": DataType.STRING,
                    "results": DataType.JSON,
                    "days_to_live": { "type": DataType.INTEGER, "nullable": True, "default": 0 }
                }
            })

        self.json_poststep_table_schema =   TableSchema({
            "name": self.json_table_prefix + "poststep",
            "description": "PostStep",
                "primary_key": ["pathrun_id", "poststep_id"],
                "rowSchema": {
                    "pathrun_id": DataType.UUID,
                    "poststep_id": DataType.INTEGER,
                    "owner_agent_id": DataType.STRING,
                    "pathway_id": DataType.UUID,
                    "post_id": DataType.STRING,
                    "status_msg": DataType.STRING,
                    "state": DataType.JSON,
                    "start_time": DataType.DATETIME,
                    "stop_time": { "type": DataType.DATETIME, "nullable": True },
                    "variables": DataType.JSON,
                    "last_poststep": { "type": DataType.INTEGER, "nullable": True },
                    "next_poststep": { "type": DataType.INTEGER, "nullable": True }
            }
        })  

        self.json_pathway_table_schema = TableSchema({
            "name": self.json_table_prefix + "pathway",
            "description": "Pathway",
                "primary_key": ["pathway_id","version"],
                "rowSchema": {
                    "pathway_id": DataType.UUID,
                    "version": {"type": DataType.REAL, "nullable": False, "default": 1},
                    "name": DataType.STRING,
                    "description": DataType.STRING,
                    "owner_agent_id": DataType.STRING,
                    "create_time": DataType.DATETIME,
                    "update_time": DataType.DATETIME,
                    "pathway_json": DataType.JSON,
                    "days_to_live": { "type": DataType.INTEGER, "nullable": True, "default": 0 }
            }
        })

        if isinstance(json_pool, Pool):
            self.set_json_pool(json_pool)
        if isinstance(graph_pool, Pool):
            self.set_graph_pool(graph_pool)
        # if tables already exist, don't create them

    
    def set_json_pool(self, json_pool: Pool, table_prefix: str=None):
        self.log(f"Setting json pool in pouch", 'DEBUG')
        print(f"Setting json pool in pouch: {json_pool}")
        self.json_pool = json_pool
        if table_prefix is not None:
            self.json_table_prefix = table_prefix
        if not self.json_pool.UsePractice("TableExists", self.json_pathrun_table_schema.name):
            self.log(f"Creating pathrun table in pouch", 'DEBUG')
            self.json_pool.UsePractice("CreateTable", self.json_pathrun_table_schema.name, self.json_pathrun_table_schema)
        if not self.json_pool.UsePractice("TableExists", self.json_poststep_table_schema.name):
            self.log(f"Creating poststep table in pouch", 'DEBUG')
            self.json_pool.UsePractice("CreateTable", self.json_poststep_table_schema.name,self.json_poststep_table_schema)
        if not self.json_pool.UsePractice("TableExists",  self.json_pathway_table_schema.name):
            self.log(f"Creating pathway table in pouch", 'DEBUG')
            print(f"Creating pathway table in pouch: {self.json_pathway_table_schema}")
            self.json_pool.UsePractice("CreateTable", self.json_pathway_table_schema.name,self.json_pathway_table_schema)
            

    def set_graph_pool(self, graph_pool: Pool, table_prefix: str=None):
        self.graph_pool = graph_pool
        if table_prefix is not None:
            self.graph_table_prefix = table_prefix

    # Create a new pathway run
    # PathRun is created by an agent, and can be taken over by another agent
    # returns the PathRunID
    def _CreatePathRun(self, agent_id: str, pathway: Pathway, can_take_over: bool = True, description: str = None, inputs: dict = {}, days_to_live: int = 0):
        # insert into json_pathrun table
        pathrunid = str(uuid.uuid4())
        self.log(f"Creating pathrun {pathrunid} in pouch", 'DEBUG')
        if description is None:
            description = pathway.description
        try:
            print(f"Creating pathrun {pathrunid} in pouch: {pathway.pathway_id}")
            self.json_pool.UsePractice("Insert", self.json_pathrun_table_schema.name, 
                                    {"pathrun_id": pathrunid, "owner_agent_id": agent_id, 
                                    "pathway_id": pathway.pathway_id,
                                    "pathway": pathway.ToJson(), "can_take_over": can_take_over,
                                    "create_time": datetime.datetime.now(),
                                    "update_time": datetime.datetime.now(),
                                    "state": RunState.PENDING.value,
                                    "status_msg": "PathRun created",
                                    "description": description,
                                    "days_to_live": days_to_live,
                                    "inputs": inputs},
                                    self.json_pathrun_table_schema)
            self.log(f"Created pathrun {pathrunid} in pouch", 'DEBUG')
            pathrun = PathRun(pathrunid, pathway, agent_id, datetime.datetime.now())
            return pathrun
        except Exception as e:
            self.log(f"Error creating pathrun: {e}", 'ERROR')
            return None

    # Get a pathway run
    # returns the PathRunID
    def _GetPathRun(self, pathrunid: str):
        # select from json_pathrun table
        try:
            self.json_pool.UsePractice("Select", self.json_pathrun_table_schema.name, 
                                    {"pathrun_id": pathrunid})
            return self.json_pool.UsePractice("Select", self.json_pathrun_table_schema.name, 
                                    {"pathrun_id": pathrunid})
        except Exception as e:
            self.log(f"Error getting pathrun: {e}", 'ERROR')
            return None

    # List all pathway runs
    # returns a list of PathRun objects
    def _ListPathRuns(self):
        # select from json_pathrun table
        self.json_pool.UsePractice("Select", self.json_pathrun_table_schema.name, {})
        return self.json_pool.UsePractice("Select", self.json_pathrun_table_schema.name, {})

    # Update a pathway run
    # returns the PathRunID
    def _UpdatePathRun(self, pathrunid: str, description: str = None, state: RunState = None, status_msg: str = None, inputs: dict = {}):
        # update json_pathrun table
        data = {}
        if description is not None:
            data["description"] = description
        if state is not None:
            data["state"] = state.value
        if status_msg is not None:
            data["status_msg"] = status_msg
        if inputs is not None:
            data["inputs"] = inputs
        self.json_pool.UsePractice("Update", self.json_pathrun_table_schema.name, 
                                   data,
                                   {"pathrun_id": pathrunid},
                                   self.json_pathrun_table_schema)

    # Stop a pathway run
    # returns the PathRunID
    def _StopPathRun(self, pathrunid: str, results: dict = None):
        # update json_pathrun table
        self.json_pool.UsePractice("Update", self.json_pathrun_table_schema.name, 
                                   {"stop_time": datetime.datetime.now(), "results": results, "state": RunState.STOPPED.value, "status_msg": "PathRun stopped"},
                                   {"pathrun_id": pathrunid},
                                   self.json_pathrun_table_schema)

    # Complete a pathway run
    # returns the PathRunID
    def _CompletePathRun(self, pathrunid: str, results: dict = None):
        # update json_pathrun table
        self.json_pool.UsePractice("Update", self.json_pathrun_table_schema.name, 
                                   {"stop_time": datetime.datetime.now(), "results": results, "state": RunState.COMPLETED.value, "status_msg": "PathRun completed"},
                                   {"pathrun_id": pathrunid},
                                   self.json_pathrun_table_schema)

    # Create a new pathway
    # returns the PathwayID
    def _CreatePathway(self, pathway: Pathway):
        # insert into json_pathway table
        try:
            pathwayid = pathway.pathway_id
            self.json_pool.UsePractice("Insert", self.json_pathway_table_schema.name, 
                                    {"pathway_id": pathwayid, 
                                     "version": 1,
                                     "name": pathway.name,
                                     "description": pathway.description,
                                     "owner_agent_id": pathway.owner_agent_id,
                                     "create_time": datetime.datetime.now(),
                                     "update_time": datetime.datetime.now(),
                                     "pathway_json": pathway.ToJson()},
                                    self.json_pathway_table_schema)
            self.log(f"Created pathway {pathwayid} in pouch", 'DEBUG')
            return pathwayid
        except Exception as e:
            self.log(f"Error creating pathway: {e}", 'ERROR')
            return None

    # Get a pathway
    # returns the PathwayID
    def _GetPathway(self, pathwayid: str):
        # select from json_pathway table
        try:
            self.json_pool.UsePractice("Select", self.json_pathway_table_schema.name, 
                                    {"pathway_id": pathwayid})
            return self.json_pool.UsePractice("Select", self.json_pathway_table_schema.name, 
                                    {"pathway_id": pathwayid})
        except Exception as e:
            self.log(f"Error getting pathway: {e}", 'ERROR')
            return None

    # List all pathways
    # returns a list of Pathway objects
    def _ListPathways(self):
        # select from json_pathway table
        self.json_pool.UsePractice("Select", self.json_pathway_table_schema.name, {})
        return self.json_pool.UsePractice("Select", self.json_pathway_table_schema.name, {})

    # Update a pathway
    # returns the PathwayID
    def _UpdatePathway(self, pathwayid: str, pathway: Pathway):
        # update json_pathway table
        self.json_pool.UsePractice("Update", self.json_pathway_table_schema.name, 
                                   {"pathway_id": pathwayid, "pathway_json": pathway.ToJson()},
                                   self.json_pathway_table_schema)

    # Delete a pathway
    # returns the PathwayID     
    def _DeletePathway(self, pathwayid: str):
        # delete from json_pathway table
        self.json_pool.UsePractice("Delete", self.json_pathway_table_schema.name, 
                                   {"pathway_id": pathwayid})

    # Add a post step to a pathway run
    # returns the PostStepID
    def _AddPostStep(self, pathrunid: str, post: Post, owner_agent_id: str, 
                     pathwayid: str,last_poststep: int=0, variables: dict={}):
        # insert into json_poststep table
        # Get the highest poststep_id for this pathrun and increment
        existing_steps = self.json_pool.UsePractice("Select", self.json_poststep_table_schema.name, 
                                                   {"pathrun_id": pathrunid})
        poststepid = 1
        if existing_steps and len(existing_steps) > 0:
            existing_ids = [step.get("poststep_id", 0) for step in existing_steps]
            poststepid = max(existing_ids) + 1
        print(f"Adding post step {poststepid} to pathrun {pathrunid}")
        state = RunState.PENDING
        status_msg = "Pending"
        now = datetime.datetime.now()
        if isinstance(variables, StepVariables):
            variables = variables.ToJson()  
        self.json_pool.UsePractice("Insert", self.json_poststep_table_schema.name, 
                                   {"pathrun_id": pathrunid, "poststep_id": poststepid, 
                                    "owner_agent_id": owner_agent_id,
                                    "post_id": post.post_id, "state": state,
                                    "status_msg": status_msg,
                                    "start_time": now,
                                    "stop_time": None,
                                    "variables": variables,
                                    "pathway_id": pathwayid,
                                    "last_poststep": None,
                                    "last_poststep": last_poststep,
                                    "next_poststep": None},
                                    self.json_poststep_table_schema) 
        poststep = PostStep(pathrunid, post, state, now, None, variables, last_poststep, poststepid, status_msg)
        return poststep

    # Update a post step
    # returns the PostStepID
    def _UpdatePostStep(self, poststep: PostStep):
        # update json_poststep table
        if isinstance(poststep.variables, StepVariables):
            variables = poststep.variables.ToJson()
        else:
            variables = poststep.variables
        return self.json_pool.UsePractice("Update", self.json_poststep_table_schema.name, 
                                   {"pathrun_id": poststep.pathrunid, "poststep_id": poststep.poststep_id, 
                                    "post_id": poststep.post.post_id, "state": poststep.state,
                                    "start_time": datetime.datetime.now(),
                                    "stop_time": None,
                                    "variables": variables,
                                    "status_msg": poststep.status_msg,
                                    "last_poststep": None,
                                    "next_poststep": None},
                                    {"pathrun_id": poststep.pathrunid, "poststep_id": poststep.poststep_id},
                                    self.json_poststep_table_schema)
        
    # Delete a post step
    # returns the PostStepID    
    def _DeletePostStep(self, pathrunid: str, poststepid: int):
        # delete from json_poststep table
        self.json_pool.UsePractice("Delete", self.json_poststep_table_schema.name, 
                                   {"pathrun_id": pathrunid, "poststep_id": poststepid})

    # List all post steps
    # returns a list of PostStep objects
    def _ListPostSteps(self, pathrun_id: str, state: RunState = None):
        # select from json_poststep table
        data = {"pathrun_id": pathrun_id}
        if state is not None:
            data["state"] = state.value
        self.json_pool.UsePractice("Select", self.json_poststep_table_schema.name, 
                                   data)

    def _GetPostStep(self, pathrun_id: str, poststep_id: int):
        # select from json_poststep table
        self.json_pool.UsePractice("Select", self.json_poststep_table_schema.name, 
                                   {"pathrun_id": pathrun_id, "poststep_id": poststep_id})

    def FromJson(self, json_data: dict):
        super().FromJson(json_data)
        if "json_table_prefix" in json_data:
            self.json_table_prefix = json_data["json_table_prefix"]
        if "graph_table_prefix" in json_data:
            self.graph_table_prefix = json_data["graph_table_prefix"]

    def ToJson(self):
        json_data = super().ToJson()
        json_data["json_pool"] = self.json_pool
        json_data["graph_pool"] = self.graph_pool
        json_data["json_table_prefix"] = self.json_table_prefix
        json_data["graph_table_prefix"] = self.graph_table_prefix
        return json_data    
