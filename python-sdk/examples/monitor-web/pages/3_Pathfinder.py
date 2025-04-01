import streamlit as st
import json
import os
import time
import datetime
import traceback
from prompits.Pit import Pit
from prompits.Agent import Agent, AgentInfo
from prompits.Pathway import Pathway
from prompits.Pathfinder import Pathfinder

class PathfinderExecutor(Pit):
    def __init__(self):
        super().__init__("PathfinderExecutor", "Executor for pathfinder operations")
        self.agent = None
        self.pathfinder = None
        self.executions = {}  # Store execution history
        
    def initialize_agent(self, agent_config_path):
        self.log(f"Loading agent config from {agent_config_path}")
        try:
            with open(agent_config_path, 'r') as f:
                json_data = json.load(f)
            
            agent_info = AgentInfo.FromJson(json_data)
            self.agent = Agent.FromJson(agent_info)
            
            # Start the gRPC server component if it exists
            if 'plugs' in self.agent.pits and 'grpc_server' in self.agent.pits['plugs']:
                self.agent.pits['plugs']['grpc_server'].start()
            
            # Create Pathfinder
            self.pathfinder = Pathfinder(self.agent)
            
            return True
        except Exception as e:
            self.log(f"Error initializing agent: {str(e)}", "ERROR")
            return False
            
    def execute_pathfinder(self, pathway_path, input_vars=None):
        if not self.agent or not self.pathfinder:
            raise ValueError("Agent and Pathfinder must be initialized first")
            
        if not input_vars:
            input_vars = {}
            
        try:
            self.log(f"Loading pathway from {pathway_path}")
            with open(pathway_path, 'r') as f:
                json_data = json.load(f)
            pathway = Pathway.FromJson(json_data)
            
            # Generate execution ID based on timestamp
            execution_id = f"exec_{int(time.time())}"
            
            # Store execution information
            self.executions[execution_id] = {
                "pathway_path": pathway_path,
                "input_vars": input_vars,
                "status": "running",
                "start_time": datetime.datetime.now(),
                "result": None,
                "error": None
            }
            
            # Run the pathway
            self.log(f"Running pathway with inputs: {input_vars}")
            result = self.pathfinder.Run(pathway, **input_vars)
            
            # Update execution with result
            self.executions[execution_id]["status"] = "completed"
            self.executions[execution_id]["end_time"] = datetime.datetime.now()
            self.executions[execution_id]["result"] = result
            
            return execution_id, result
        except Exception as e:
            self.log(f"Error executing pathfinder: {str(e)}", "ERROR")
            if execution_id in self.executions:
                self.executions[execution_id]["status"] = "failed"
                self.executions[execution_id]["end_time"] = datetime.datetime.now()
                self.executions[execution_id]["error"] = str(e)
            raise e
        
    def get_execution_status(self, execution_id):
        if execution_id not in self.executions:
            raise ValueError(f"No execution found with ID: {execution_id}")
        return self.executions[execution_id]

    def ToJson(self):
        return self.agent.ToJson()
    
    def FromJson(self, json_data):
        raise NotImplementedError("FromJson not implemented")

def get_pathway_details(pathway_path):
    """Extract pathway details including description and entrance post inputs"""
    try:
        with open(pathway_path, 'r') as f:
            pathway_data = json.load(f)
            
        details = {
            "name": pathway_data.get("name", "Unnamed Pathway"),
            "description": pathway_data.get("description", "No description provided"),
            "entrance_post_inputs": [],
            "variables": pathway_data.get("variables", {})
        }
        
        # Find entrance post
        # The first post is typically the entrance post
        entrance_post =    pathway_data.get("entrance_post", {})

        details["entrance_post_name"] = entrance_post.get("name", "Unknown")
        details["entrance_post_inputs"] = entrance_post.get("inputs", [])
            
        return details
    except Exception as e:
        return {
            "name": "Error",
            "description": f"Error parsing pathway: {str(e)}",
            "entrance_post_inputs": [],
            "variables": {}
        }

# Setup page
st.set_page_config(page_title="Pathfinder Execution", page_icon="🎯", layout="wide")
st.title("Pathfinder Execution")

# Get base directory for file selections
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
agent_config_path = os.path.join(base_dir, "monitor_agent.json")

# Initialize session state
if "executor" not in st.session_state:
    st.session_state.executor = PathfinderExecutor()
    st.session_state.agent_initialized = False
    st.session_state.executions = []
    st.session_state.execution_results = {}
    st.session_state.selected_pathway = None
    st.session_state.pathway_details = None
    
executor = st.session_state.executor

