import traceback
import streamlit as st
import json
import os
import time
import datetime
import pandas as pd
from prompits.Agent import Agent, AgentInfo
from prompits.Pit import Pit

class PlazaMonitor(Pit):
    def __init__(self):
        super().__init__("PlazaMonitor",  "Monitor the status of the plaza")
        self.log("Initializing PlazaMonitor")
        self.agent = None
        
    def create_agent_from_json(self, json_path):
        self.log(f"Loading agent config from {json_path}")
        with open(json_path, 'r') as f:
            config = json.load(f)
        agent_info=AgentInfo.FromJson(config)
        self.agent = Agent.FromJson(agent_info)
        self.log(f"Agent created: {self.agent.agent_id}")
        return self.agent
        
    def get_plaza_status(self):
        if not self.agent:
            raise ValueError("Agent not initialized")
        
        self.log("Getting plaza status")
        results = {}
        for plaza_name, plaza in self.agent.plazas.items():
            self.log(f"Checking plaza: {plaza_name}")
            active_agents = self.agent.UsePractice(f"{plaza_name}/ListActiveAgents")
            plaza_agents = []
            for active_agent in active_agents:
                #self.log(f"{active_agent}","DEBUG")
                self.log(f"Active agent: {active_agent["agent_id"]}","DEBUG")
                plaza_agents.append(active_agent)
            results[plaza_name] = plaza_agents
        
        return results
    
    def get_agent_info(self, agent_id, plaza_name):
        if not self.agent:
            raise ValueError("Agent not initialized")
        
        self.log(f"Getting info for agent: {agent_id} from plaza: {plaza_name}")
        try:
            # Use the GetAgentInfo practice if available
            agent_info = self.agent.UsePractice(f"{plaza_name}/GetAgentInfo", agent_id=agent_id)
            return agent_info
        except Exception as e:
            self.log(f"Error getting agent info: {str(e)}", "ERROR")
            return None
    
    def ToJson(self):
        return self.agent.ToJson()
    
    def FromJson(self, json_data):
        raise NotImplementedError("FromJson not implemented")

def process_status_data(status, monitor):
    """Process raw status data into display format"""
    processed_data = {}
    raw_data = {}
    for plaza_name, agents in status.items():
        if not agents:
            processed_data[plaza_name] = []
            raw_data[plaza_name] = []
        else:
            agent_data = []
            raw_agents = []
            for idx, agent_info in enumerate(agents):
                # Get update_time (timestamp) and convert to seconds ago
                update_time = agent_info.get('update_time', 0)
                if update_time:
                    try:
                        # Check the type of update_time
                        if isinstance(update_time, datetime.datetime):
                            update_datetime = update_time
                        elif isinstance(update_time, (int, float)):
                            update_datetime = datetime.datetime.fromtimestamp(update_time)
                        elif isinstance(update_time, str):
                            try:
                                update_datetime = datetime.datetime.fromtimestamp(float(update_time))
                            except:
                                update_datetime = datetime.datetime.fromisoformat(update_time)
                        else:
                            raise TypeError(f"Cannot handle update_time of type {type(update_time)}")
                            
                        now = datetime.datetime.now()
                        seconds_ago = int((now - update_datetime).total_seconds())
                        last_seen = f"{seconds_ago} seconds ago"
                    except Exception as e:
                        monitor.log(f"Error calculating time difference: {e} for value: {update_time} of type {type(update_time)}", "ERROR")
                        last_seen = "Unknown"
                else:
                    last_seen = "Unknown"
                
                # Store the display data
                agent_data.append({
                    "Agent Name": agent_info.get("agent_name", "Unknown"),
                    "Last Seen": last_seen,
                    "Status": agent_info.get("status", "Unknown"),  
                    "Agent ID": agent_info.get("agent_id", "Unknown")
                })
                
                # Store the raw data for future reference
                raw_agents.append(agent_info)
                
            processed_data[plaza_name] = agent_data
            raw_data[plaza_name] = raw_agents
    
    return processed_data, raw_data

