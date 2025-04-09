# Pathfinder is a service
# It takes a pathway and parameters
# the run method runs the posts in the pathway with the given parameters
# the run method returns a result
# the result is a dictionary with the following keys:
# - status: the status of the pathway
# - result: the result of the pathway
# - pathway: the pathway that was run
# - parameters: the parameters that were used to run the pathway    
# Pathfinder use Pouch to store and retrieve pathway and parameters
# Pathfinder use Pouch to store the state of a pathway run    

from enum import Enum
import traceback
from .Pit import Pit
from .Agent import Agent
from .Pathway import Pathway,Post
from .Practice import Practice
from .services.Pouch import PathRun, PostStep, Pouch, RunState, StepVariables
import time
import json
import os
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import MetricsData
from typing import Dict, Any
# Create metrics directory if it doesn't exist
metrics_dir = "metrics"
if not os.path.exists(metrics_dir):
    os.makedirs(metrics_dir)
class PathfinderStatus(Enum):
    """
    PathfinderStatus is a class that contains the status of a pathway run.
    """
    STANDBY = "standby"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
class PathfinderState:
    """
    PathfinderState is a class that contains the state of a pathway run.
    """
    def __init__(self, pouch: Pouch):
        self.pouch = pouch
        self.status : PathfinderStatus = PathfinderStatus.STANDBY
        self.pathway : Pathway = None
        self.parameters : Dict[str, Any] = {}
        self.result : Dict[str, Any] = {}
        self.start_time : float = 0
        self.end_time : float = 0
        self.duration : float = 0

# Set up file-based OTLP exporter
class FileMetricExporter(OTLPMetricExporter):
    """
    Custom metrics exporter that writes OpenTelemetry metrics to a local file.
    
    This exporter extends the OTLPMetricExporter and redirects metric data
    to a JSON Lines file instead of sending it to an OTLP endpoint.
    """
    
    def __init__(self, file_path):
        """
        Initialize the FileMetricExporter.
        
        Args:
            file_path: Path to the file where metrics will be written
        """
        super().__init__()
        self.file_path = file_path

    def _export(self, metrics):
        """
        Export metrics data to a file in JSON Lines format.
        
        This method overrides the base exporter's _export method to write
        metrics to a local file instead of sending them to an OTLP endpoint.
        
        Args:
            metrics: MetricsData object containing the metrics to export
            
        Returns:
            None: This method always returns None
        """
        # Convert metrics to JSON-serializable format
        metrics_json = []
        # check if metrics_data is the right type
        if not isinstance(metrics, MetricsData):
            #print(f"Error in _export: metrics_data is not the right type",'ERROR')
            return None
        try:
            for metric in metrics.resource_metrics:
                for scope_metrics in metric.scope_metrics:
                    for metric_data in scope_metrics.metrics:
                        metric_dict = {
                            "name": metric_data.name,
                            "description": metric_data.description,
                            "unit": metric_data.unit,
                            "timestamp": time.time(),
                            "data_points": []
                        }
                    
                        for point in metric_data.data.data_points:
                            data_point = {
                                "attributes": dict(point.attributes),
                                "time_unix_nano": point.time_unix_nano,
                                "value": point.value if hasattr(point, 'value') else None,
                            }
                            if hasattr(point, 'count'):
                                data_point["count"] = point.count
                            if hasattr(point, 'sum'):
                                data_point["sum"] = point.sum
                            if hasattr(point, 'bucket_counts'):
                                data_point["bucket_counts"] = point.bucket_counts
                            metric_dict["data_points"].append(data_point)
                    
                        metrics_json.append(metric_dict)
        
            # Append metrics to file
            with open(self.file_path, 'a') as f:
                for metric in metrics_json:
                        f.write(json.dumps(metric) + '\n')
        except Exception as e:
            print(f"Error in _export: {e}")
            print(f"{traceback.format_exc()}")
        return None