# Auto-initialize agent when page loads
if not st.session_state.agent_initialized:
    with st.spinner("Initializing agent with monitor_agent.json..."):
        if os.path.exists(agent_config_path):
            try:
                if executor.initialize_agent(agent_config_path):
                    st.session_state.agent_initialized = True
                    st.success(f"Agent initialized successfully with monitor_agent.json!")
                else:
                    st.error("Failed to initialize agent. Check the logs for details.")
            except Exception as e:
                st.error(f"Error initializing agent: {str(e)}")
                st.code(traceback.format_exc())
        else:
            st.error(f"Agent configuration file not found: {agent_config_path}")
            st.info("Please make sure monitor_agent.json exists in the monitor-web directory.")

# Pathway execution section
st.header("Pathway Execution")

# Pathway selection
default_pathway_path = os.path.join(base_dir, "pathways", "example_pathway.json")
pathway_paths = []

# Find pathway files in the monitor-web/pathways directory
pathways_dir = os.path.join(base_dir, "pathways")
if not os.path.exists(pathways_dir):
    os.makedirs(pathways_dir)
    st.info(f"Created pathways directory at {pathways_dir}")
    
    # Create an example pathway file
    example_pathway = {
        "name": "Example Pathway",
        "description": "A simple example pathway that demonstrates how to use the Pathfinder. This pathway sends a prompt to an LLM and returns the answer.",
        "posts": [
            {
                "name": "Get Answer",
                "inputs": ["prompt"],
                "outputs": ["answer"],
                "practice": "LLM/Completion"
            }
        ],
        "variables": {
            "prompt": {"type": "string", "default": "What is the capital of France?"},
            "answer": {"type": "string"}
        }
    }
    
    with open(default_pathway_path, 'w') as f:
        json.dump(example_pathway, f, indent=2)
    
    st.info(f"Created example pathway file at {default_pathway_path}")

# Scan for pathway files
for file in os.listdir(pathways_dir):
    if file.endswith(".json"):
        pathway_paths.append(os.path.join(pathways_dir, file))

# Create a selectbox for pathways if any exist
pathway_path = None
if pathway_paths:
    pathway_options = {os.path.basename(path): path for path in pathway_paths}
    selected_pathway = st.selectbox(
        "Select Pathway",
        options=list(pathway_options.keys()),
        disabled=not st.session_state.agent_initialized
    )
    pathway_path = pathway_options[selected_pathway]
    
    # Check if pathway selection changed
    if st.session_state.selected_pathway != pathway_path:
        st.session_state.selected_pathway = pathway_path
        st.session_state.pathway_details = get_pathway_details(pathway_path)
else:
    pathway_path = st.text_input(
        "Pathway File Path", 
        value=default_pathway_path if os.path.exists(default_pathway_path) else "",
        help="Path to the pathway JSON file",
        disabled=not st.session_state.agent_initialized
    )
    
    # Update pathway details if path changed manually
    if pathway_path and os.path.exists(pathway_path):
        if st.session_state.selected_pathway != pathway_path:
            st.session_state.selected_pathway = pathway_path
            st.session_state.pathway_details = get_pathway_details(pathway_path)