# Must be the first Streamlit command
st.set_page_config(page_title="Plaza Status", page_icon="🏛️", layout="wide")

# Initialize session state
if "monitor" not in st.session_state:
    st.session_state.monitor = PlazaMonitor()
    st.session_state.refresh_count = 0
    st.session_state.auto_refresh = True
    st.session_state.last_update_time = None
    st.session_state.refresh_interval = 10
    st.session_state.countdown_interval = 1.0  # Ensure this is a float
    st.session_state.selected_agent = None
    st.session_state.selected_plaza = None
    st.session_state.status_data = {}
    st.session_state.raw_data = {}

# Get file path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
agent_config_path = os.path.join(base_dir, "monitor_agent.json")

# Initialize agent if needed
monitor = st.session_state.monitor
if not monitor.agent:
    try:
        with st.spinner("Creating agent..."):
            agent = monitor.create_agent_from_json(agent_config_path)
            st.success(f"Agent {agent.agent_id} created successfully")
    except Exception as e:
        st.error(f"Failed to create agent: {str(e)}")

# Auto-refresh mechanism 
if "refresh_trigger" not in st.session_state:
    st.session_state.refresh_trigger = "initial"
    st.session_state.next_refresh = time.time() + st.session_state.refresh_interval

# Main title
st.title("Plaza Status Monitor")

# Control bar with auto-refresh and refresh button
control_col1, control_col2, control_col3 = st.columns([4, 2, 1])
with control_col1:
    refresh_label = f"Auto refresh every {st.session_state.refresh_interval} seconds"
    auto_refresh = st.checkbox(refresh_label, 
                            value=st.session_state.auto_refresh,
                            key=f"auto_refresh_{st.session_state.refresh_count}")
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
        if auto_refresh:
            st.session_state.next_refresh = time.time() + st.session_state.refresh_interval

with control_col2:
    if st.session_state.auto_refresh:
        remaining = max(0, int(st.session_state.next_refresh - time.time()))
        st.write(f"Next refresh: {remaining}s")

with control_col3:
    # Manual refresh button
    if st.button("Refresh Now", key=f"refresh_btn_{st.session_state.refresh_count}"):
        st.session_state.refresh_trigger = "manual"
        st.session_state.next_refresh = time.time() + st.session_state.refresh_interval

# Update data based on trigger
trigger_refresh = False
if st.session_state.refresh_trigger == "initial" or st.session_state.refresh_trigger == "manual":
    trigger_refresh = True
    st.session_state.refresh_trigger = "waiting"
elif st.session_state.auto_refresh and time.time() >= st.session_state.next_refresh:
    trigger_refresh = True
    st.session_state.next_refresh = time.time() + st.session_state.refresh_interval

# Get plaza status (only when needed)
status_container = st.container()
agent_detail_container = st.container()