# Create file exporter
file_exporter = FileMetricExporter(os.path.join(metrics_dir, "pathfinder_metrics.jsonl"))
metric_reader = PeriodicExportingMetricReader(file_exporter, export_interval_millis=5000)
provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("pathfinder_metrics")

# Create metrics
pathway_duration = meter.create_histogram(
    name="pathway_execution_duration",
    description="Duration of pathway execution",
    unit="s"
)

post_duration = meter.create_histogram(
    name="post_execution_duration",
    description="Duration of post execution",
    unit="s"
)

pathway_counter = meter.create_counter(
    name="pathway_executions",
    description="Number of pathway executions",
)

post_counter = meter.create_counter(
    name="post_executions",
    description="Number of post executions",
)

error_counter = meter.create_counter(
    name="execution_errors",
    description="Number of execution errors",
)

class Pathfinder(Pit):
    """
    !!! This is a work in progress !!!
    
    Pathfinder is a service that executes pathways with provided parameters.
    
    A Pathfinder takes a pathway and parameters,
    runs the posts in the pathway with the given parameters, and returns results.
    It can be used to run a pathway in a single agent or in a multi-agent environment.

    If a pouch is provided, the Pathfinder will use it to store and retrieve pathway and parameters.
    If a pouch is not provided, the Pathfinder can run pathways with no memory or state.

    """
        # TODO: Support async execution of pathways though Pouch
        # TODO: Support concurrent execution of pathways
        # TODO: Support OpenTelemetry metrics
    
    def __init__(self, agent: Agent, name="Pathfinder", 
                 description="Pathfinder is a service that takes a pathway and parameters and runs the posts in the pathway with the given parameters",
                 pouch = None):
        """
        Initialize a Pathfinder instance.
        
        Args:
            agent: The agent that owns this Pathfinder
            name: Name of the Pathfinder
            description: Description of the Pathfinder's purpose
        """
        super().__init__(name, description)
        self.agent = agent
        if pouch:
            if isinstance(pouch, str):
                self.pouch=agent.services[pouch]
            elif isinstance(pouch, Pouch):
                self.pouch=pouch
            else:
                raise ValueError(f"Invalid pouch type: {type(pouch)}")
        else:
            self.pouch=None

        self.state = PathfinderState(pouch)
        self.state.status = PathfinderStatus.STANDBY
        
        # Add practices
        self.AddPractice(Practice("GetStatus", self.GetStatus))
        self.AddPractice(Practice("Run", self.Run))
        self.AddPractice(Practice("GetState", self.GetState))
                
        # Copy log subscribers from agent
        if hasattr(agent, 'log_subscribers'):
            initial_subscribers = len(self.log_subscribers)
            for subscriber in agent.log_subscribers:
                if subscriber not in self.log_subscribers:
                    self.log_subscribers.append(subscriber)
            
            if len(self.log_subscribers) > initial_subscribers:
                self.log(f"Inherited {len(self.log_subscribers) - initial_subscribers} log subscribers from agent", 'DEBUG')
            
        # Verify log subscribers
        self.log(f"Pathfinder has {len(self.log_subscribers)} log subscribers", 'DEBUG')
            
        # Test log generation
        self.log(f"Pathfinder initialized with agent: {agent.name}", 'INFO')

    def _find_agent_practice(self, practice: str):
        """
        Find an agent with the specified practice.
        First checks this agent's pits, then searches for practices in other agents through plazas.
        
        Args:
            practice: The practice to find
            
        Returns:
            Dict or None: Information about the agent with the practice, or None if not found
        """
        # First check if this agent has a direct practice with this name
        if practice in self.agent.practices:
            self.log(f"Found practice {practice} directly in our agent", 'DEBUG')
            return {"agent_address": f"{self.agent.agent_id}@MainPlaza", "practice": practice}
            
        # Check if the practice is in any of our agent's pits
        for pit_type, pits in self.agent.pits.items():
            for pit_name, pit in pits.items():
                if hasattr(pit, 'practices') and practice in pit.practices:
                    self.log(f"Found practice {practice} in local pit {pit_name}", 'DEBUG')
                    return {"agent_address": f"{self.agent.agent_id}@MainPlaza", "practice": f"{pit_name}/{practice}"}
        
        # If not found locally, check other agents through plazas
        plaza_name = "MainPlaza"
        self.log(f"Practice {practice} not found locally, searching in remote agents", 'DEBUG')
        agents_info = self.agent.UsePractice(f"{plaza_name}/ListActiveAgents")
        #self.log(f"agents_info: {agents_info}","DEBUG")
        for agent_info in agents_info:
            # Skip ourselves - we already checked local pits
            if agent_info["agent_id"] == self.agent.agent_id:
                continue
                
            # find in each pits of the agent
            for pit_type in agent_info["agent_info"]["components"].keys():
                for pit in agent_info["agent_info"]["components"][pit_type].keys():
                    if pit in agent_info["agent_info"]["components"][pit_type]:
                        #self.log(f"pit in agent_info: {pit}","DEBUG")
                        #self.log(f"{agent_info['agent_info']['components'][pit_type]}","DEBUG")
                        if "practices" in agent_info["agent_info"]["components"][pit_type][pit]:
                            for remote_practice in agent_info["agent_info"]["components"][pit_type][pit]['practices']:
                                if remote_practice == practice:
                                    self.log(f"Found practice: {pit+'/'+practice} in remote agent {agent_info['agent_id']}","INFO")
                                    return {"agent_address": agent_info["agent_id"]+'@'+plaza_name, "practice": pit+"/"+practice}
                    else:
                        self.log(f"pit not in agent_info: {pit}","DEBUG")
        
        self.log(f"No agent found for practice {practice}", 'WARNING')
        return None
    
    def GetStatus(self):
        """
        Get the current status of the Pathfinder.
        
        Returns:
            str: The current status of the Pathfinder
        """
        return self.state.status
    
    def GetState(self):
        """
        Get the current state of the Pathfinder.
        """
        return self.state
    
    # run_post is a helper function to run a post with the given variables
    def run_post(self, poststep: PostStep, variables: Dict[str, Any]):
        """
        Run a post with the given variables.
        
        Args:
            poststep: The poststep to run
            variables: The variables to use
            
        Returns:
            Dict[str, Any]: Updated variables dictionary
        """
        self.log(f"Starting post execution: {poststep.post.name}", 'INFO')
        start_time = time.time()
        # poststep is created in the pouch

        try:
            # Find suitable agent for this practice
            self.log(f"Finding agent for practice: {poststep.post.practice}", 'DEBUG')
            poststep.status_msg = f"Finding agent for practice {poststep.post.practice}"
            poststep.state = RunState.RUNNING
            self.pouch.UsePractice("UpdatePostStep", poststep)
            agent_info = self._find_agent_practice(poststep.post.practice)
            # Process parameters and prepare practice input
            variables_copy = variables.copy()  # Create a copy to avoid modifying the original
            
            if agent_info:
                self.log(f"Found agent for practice {poststep.post.practice}: {agent_info}", 'DEBUG')
                # Prepare practice input by processing parameters
                practice_input = {}
                for key, value in poststep.post.parameters.items():
                    processed_value = value
                    if isinstance(value, str):
                        # Replace {key} placeholders with input values
                        import re
                        # Find all {variable} patterns in the string
                        placeholder_pattern = r'\{([^{}]+)\}'
                        placeholders = re.findall(placeholder_pattern, processed_value)
                        
                        # Replace each placeholder with its value from variables
                        for placeholder in placeholders:
                            if placeholder in variables:
                                placeholder_value = str(variables[placeholder])     
                                # Replace the placeholder with its value
                                processed_value = processed_value.replace(f"{{{placeholder}}}", placeholder_value)
                                self.log(f"Replaced placeholder {{{placeholder}}} with value: {placeholder_value}", 'DEBUG')
                                break
                            else:
                                self.log(f"Warning: Placeholder {{{placeholder}}} not found]", 'WARNING')
                    practice_input[key] = processed_value
                
                self.log(f"Calling practice {agent_info['practice']} with inputs: {practice_input}", 'DEBUG')
                poststep.status_msg = f"Calling practice {agent_info['practice']}"
                poststep.state = RunState.RUNNING
                self.pouch.UsePractice("UpdatePostStep", poststep)
                responses = self.agent.UsePracticeRemote(agent_info['practice'], agent_info['agent_address'], practice_input)
                self.log(f"Practice {agent_info['practice']} returned: {responses}", 'DEBUG')
                
                # Process outputs and update variables
                response=json.loads(responses[0]['content'])['body']
                if 'result' in response:
                    if hasattr(poststep.post, 'outputs') and poststep.post.outputs:
                        for output_key, output_config in poststep.post.outputs.items():
                            if 'field_mapping' in output_config:
                                field_mapping = output_config['field_mapping']
                                for src_field, dest_field in field_mapping.items():
                                    if src_field in response['result']:
                                        variables_copy[dest_field] = response['result'][src_field]
                                        self.log(f"Mapped output {src_field} to variable {dest_field}: {variables_copy[dest_field]}", 'DEBUG')
                                    else:
                                        self.log(f"Warning: Source field {src_field} not found in response", 'WARNING')
                else:
                    self.log(f"Warning: No 'result' field in response: {response.keys()}", 'WARNING')
                
                # Record successful post execution
                post_counter.add(1, {"post_id": poststep.post.post_id, "status": "success"})
                self.log(f"Post {poststep.post.name} completed successfully", 'INFO')
                poststep.status_msg = f"Finished post {poststep.post.name}"
                poststep.state = RunState.COMPLETED
                poststep.variables = variables_copy
                self.pouch.UsePractice("UpdatePostStep", poststep)
                return variables_copy

            else:
                error_msg = f"No agent found for practice {poststep.post.practice}"
                self.log(error_msg, 'WARNING')
                error_counter.add(1, {"post_id": poststep.post.post_id, "error": "no_agent_found"})
                return variables
                
        except Exception as e:
            error_msg = f"Error in post execution: {str(e)}\n{traceback.format_exc()}"
            self.log(error_msg, 'ERROR')
            error_counter.add(1, {"post_id": poststep.post.post_id, "error": str(e)})
            # Record execution time even on error
            end_time = time.time()
            self.log(f"Post execution failed after {end_time - start_time:.4f} seconds", 'DEBUG')
            raise
        finally:
            duration = time.time() - start_time
            post_duration.record(duration, {"post_id": poststep.post.post_id})
            self.log(f"Post execution took {duration:.4f} seconds", 'DEBUG')

    def Run(self, pathway, days_to_live=0, *args, **inputs: dict):
        """
        Run a pathway with the given inputs.
        
        Args:
            pathway: The pathway to run (can be a Pathway object or a dict or a str)
            days_to_live: The number of days to live for the pathway run from start_time
            *args: Additional positional arguments
            **inputs: The input parameters for the pathway
            
        Returns:
            dict: The output variables after pathway execution
        """
        # Record pathway execution metrics
        self.log(f"Starting pathway execution: {pathway.pathway_id if hasattr(pathway, 'pathway_id') else 'Unnamed'}", 'INFO')
        start_time = time.time()
        try:
            # if pathway is a dict, convert it to a Pathway object
            # if pathway is a str, load it from the pouch
            # if pathway is a Pathway object, use it as is
            # otherwise, raise an error
            if isinstance(pathway, dict):
                self.log(f"Converting pathway from dictionary to Pathway object", 'DEBUG')
                pathway = Pathway.FromJson(pathway)
            elif isinstance(pathway, str):
                self.log(f"Loading pathway from pouch: {pathway}", 'DEBUG')
                pathway = self.pouch.UsePractice("GetPathway", pathway)
            elif isinstance(pathway, Pathway):
                self.log(f"Using provided pathway object", 'DEBUG')
            else:
                raise ValueError(f"Invalid pathway type: {type(pathway)}")
            
            # save the pathway to the pouch if not already there
            if self.pouch:
                if not self.pouch.UsePractice("GetPathway", pathway.pathway_id):
                    self.pouch.UsePractice("CreatePathway", pathway)
                    self.log(f"Created pathway {pathway.pathway_id} in pouch", 'DEBUG')
                else:
                    self.log(f"Pathway {pathway.pathway_id} already exists in pouch", 'DEBUG')

            # create a path run in the pouch
            if not inputs:
                print("No inputs provided, using empty dictionary")
                inputs = {}
            else:
                print(f"Inputs provided: {inputs}")
            if "pathrun_description" in inputs and inputs["pathrun_description"]:
                description=inputs["pathrun_description"]
            else:
                description=pathway.description
            print(f"Creating path run with description: {description}")
            self.log(f"Creating path run with description: {description}", 'DEBUG')
            pathrun = self.pouch.UsePractice("CreatePathRun", self.agent.agent_id, pathway, True, description, inputs, days_to_live)
            self.log(f"Created path run: {pathrun.pathrun_id}", 'DEBUG')
            result = self.Resume(pathrun, inputs)
            return result
        except Exception as e:
            self.log(f"Error creating path run: {e}", 'ERROR')
            raise
        finally:
            duration = time.time() - start_time
            pathway_duration.record(duration, {"pathway_id": pathway.pathway_id})
            self.log(f"Pathway execution took {duration:.4f} seconds", 'INFO')

    def Resume(self, pathrun:PathRun, inputs: dict):
        """
        Resume a pathway run from a pathrun_id.
        """
        if not isinstance(pathrun, PathRun):
            raise ValueError(f"Invalid pathrun type: {type(pathrun)}")
        if pathrun.state == RunState.RUNNING:
            raise ValueError(f"Pathrun {pathrun.pathrun_id} is running, cannot resume")
        if pathrun.state == RunState.COMPLETED:
            raise ValueError(f"Pathrun {pathrun.pathrun_id} is completed, cannot resume")
        
        pathrun.state = RunState.RUNNING
        self.pouch.UsePractice("UpdatePathRun", pathrun.pathrun_id, state=RunState.RUNNING, status_msg="PathRun resumed", inputs=inputs)
        self.log(f"Resuming pathway run: {pathrun.pathrun_id}", 'INFO')
        start_time = time.time()

        try:
            # check if pathrun is in pouch
            if not self.pouch.UsePractice("GetPathRun", pathrun.pathrun_id):
                raise ValueError(f"Pathrun {pathrun.pathrun_id} not found in pouch")
            # check if pathway is in pouch
            # if not self.pouch.UsePractice("GetPathway", pathrun.pathway.pathway_id):
            #     raise ValueError(f"Pathway {pathrun.pathway.pathway_id} not found in pouch")
            # check if any poststeps are in pouch
            poststeps = self.pouch.UsePractice("ListPostSteps", pathrun.pathrun_id)
            if not poststeps:
                # Start from entrance post
                current_post = pathrun.pathway.entrance_post
                # Initialize variables with provided inputs
                self.log(f"Initial variables: {pathrun.inputs}", 'DEBUG')
                variables = inputs
                self.log(f"Initial variables: {variables}", 'DEBUG')
                last_poststep_id = 0
                # Main pathway execution loop
                poststep=self.pouch.UsePractice("AddPostStep", pathrun.pathrun_id, current_post,
                                               self.agent.agent_id, pathrun.pathway.pathway_id,last_poststep_id,    
                                               variables=StepVariables(inputs, current_post.parameters))
                print(f"Poststep variables: {poststep.variables}")
                self.log(f"Starting with entrance post: {current_post.post_id}", 'INFO')
            else:
                # check if any poststeps are failed or stopped
                failed_poststeps = [poststep for poststep in poststeps if poststep.state == RunState.FAILED or poststep.state == RunState.STOPPED]
                if failed_poststeps:
                    current_post = failed_poststeps[-1].post
                    poststep = failed_poststeps[-1]
                    self.log(f"Starting with last failed poststep: {current_post.post_id}", 'INFO')
                else:
                    current_post = poststeps[-1].post
                    poststep = poststeps[-1]
                    self.log(f"Starting with last poststep: {current_post.post_id}", 'INFO')
                if isinstance(poststep.variables, StepVariables):
                    variables = poststep.variables.ToJson()
                else:
                    variables = poststep.variables

            while current_post is not None:
                if poststep.state == RunState.COMPLETED:
                    self.log(f"Post {current_post.post_id} completed with variables: {variables}", 'DEBUG')
                else:
                    self.log(f"Executing post: {current_post.post_id} with practice: {current_post.practice}", 'INFO')
                    last_poststep_id = poststep.poststep_id
                    variables = self.run_post(poststep, variables)
                    self.log(f"Post {current_post.post_id} completed with variables: {variables}", 'DEBUG')
                    
                # Check for exit condition
                if current_post.next_post == "exit":
                    self.log(f"Reached exit post, finishing pathway", 'INFO')
                    break
                else:
                    # Find the next post in the posts list
                    next_post = next((post for post in pathrun.pathway.posts if post.post_id == current_post.next_post), None)
                    if next_post is None:
                        self.log(f"Could not find next post {current_post.next_post}, finishing pathway", 'WARNING')
                        break
                    self.log(f"Moving to next post: {next_post.post_id}", 'DEBUG')
                    current_post = next_post
                    next_poststep=self.pouch.UsePractice("AddPostStep", pathrun.pathrun_id, current_post, self.agent.agent_id, pathrun.pathway.pathway_id,last_poststep_id)
                    poststep.next_poststep = next_poststep.poststep_id
                    self.pouch.UsePractice("UpdatePostStep", poststep)
                    self.log(f"Created post step: {next_poststep.poststep_id}", 'DEBUG')
                    poststep = next_poststep
   
            # Record successful pathway execution
            pathway_counter.add(1, {"pathway_id": pathrun.pathway.pathway_id, "status": "success"})
            self.log(f"Pathway {pathrun.pathway.pathway_id} completed successfully", 'INFO')
            if "result" in variables:
                self.pouch.UsePractice("CompletePathRun", pathrun.pathrun_id, variables["result"])
            else:
                self.pouch.UsePractice("CompletePathRun", pathrun.pathrun_id)
            return variables
        except Exception as e:
            error_msg = f"Error in pathway execution: {str(e)}\n{traceback.format_exc()}"
            self.log(error_msg, 'ERROR')
            error_counter.add(1, {"pathway_id": pathrun.pathway.pathway_id, "error": str(e)})
            raise
        finally:
            duration = time.time() - start_time
            pathway_duration.record(duration, {"pathway_id": pathrun.pathway.pathway_id})
            self.log(f"Pathway execution took {duration:.4f} seconds", 'INFO')


    def FromJson(self, json_data: dict):
        """
        Initialize a Pathfinder from a JSON representation.
        
        This method deserializes a Pathfinder instance from a dictionary
        containing the pathway, parameters, and agent information.
        
        Args:
            json_data: Dictionary with serialized Pathfinder data
            
        Returns:
            Pathfinder: Self reference for method chaining
        """
        self.pathway = Pathway.FromJson(json_data)
        self.parameters = json_data["parameters"]
        self.agent = json_data["agent"]
        self.pathfinder = Pathfinder(self.agent)
        return self

    def ToJson(self):
        """
        Convert Pathfinder to a JSON-serializable dictionary.
        
        This method serializes the Pathfinder's state to a dictionary
        that can be saved or transmitted.
        
        Returns:
            Dict: JSON-serializable dictionary representation
        """
        return {
            "pathway": self.pathway.ToJson(),
            "parameters": self.parameters,
            "agent": self.agent.ToJson()
        }