# Upload pathway file option
uploaded_file = st.file_uploader("Or upload a pathway JSON file", type=["json"], disabled=not st.session_state.agent_initialized)
if uploaded_file is not None:
    # Save the uploaded file
    save_path = os.path.join(pathways_dir, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    pathway_path = save_path
    st.success(f"Pathway file uploaded and saved to {save_path}")
    
    # Update pathway details for the uploaded file
    st.session_state.selected_pathway = pathway_path
    st.session_state.pathway_details = get_pathway_details(pathway_path)

# Display pathway details if available
if st.session_state.pathway_details:
    with st.expander("Pathway Details", expanded=True):
        details = st.session_state.pathway_details
        
        # Display basic information
        st.markdown(f"### {details['name']}")
        st.markdown(f"**Description:** {details['description']}")
        
        # Display entrance post information
        if 'entrance_post_name' in details:
            st.markdown(f"**Entrance Post:** {details['entrance_post_name']}")
            
        # Display required inputs
        if details['entrance_post_inputs']:
            st.markdown("**Required Inputs:**")
            input_descriptions = []
            print(details['entrance_post_inputs'])
            for input_name in details['entrance_post_inputs']:
                print(input_name)
                print(details['entrance_post_inputs'])
                var_info = details['entrance_post_inputs'].get(input_name, {})
                print(var_info)
                var_type = var_info.get('type', 'any')
                var_desc = var_info.get('description', 'No description')
                input_descriptions.append(f"- **{input_name}** ({var_type}): {var_desc}")
            
            st.markdown("\n".join(input_descriptions))

# Input variables - now smartly populated based on pathway details
st.subheader("Input Variables")
if pathway_path and os.path.exists(pathway_path) and st.session_state.pathway_details:
    try:
        # Get required inputs and their defaults
        details = st.session_state.pathway_details
        default_vars = {}
        
        # Populate only the variables needed for entrance post
        for input_name in details['entrance_post_inputs']:
            if input_name in details['variables'] and 'default' in details['variables'][input_name]:
                default_vars[input_name] = details['variables'][input_name]['default']
            else:
                # Add placeholder for required inputs without defaults
                default_vars[input_name] = f"Enter value for {input_name}"
        
        # Use default variables as initial value
        if default_vars:
            input_vars_text = st.text_area(
                "Input Variables (JSON format)", 
                value=json.dumps(default_vars, indent=2),
                height=150,
                help="JSON formatted input variables for the pathway",
                disabled=not st.session_state.agent_initialized
            )
        else:
            input_vars_text = st.text_area(
                "Input Variables (JSON format)", 
                value='{"prompt": "What is the capital of France?"}',
                height=150,
                help="JSON formatted input variables for the pathway",
                disabled=not st.session_state.agent_initialized
            )
    except Exception:
        input_vars_text = st.text_area(
            "Input Variables (JSON format)", 
            value='{"prompt": "What is the capital of France?"}',
            height=150,
            help="JSON formatted input variables for the pathway",
            disabled=not st.session_state.agent_initialized
        )
else:
    input_vars_text = st.text_area(
        "Input Variables (JSON format)", 
        value='{"prompt": "What is the capital of France?"}',
        height=150,
        help="JSON formatted input variables for the pathway",
        disabled=not st.session_state.agent_initialized
    )

# Execute button
if st.button("Execute Pathway", disabled=not st.session_state.agent_initialized):
    if pathway_path and os.path.exists(pathway_path):
        try:
            # Parse input variables
            input_vars = json.loads(input_vars_text)
            
            # Validate that all required inputs are provided
            if st.session_state.pathway_details and 'entrance_post_inputs' in st.session_state.pathway_details:
                missing_inputs = []
                for required_input in st.session_state.pathway_details['entrance_post_inputs']:
                    if required_input not in input_vars:
                        missing_inputs.append(required_input)
                
                if missing_inputs:
                    st.error(f"Missing required input(s): {', '.join(missing_inputs)}")
                else:
                    with st.spinner("Executing pathway..."):
                        execution_id, result = executor.execute_pathfinder(pathway_path, input_vars)
                        
                        # Store result in session state
                        st.session_state.executions.append(execution_id)
                        st.session_state.execution_results[execution_id] = result
                        
                        st.success(f"Execution completed successfully! Execution ID: {execution_id}")
            else:
                # If we can't validate inputs, just run with what we have
                with st.spinner("Executing pathway..."):
                    execution_id, result = executor.execute_pathfinder(pathway_path, input_vars)
                    
                    # Store result in session state
                    st.session_state.executions.append(execution_id)
                    st.session_state.execution_results[execution_id] = result
                    
                    st.success(f"Execution completed successfully! Execution ID: {execution_id}")
        except json.JSONDecodeError:
            st.error("Invalid JSON format for input variables")
        except Exception as e:
            st.error(f"Error executing pathway: {str(e)}")
            st.code(traceback.format_exc())
    else:
        st.error(f"Pathway file not found: {pathway_path}")

# Execution history
if st.session_state.executions:
    st.header("Execution History")
    
    for execution_id in reversed(st.session_state.executions):
        with st.expander(f"Execution: {execution_id}"):
            try:
                execution_info = executor.get_execution_status(execution_id)
                
                # Display execution details
                st.markdown(f"**Status:** {execution_info['status']}")
                st.markdown(f"**Pathway:** {execution_info['pathway_path']}")
                st.markdown(f"**Start Time:** {execution_info['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if 'end_time' in execution_info and execution_info['end_time']:
                    st.markdown(f"**End Time:** {execution_info['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Calculate duration
                    duration = (execution_info['end_time'] - execution_info['start_time']).total_seconds()
                    st.markdown(f"**Duration:** {duration:.2f} seconds")
                
                # Display input variables
                st.subheader("Input Variables")
                st.json(execution_info['input_vars'])
                
                # Display result or error
                if execution_info['status'] == 'completed':
                    st.subheader("Result")
                    st.json(execution_info['result'])
                elif execution_info['status'] == 'failed' and execution_info['error']:
                    st.subheader("Error")
                    st.error(execution_info['error'])
            except Exception as e:
                st.error(f"Error displaying execution info: {str(e)}")

# Help section
with st.expander("Help & Information"):
    st.markdown("""
    ## Pathfinder Execution Help
    
    The Pathfinder is a tool that uses agents to find the best way to run a pathway.
    
    ### Steps to run a pathway:
    1. Select or upload a pathway file (JSON format)
    2. Review the pathway details and required inputs
    3. Enter input variables in JSON format
    4. Click "Execute Pathway"
    
    ### Example Input Variables:
    ```json
    {
        "prompt": "What is the capital of France?"
    }
    ```
    
    For more information, refer to the Prompits documentation.
    """) 