if trigger_refresh:
    try:
        # Clear the placeholder
        with status_container:
            raw_status = monitor.get_plaza_status()
            status_data, raw_data = process_status_data(raw_status, monitor)
            
            # Store in session state for future reference
            st.session_state.status_data = status_data
            st.session_state.raw_data = raw_data
            st.session_state.last_update_time = datetime.datetime.now()
            
            # Display the timestamp
            st.write(f"Last updated: {st.session_state.last_update_time.strftime('%H:%M:%S')}")
            
            # Display all plazas and their agents
            for plaza_name, agents in status_data.items():
                st.subheader(f"Plaza: {plaza_name}")
                
                if not agents:
                    st.info("No active agents in this plaza")
                else:
                    # Create a dataframe for display
                    df = pd.DataFrame(agents)
                    
                    # Display interactive dataframe with selection
                    st.write("View agent details:")
                    selection = st.dataframe(
                        df,
                        use_container_width=True,
                        column_config={
                            "Agent Name": st.column_config.TextColumn("Agent Name"),
                            "Last Seen": st.column_config.TextColumn("Last Seen"),
                            "Status": st.column_config.TextColumn("Status"),
                            "Agent ID": st.column_config.TextColumn("Agent ID")
                        },
                        hide_index=True
                    )
                    
                    # Create a dropdown selector instead of buttons
                    agent_options = {agent["Agent ID"]: f"{agent['Agent Name']} ({agent['Agent ID']})" for agent in agents}
                    selected_agent_id = st.selectbox(
                        "Select an agent to view details:",
                        options=list(agent_options.keys()),
                        format_func=lambda x: agent_options[x],
                        key=f"select_{plaza_name}_{st.session_state.refresh_count}"
                    )
                    
                    # Add a view button
                    if st.button("View Agent Details", key=f"view_btn_{plaza_name}_{st.session_state.refresh_count}"):
                        st.session_state.selected_agent = selected_agent_id
                        st.session_state.selected_plaza = plaza_name
                        st.rerun()
            
            st.session_state.refresh_count += 1
    except Exception as e:
        with status_container:
            st.error(f"Error refreshing status: {str(e)}")
            st.code(traceback.format_exc())
else:
    # Just redisplay the last data
    if st.session_state.last_update_time:
        with status_container:
            # Display the timestamp
            st.write(f"Last updated: {st.session_state.last_update_time.strftime('%H:%M:%S')}")
            
            try:
                # If we have data in session state, use it
                if st.session_state.status_data:
                    # Display all plazas and their agents
                    for plaza_name, agents in st.session_state.status_data.items():
                        st.subheader(f"Plaza: {plaza_name}")
                        
                        if not agents:
                            st.info("No active agents in this plaza")
                        else:
                            # Create a dataframe for display
                            df = pd.DataFrame(agents)
                            
                            # Display interactive dataframe with selection
                            st.write("View agent details:")
                            selection = st.dataframe(
                                df,
                                use_container_width=True,
                                column_config={
                                    "Agent Name": st.column_config.TextColumn("Agent Name"),
                                    "Last Seen": st.column_config.TextColumn("Last Seen"),
                                    "Status": st.column_config.TextColumn("Status"),
                                    "Agent ID": st.column_config.TextColumn("Agent ID")
                                },
                                hide_index=True
                            )
                            
                            # Create a dropdown selector instead of buttons
                            agent_options = {agent["Agent ID"]: f"{agent['Agent Name']} ({agent['Agent ID']})" for agent in agents}
                            selected_agent_id = st.selectbox(
                                "Select an agent to view details:",
                                options=list(agent_options.keys()),
                                format_func=lambda x: agent_options[x],
                                key=f"select_{plaza_name}_{st.session_state.refresh_count}"
                            )
                            
                            # Add a view button
                            if st.button("View Agent Details", key=f"view_btn_{plaza_name}_{st.session_state.refresh_count}"):
                                st.session_state.selected_agent = selected_agent_id
                                st.session_state.selected_plaza = plaza_name
                                st.rerun()
                # Otherwise, refresh the data
                else:
                    raw_status = monitor.get_plaza_status()
                    status_data, raw_data = process_status_data(raw_status, monitor)
                    
                    # Store in session state for future reference
                    st.session_state.status_data = status_data
                    st.session_state.raw_data = raw_data
                    
                    # Display all plazas and their agents
                    for plaza_name, agents in status_data.items():
                        st.subheader(f"Plaza: {plaza_name}")
                        
                        if not agents:
                            st.info("No active agents in this plaza")
                        else:
                            # Create a dataframe for display
                            df = pd.DataFrame(agents)
                            
                            # Display interactive dataframe with selection
                            st.write("View agent details:")
                            selection = st.dataframe(
                                df,
                                use_container_width=True,
                                column_config={
                                    "Agent Name": st.column_config.TextColumn("Agent Name"),
                                    "Last Seen": st.column_config.TextColumn("Last Seen"),
                                    "Status": st.column_config.TextColumn("Status"),
                                    "Agent ID": st.column_config.TextColumn("Agent ID")
                                },
                                hide_index=True
                            )
                            
                            # Create a dropdown selector instead of buttons
                            agent_options = {agent["Agent ID"]: f"{agent['Agent Name']} ({agent['Agent ID']})" for agent in agents}
                            selected_agent_id = st.selectbox(
                                "Select an agent to view details:",
                                options=list(agent_options.keys()),
                                format_func=lambda x: agent_options[x],
                                key=f"select_{plaza_name}_{st.session_state.refresh_count}"
                            )
                            
                            # Add a view button
                            if st.button("View Agent Details", key=f"view_btn_{plaza_name}_{st.session_state.refresh_count}"):
                                st.session_state.selected_agent = selected_agent_id
                                st.session_state.selected_plaza = plaza_name
                                st.rerun()
            except Exception as e:
                st.error(f"Error displaying status: {str(e)}")
                st.code(traceback.format_exc())

# Display selected agent details if any
with agent_detail_container:
    if st.session_state.selected_agent and st.session_state.selected_plaza:
        st.markdown("---")
        st.header(f"Agent Details: {st.session_state.selected_agent}")
        
        # Find the agent data from the raw data in session state
        agent_data = None
        try:
            # Try to get agent data from session state first
            raw_data = st.session_state.raw_data
            if st.session_state.selected_plaza in raw_data:
                for agent in raw_data[st.session_state.selected_plaza]:
                    if agent.get("agent_id", "") == st.session_state.selected_agent:
                        agent_data = agent
                        break
            
            # If not found, try to get more detailed agent info
            if not agent_data:
                agent_data = monitor.get_agent_info(st.session_state.selected_agent, st.session_state.selected_plaza)
                        
            if agent_data:
                # Organize the information in tabs for better readability
                tabs = st.tabs(["General Info", "Pits", "Practices", "Raw Data"])
                
                with tabs[0]:  # General Info
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Basic Information")
                        st.markdown(f"**Name:** {agent_data.get('agent_name', 'N/A')}")
                        st.markdown(f"**ID:** {agent_data.get('agent_id', 'N/A')}")
                        st.markdown(f"**Status:** {agent_data.get('status', 'N/A')}")
                        st.markdown(f"**Version:** {agent_data.get('version', 'N/A')}")
                    
                    with col2:
                        st.markdown("### Connection Details")
                        st.markdown(f"**Plaza:** {st.session_state.selected_plaza}")
                        if "last_seen" in agent_data:
                            st.markdown(f"**Last Seen:** {agent_data.get('last_seen', 'N/A')}")
                        if "host" in agent_data:
                            st.markdown(f"**Host:** {agent_data.get('host', 'N/A')}")
                        if "port" in agent_data:
                            st.markdown(f"**Port:** {agent_data.get('port', 'N/A')}")
                
                with tabs[1]:  # Pits
                    st.markdown("### Agent Pits")
                    
                    # Create a list of all pits and components
                    all_pits = []
                    
                    # Add main pits if available
                    if "components" in agent_data["agent_info"]:
                        pits_type = agent_data["agent_info"]["components"]
                        if isinstance(pits_type, list):
                            for pit in pits_type:
                                if isinstance(pit, dict):
                                    all_pits.append({
                                        "Type": "Pit",
                                        "Name": pit.get("name", "Unnamed Pit"),
                                        "Description": pit.get("description", "No description")
                                    })
                                else:
                                    all_pits.append({
                                        "Type": "Pit",
                                        "Name": str(pit),
                                        "Description": ""
                                    })
                        elif isinstance(pits_type, dict):
                            for pit_key, pit_value in pits_type.items():
                                # Handle nested pits
                                if isinstance(pit_value, dict):
                                    all_pits.append({
                                        "Type": "Pit",
                                        "Name": pit_key,
                                        "Description": pit_value.get("description", "No description")
                                    })
                                    # Add attributes as properties
                                    for k, v in pit_value.items():
                                        if k != "description":
                                            all_pits.append({
                                                "Type": "Property",
                                                "Name": f"  ↳ {k}",
                                                "Description": str(v)
                                            })
                                else:
                                    all_pits.append({
                                        "Type": "Pit",
                                        "Name": pit_key,
                                        "Description": str(pit_value)
                                    })
                    
                    # Display all pits and components in a table
                    if all_pits:
                        pit_df = pd.DataFrame(all_pits)
                        st.dataframe(
                            pit_df,
                            use_container_width=True,
                            column_config={
                                "Type": st.column_config.TextColumn("Type"),
                                "Name": st.column_config.TextColumn("Name"),
                                "Description": st.column_config.TextColumn("Description"),
                            },
                            hide_index=True
                        )
                    else:
                        st.info("No pits or components information available")
                
                with tabs[2]:  # Practices
                    if "practices" in agent_data['agent_info']:
                        st.markdown("### Agent Practices")
                        practices = agent_data["agent_info"]["practices"]
                        
                        # Extract practice details for the table display
                        practice_rows = []
                        practice_names = []
                        input_schemas = []
                        print(f"Practices: {practices}")
                        # Process the practices data into a flat list of practice names
                        if isinstance(practices, list):
                            practice_names = practices
                        elif isinstance(practices, dict):   
                            for practice_name in practices.keys():
                                practice_names.append(f"{practice_name}")
                                practice_value = practices[practice_name]
                                input_schemas.append(f"{practices[practice_name]["input_schema"]}")
                        
                        # Create a DataFrame with the practice information
                        practice_df = pd.DataFrame({
                            "name": practice_names,
                            "input_schema": input_schemas
                        })
                        
                        # Show the practices in a dataframe
                        st.dataframe(
                            practice_df,
                            column_config={
                                "name": st.column_config.TextColumn("Practice Name"),
                                "input_schema": st.column_config.TextColumn("Input Schema")
                            },
                            hide_index=True
                        )
                        
                        # Add use buttons below the table
                        st.markdown("### Use Practice")
                        selected_practice = st.selectbox("Select a practice to use:", practice_names)
                        
                        # Input fields for practice parameters
                        st.markdown("#### Input Parameters")
                        param_json = st.text_area("Parameters (JSON format):", value="{}")
                        
                        # Use practice button
                        if st.button("Use Practice", key="use_practice_btn"):
                            try:
                                # Try to parse the JSON parameters
                                practice_params = json.loads(param_json)
                                
                                # Similar implementation to Pathfinder.run_post()
                                st.info(f"Calling practice: {selected_practice} with parameters: {practice_params}")
                                
                                try:
                                    # Find the plaza and practice
                                    practice_parts = selected_practice.split("/")
                                    if len(practice_parts) == 1:
                                        # Direct practice on the agent
                                        practice_name = practice_parts[0]
                                        agent_address = f"{agent_data['agent_id']}@MainPlaza"
                                    else:
                                        # Practice within a pit
                                        practice_name = selected_practice
                                        agent_address = f"{agent_data['agent_id']}@MainPlaza"
                                    
                                    # Log the process
                                    monitor.log(f"Calling practice {practice_name} on agent {agent_address} with inputs: {practice_params}", "INFO")
                                    
                                    # Execute the practice
                                    responses = monitor.agent.UsePracticeRemote(practice_name, agent_address, practice_params)
                                    
                                    # Display response
                                    st.success("Practice executed successfully!")
                                    result_container = st.container()
                                    
                                    with result_container:
                                        st.subheader("Practice Response")
                                        
                                        # First log the response type and structure for debugging
                                        monitor.log(f"Response type: {type(responses)}", "DEBUG")
                                        monitor.log(f"Response content: {responses}", "DEBUG")
                                        
                                        # Parse the response structure - handle different possible formats
                                        if responses is not None:
                                            try:
                                                # Check if response is an error message
                                                if isinstance(responses, dict) and 'error' in responses:
                                                    st.error(f"Practice execution failed: {responses['error']}")
                                                    st.json(responses)
                                                else:
                                                    # Check response type and handle accordingly
                                                    if isinstance(responses, list) and len(responses) > 0:
                                                        # List of responses
                                                        response_item = responses[0]
                                                        if isinstance(response_item, dict):
                                                            if 'error' in response_item:
                                                                st.error(f"Practice execution failed: {response_item['error']}")
                                                                st.json(response_item)
                                                            elif 'content' in response_item:
                                                                try:
                                                                    content = json.loads(response_item['content'])
                                                                    if 'error' in content:
                                                                        st.error(f"Practice execution failed: {content['error']}")
                                                                        st.json(content)
                                                                    else:
                                                                        st.json(content)
                                                                except json.JSONDecodeError:
                                                                    st.text(response_item['content'])
                                                            else:
                                                                st.json(response_item)
                                                        else:
                                                            st.write(response_item)
                                                    elif isinstance(responses, dict):
                                                        st.json(responses)
                                                    elif isinstance(responses, str):
                                                        try:
                                                            content = json.loads(responses)
                                                            st.json(content)
                                                        except json.JSONDecodeError:
                                                            st.text(responses)
                                                    else:
                                                        st.write(responses)
                                            except Exception as e:
                                                st.error(f"Error parsing response: {str(e)}")
                                                st.text("Raw response:")
                                                st.write(str(responses))
                                        else:
                                            st.warning("No response received (None returned)")
                                    
                                except Exception as e:
                                    st.error(f"Error executing practice: {str(e)}")
                                    st.code(traceback.format_exc())
                                    monitor.log(f"Error executing practice: {str(e)}\n{traceback.format_exc()}", "ERROR")
                            except json.JSONDecodeError:
                                st.error("Invalid JSON format for parameters")
                            except Exception as e:
                                st.error(f"Error using practice: {str(e)}")
                                st.code(traceback.format_exc())
                    else:
                        st.info("No practices information available")
                
                with tabs[3]:  # Raw Data
                    st.markdown("### Raw Agent Data")
                    st.json(agent_data)
            else:
                st.warning("Agent details not available. The agent may have disconnected or the data is unavailable.")
        except Exception as e:
            st.error(f"Error displaying agent details: {str(e)}")
            st.code(traceback.format_exc())

# Settings at the bottom of the page
st.markdown("---")
st.header("Settings")

# Create a two-column layout for settings
settings_col1, settings_col2 = st.columns(2)

with settings_col1:
    # Refresh interval textbox (integer)
    new_refresh_interval = st.number_input(
        "Refresh interval (seconds)", 
        min_value=1, 
        max_value=3600,
        value=st.session_state.refresh_interval,
        step=1,
        key=f"refresh_interval_bottom_{st.session_state.refresh_count}"
    )
    if new_refresh_interval != st.session_state.refresh_interval:
        st.session_state.refresh_interval = int(new_refresh_interval)
        # Reset the next refresh time based on new interval
        st.session_state.next_refresh = time.time() + st.session_state.refresh_interval

with settings_col2:
    # Countdown update interval textbox (float)
    # Ensure all values are consistently float type
    new_countdown_interval = st.number_input(
        "Countdown update interval (seconds)", 
        min_value=0.1, 
        max_value=10.0,
        value=float(st.session_state.countdown_interval),  # Explicitly convert to float
        step=0.1,
        format="%.1f",
        key=f"countdown_interval_bottom_{st.session_state.refresh_count}"
    )
    if new_countdown_interval != st.session_state.countdown_interval:
        st.session_state.countdown_interval = float(new_countdown_interval)

# Handle auto-refresh
if st.session_state.auto_refresh:
    time.sleep(float(st.session_state.countdown_interval))  # Ensure float type for sleep
    st.rerun() 