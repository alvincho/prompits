#!/usr/bin/env python3
"""
Create and run an agent from a JSON configuration file.

This script creates an agent from a JSON configuration file and runs it in an indefinite loop.
The agent will perform actions in each iteration of the loop.
"""

import argparse
import json
import time
import signal
import sys
import os
from datetime import datetime
import traceback
import uuid
import logging
from pathlib import Path
import inspect

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prompits.Agent import Agent, AgentInfo
from prompits.AgentAddress import AgentAddress
from prompits.Practice import Practice
from prompits.messages.StatusMessage import StatusMessage
from prompits.messages.UsePracticeMessage import UsePracticeRequest, UsePracticeResponse

# Global flag to control the main loop
running = True

# Initialize logging system
def setup_logging(verbose_level: str = 'WARNING', log_level: str = 'INFO'):
    """Setup logging system with 4 levels writing to daily files in ~/.prompits/log"""
    # Create log directory if it doesn't exist
    log_dir = os.path.expanduser("~/.prompits/log")
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('prompits')
    logger.propagate = False  # Prevent propagation to avoid duplicate messages
    logger.setLevel(logging.DEBUG)  # Collect all logs at the logger level
    
    # Create daily file handler with date in filename
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'prompits.{today}.log')
    file_handler = logging.FileHandler(
        log_file,
        encoding='utf-8'
    )
    # Set file logging level
    file_level = getattr(logging, log_level.upper(), logging.INFO)
    file_handler.setLevel(file_level)
    
    # Create console handler with specified verbosity
    console_handler = logging.StreamHandler(sys.stdout)
    # Set console verbosity level
    console_level = getattr(logging, verbose_level.upper(), logging.WARNING)
    console_handler.setLevel(console_level)
    
    # Create formatters and add them to the handlers
    file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    console_formatter = logging.Formatter('%(message)s')  # Simple output for console
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Remove any existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)  # Add console handler
    
    if verbose_level == 'DEBUG':
        print(f"Logging setup complete: console level={verbose_level}, file level={log_level}")
        print(f"Console handler level: {logging.getLevelName(console_handler.level)}")
        print(f"File handler level: {logging.getLevelName(file_handler.level)}")
        print(f"Logger level: {logging.getLevelName(logger.level)}")
    
    return logger

# Global logger instance and last log date
logger = None
_last_log_date = None

def init_logging(verbose_level: str = 'WARNING', log_level: str = 'INFO'):
    """Initialize global logging"""
    global logger, _last_log_date
    
    # Remove root handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up our logger
    logger = setup_logging(verbose_level, log_level)
    _last_log_date = datetime.now().date()
    
    # Disable other loggers that might be causing duplicates
    for name in logging.root.manager.loggerDict:
        if name != 'prompits':
            other_logger = logging.getLogger(name)
            other_logger.propagate = False
            other_logger.handlers = []

def log(message, no_timestamp: bool = False, level: str = 'DEBUG'):
    """
    Log a message with a timestamp at specified level.
    
    Args:
        message: The message to log
        no_timestamp: Whether to include timestamp (only affects console output)
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    """
    global logger, _last_log_date
    
    if logger is None:
        # If logger is not initialized, print directly to console
        print(f"[UNINITIALIZED LOGGER] {level}: {message}")
        return
        
    # Check if we need to rotate to a new day's log file
    current_date = datetime.now().date()
    if current_date != _last_log_date:
        # Remove old handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # Setup new logger with new date
        logger = setup_logging()
        _last_log_date = current_date
        
    if no_timestamp:
        # Direct print without using logger
        print(f"{message}")
        sys.stdout.flush()
    else:
        # Use proper logging level
        log_level = getattr(logging, level.upper(), logging.DEBUG)
        log_func = getattr(logger, level.lower(), logger.debug)
        
        try:
            log_func(message)
        except Exception as e:
            # Fallback if logging fails
            print(f"[LOGGING ERROR] {level}: {message} (Error: {str(e)})")
            sys.stdout.flush()

def signal_handler(sig, frame):
    """Handle signals to gracefully stop the agent."""
    global running
    log("Stopping agent...", level='INFO')
    running = False

def create_agent_from_config(config_file: str):
    """
    Create an agent from a configuration file.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Agent: The created agent
    """
    try:
        # Load the configuration file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if "agent_id" not in config:
            config["agent_id"] = str(uuid.uuid4())

        agent_info = AgentInfo.FromJson(config)
        agent = Agent.FromJson(agent_info)
        
        return agent
    except Exception as e:
        log(f"Error creating agent from config: {str(e)}\n{traceback.format_exc()}", level='ERROR')
        traceback.print_exc()
        return None

def list_agent_practices(agent: Agent):
    """
    List all practices of an agent.
    
    Args:
        agent: The agent to list practices for
    """
    #print(agent.pits)
    log(f"\npractices of agent {agent.name}:")
    log("=" * 50, no_timestamp=True)

    for practice_name, practice_func in agent.practices.items():
        log(f"\n  - {practice_name}", no_timestamp=True)
        # if practice_func.__doc__:
        #     log(f"    Description: {practice_func.__doc__.strip()}", no_timestamp=True)

    # loop pits, and list practices of each pit
    # print(f"pits: {agent.pits}")
    for pit_type, pits in agent.pits.items():
        for pit_name, pit in pits.items():
            log(f"\nPit: {pit_name}", no_timestamp=True)
            log("=" * 50, no_timestamp=True)
            for practice_name, practice_func in pit.practices.items():
                log(f"\n  - {practice_name}", no_timestamp=True)
                # if practice_func.__doc__:
                #     log(f"    Description: {practice_func.__doc__.strip()}", no_timestamp=True)


def display_practice_help(agent: Agent, help_arg: str):
    """
    Display help information for a specific pit or practice.
    
    Args:
        agent: The agent to get help for
        help_arg: The pit/practice to get help for (format: pit_name or pit_name/practice_name)
    """
    parts = help_arg.split('/')
    
    if len(parts) == 1:
        # Check if it's an agent practice first
        practice_name = parts[0]
        if hasattr(agent, "practices") and isinstance(agent.practices, dict) and practice_name in agent.practices:
            practice_func = agent.practices[practice_name]
            log(f"\nAgent practice: {practice_name}")
            log("=" * 50)
            
            if practice_func.__doc__:
                log(f"Description: {practice_func.__doc__.strip()}")
            else:
                log("Description: No description available")
            
            # Get function signature
            sig = inspect.signature(practice_func)
            log("\nParameters:")
            log("-" * 30)
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                param_str = f"  - {param_name}"
                if param.default != inspect.Parameter.empty:
                    param_str += f" (default: {param.default})"
                log(param_str)
                
                # Try to get parameter description from docstring
                if practice_func.__doc__:
                    param_desc = None
                    for line in practice_func.__doc__.split('\n'):
                        line = line.strip()
                        if line.startswith(f"{param_name}:"):
                            param_desc = line[len(param_name) + 1:].strip()
                            break
                    
                    if param_desc:
                        log(f"    {param_desc}")
            return
            
        # Only pit name provided, show all practices for this pit
        pit_name = parts[0]
        if pit_name not in agent.pits:
            log(f"Pit '{pit_name}' not found in agent {agent.name}")
            log(f"Available pits: {list(agent.pits.keys())}")
            log(f"Available agent practices: {agent.list_practices() if hasattr(agent, 'list_practices') else []}")
            return
            
        pit = agent.pits[pit_name]
        log(f"\nPit: {pit_name}")
        log("=" * 50)
        log(f"Description: {pit.description}")
        log("\npractices:")
        log("-" * 30)
        
        if hasattr(pit, "practices") and isinstance(pit.practices, dict):
            for practice_name, practice_func in pit.practices.items():
                log(f"\n  - {practice_name}")
                if practice_func.__doc__:
                    log(f"    Description: {practice_func.__doc__.strip()}")
                
                # Get function signature
                sig = inspect.signature(practice_func)
                params = []
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_str = param_name
                    if param.default != inspect.Parameter.empty:
                        param_str += f"={param.default}"
                    params.append(param_str)
                
                if params:
                    log(f"    Parameters: {', '.join(params)}")
                else:
                    log("    Parameters: None")
    
    elif len(parts) == 2:
        # Pit and practice name provided
        pit_name, practice_name = parts
        if pit_name not in agent.pits:
            log(f"Pit '{pit_name}' not found in agent {agent.name}")
            return
            
        pit = agent.pits[pit_name]
        if not hasattr(pit, "practices") or not isinstance(pit.practices, dict):
            log(f"Pit '{pit_name}' has no practices")
            return
            
        if practice_name not in pit.practices:
            log(f"practice '{practice_name}' not found in pit '{pit_name}'")
            return
            
        practice_func = pit.practices[practice_name]
        log(f"\npractice: {pit_name}/{practice_name}")
        log("=" * 50)
        
        if practice_func.__doc__:
            log(f"Description: {practice_func.__doc__.strip()}")
        else:
            log("Description: No description available")
        
        # Get function signature
        sig = inspect.signature(practice_func)
        log("\nParameters:")
        log("-" * 30)
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_str = f"  - {param_name}"
            if param.default != inspect.Parameter.empty:
                param_str += f" (default: {param.default})"
            log(param_str)
            
            # Try to get parameter description from docstring
            if practice_func.__doc__:
                param_desc = None
                for line in practice_func.__doc__.split('\n'):
                    line = line.strip()
                    if line.startswith(f"{param_name}:"):
                        param_desc = line[len(param_name) + 1:].strip()
                        break
                
                if param_desc:
                    log(f"    {param_desc}")
    
    else:
        log("Invalid help format. Use --help-practice pit_name or --help-practice pit_name/practice_name")

def parse_practice_args(args_str: str):
    """
    Parse practice arguments from a string.
    
    Args:
        args_str: Arguments for the practice in Python syntax
        
    Returns:
        tuple: (args, kwargs)
    """
    if not args_str:
        return [], {}
    

    # If the argument is a simple string without quotes, treat it as a single string argument
    try:
        if not args_str.startswith('"') and not args_str.startswith("'") and ',' not in args_str and '=' not in args_str:
            return [args_str], {}
    except Exception as e:
        pass
    
    # Handle quoted strings directly
    try:
        if (args_str.startswith('"') and args_str.endswith('"')) or (args_str.startswith("'") and args_str.endswith("'")):
            # Remove the quotes
            arg = args_str[1:-1]
            return [arg], {}
    except Exception as e:
        pass
    
    # Try to parse using ast.literal_eval
    try:
        import ast
        
        # Add parentheses to make it a tuple
        args_tuple = ast.literal_eval(f"({args_str})")
        
        # Extract args and kwargs
        args = []
        kwargs = {}
        
        for arg in args_tuple:
            if isinstance(arg, tuple) and len(arg) == 2 and isinstance(arg[0], str):
                # This is a kwarg
                kwargs[arg[0]] = arg[1]
            else:
                # This is a positional arg
                args.append(arg)
                
        return args, kwargs
    except Exception as e:
        # If parsing fails, try a simpler approach
        log(f"Warning: Could not parse arguments using AST: {str(e)}")
        
        # Otherwise, split by commas and handle basic types
        args = []
        for arg in args_str.split(','):
            arg = arg.strip()
            if not arg:
                continue
                
            # Try to convert to appropriate type
            if arg.lower() == 'true':
                args.append(True)
            elif arg.lower() == 'false':
                args.append(False)
            elif arg.lower() == 'none':
                args.append(None)
            elif arg.isdigit():
                args.append(int(arg))
            elif arg.replace('.', '', 1).isdigit():
                args.append(float(arg))
            else:
                # Remove quotes if present
                try:
                    if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                        arg = arg[1:-1]
                finally:
                    args.append(arg)
                
        return args, {}

def use_practice(agent: Agent, practice_name: str, *args, **kwargs):
    """
    Use a practice of an agent.
    
    Args:
        agent: The agent to use the practice from
        practice_arg: The practice to use (format: pit_name/practice_name or practice_name)
        *args: Positional arguments for the practice
        **kwargs: Keyword arguments for the practice
        
    Returns:
        Any: The result of the practice
    """
    try:
        log(f"Using practice {practice_name} with args: {args} and kwargs: {kwargs}","DEBUG")
        result = agent.UsePractice(practice_name, *args, **kwargs)
        log(f"Result: {result}")
        return result
    except Exception as e:
        log(f"Error using practice {practice_name}: {str(e)}", level='ERROR')
        traceback.print_exc()
        return None

def refresh_advertisements(agent: Agent, duration: int, interval: int = 10):
    """
    Refresh agent advertisements for a specified duration.
    
    Args:
        agent: The agent to refresh advertisements for
        duration: Duration in seconds to refresh advertisements
        interval: Interval between advertisement refreshes in seconds
        
    Returns:
        The thread running the advertisement refresh
    """
    import threading
    import time
    
    # Find all plazas to advertise on
    plazas = list(agent.plazas.keys())
    if not plazas:
        log(f"Agent {agent.name} has no plazas to advertise on")
        return None
    
    log(f"Starting advertisement refresh for {'indefinite time' if duration <= 0 else duration} seconds with {interval} second intervals on plazas: {plazas}", level='INFO')
    log(f"Plaza details: {[(name, type(plaza).__name__) for name, plaza in agent.plazas.items()]}", level='DEBUG')
    
    # Store the stop event on the agent so it can be accessed later
    agent._refresh_stop_event = threading.Event()
    
    # Create a function to refresh advertisements
    def refresh_ads():
        start_time = time.time()
        end_time = start_time + duration if duration > 0 else float('inf')
        refresh_count = 0
        
        # Continue refreshing until the duration is up or the stop event is set
        while time.time() < end_time and not agent._refresh_stop_event.is_set():
            refresh_count += 1
            log(f"Refresh cycle #{refresh_count} started", level='DEBUG')
            
            # Refresh advertisements on all plazas
            for plaza_name in plazas:
                try:
                    # First check if plaza is still available 
                    if plaza_name not in agent.plazas:
                        log(f"Plaza {plaza_name} no longer available, skipping", level='WARNING')
                        continue
                        
                    # Try different approaches to refresh the advertisement
                    if hasattr(agent, 'Advertise') and callable(agent.Advertise):
                        # Try to call the direct method first
                        agent.Advertise(plaza_name)
                        log(f"Refreshed advertisement on plaza {plaza_name} (direct call)", level='DEBUG')
                    elif "Advertise" in agent.practices:
                        # Fall back to using UsePractice
                        agent.UsePractice("Advertise", plaza_name)
                        log(f"Refreshed advertisement on plaza {plaza_name} (practice call)", level='DEBUG')
                    else:
                        log(f"No Advertise method found for plaza {plaza_name}", level='ERROR')
                        
                    # List all active agents in the plaza using ListActiveAgents practice
                    log(f"Listing active agents in plaza {plaza_name}...\n", level='INFO')
                    try:
                        # Get the plaza object
                        plaza = agent.plazas.get(plaza_name)
                        if plaza and hasattr(plaza, "UsePractice"):
                            # Use the ListActiveAgents practice
                            active_agents = plaza.UsePractice("ListActiveAgents")
                            log(f"Active agents: {active_agents}", level='DEBUG')
                            if active_agents:
                                log(f"Found {len(active_agents)} active agents in plaza {plaza_name}:\n", level='DEBUG')
                                for active_agent in active_agents:
                                    agent_name = active_agent.get('agent_name', 'Unknown')
                                    agent_id = active_agent.get('agent_id', 'Unknown')
                                    log(f"  - Agent: {agent_name} (ID: {agent_id})", level='INFO')
                                log(f"", level='INFO')
                            else:
                                log(f"No active agents found in plaza {plaza_name}", level='INFO')
                        else:
                            log(f"Plaza {plaza_name} does not support ListActiveAgents practice", level='WARNING')
                    except Exception as e:
                        log(f"Error listing active agents in plaza {plaza_name}: {str(e)}", level='ERROR')
                        import traceback
                        traceback.print_exc()
                        
                except Exception as e:
                    log(f"Error refreshing advertisement on plaza {plaza_name}: {str(e)}", level='ERROR')
                    import traceback
                    traceback.print_exc()
            
            # Print a message showing we're still refreshing
            if refresh_count % 5 == 0:  # Log only every 5 cycles to reduce noise
                log(f"Advertisement refresh cycle #{refresh_count} completed. Next refresh in {interval} seconds", level='INFO')
            
            # Wait for the next refresh or until stopped
            agent._refresh_stop_event.wait(interval)
        
        log(f"Completed advertisement refresh after {time.time() - start_time:.1f} seconds, {refresh_count} refreshes", level='INFO')
    
    # Start the refresh thread
    thread = threading.Thread(target=refresh_ads, name="AdvertisementRefreshThread")
    thread.daemon = True
    thread.start()
    
    # Store thread on agent for future reference
    agent._refresh_thread = thread
    
    return thread

def handle_client(client_socket, client_address, agent, stop_event):
    """
    Handle a client connection.
    
    Args:
        client_socket: Client socket
        client_address: Client address
        agent: The agent to control
        stop_event: Event to signal server to stop
    """
    try:
        # Set a timeout for receiving data
        client_socket.settimeout(5)
        
        # Receive the command
        data = client_socket.recv(1024).decode('utf-8').strip()
        log(f"Received command: {data}")
        
        # Process the command
        if data == "StopAgent":
            log("Received StopAgent command from socket")
            # Use the StopAgent practice
            if hasattr(agent, "UsePractice") and callable(agent.UsePractice):
                try:
                    agent.UsePractice("StopAgent")
                    response = "Agent stopping"
                    
                    # Signal any refresh threads to stop
                    if hasattr(agent, "_refresh_stop_event") and agent._refresh_stop_event:
                        agent._refresh_stop_event.set()
                        log("Signaled advertisement refresh to stop")
                except Exception as e:
                    response = f"Error stopping agent: {str(e)}"
            else:
                response = "Agent does not support StopAgent practice"
            
            # Signal the server to stop
            stop_event.set()
        elif data == "status":
            # Get agent status
            response = f"Agent {agent.name} is {'running' if agent.running else 'stopped'}"
        elif data == "info":
            # Get agent info
            response = f"Agent: {agent.name}\n"
            response += f"Description: {agent.description}\n"
            response += f"ID: {agent.agent_id}\n"
            response += f"Running: {agent.running}\n"
            response += f"Pits: {', '.join(agent.pits.keys())}\n"
            response += f"Plazas: {', '.join(agent.plazas.keys())}\n"
        elif data == "practices":
            # Get agent practices
            response = "Agent practices:\n"
            if hasattr(agent, "list_practices") and callable(agent.list_practices):
                practices = agent.list_practices()
                if practices:
                    response += f"  {', '.join(practices)}\n"
            
            # Get pit practices
            for pit_name, pit in agent.pits.items():
                if hasattr(pit, "practices") and isinstance(pit.practices, dict):
                    response += f"\nPit {pit_name} practices:\n"
                    response += f"  {', '.join(pit.practices.keys())}\n"
        elif data == "help":
            # Show available commands
            response = "Available commands:\n"
            response += "  status - Get agent status\n"
            response += "  info - Get agent information\n"
            response += "  practices - List agent practices\n"
            response += "  StopAgent - Stop the agent\n"
            response += "  help - Show this help message\n"
        elif data.startswith("use "):
            # Use a practice
            parts = data.split(" ", 2)
            if len(parts) < 2:
                response = "Invalid use command. Format: use <practice> [args]"
            else:
                practice = parts[1]
                args_str = parts[2] if len(parts) > 2 else None
                
                try:
                    # Parse arguments
                    args, kwargs = parse_practice_args(args_str)
                    
                    # Use the practice
                    if hasattr(agent, "UsePractice") and callable(agent.UsePractice):
                        try:
                            result = agent.UsePractice(practice, *args, **kwargs)
                            response = f"Result: {result}"
                        except Exception as e:
                            response = f"Error using practice {practice}: {str(e)}"
                    else:
                        response = "Agent does not support UsePractice method"
                except Exception as e:
                    response = f"Error parsing arguments: {str(e)}"
        elif data.startswith("refresh "):
            # Refresh advertisements
            parts = data.split(" ")
            if len(parts) < 2:
                response = "Invalid refresh command. Format: refresh <duration> [interval]"
            else:
                try:
                    duration = int(parts[1])
                    interval = int(parts[2]) if len(parts) > 2 else 10
                    
                    # Use the RefreshPractice practice
                    if hasattr(agent, "UsePractice") and callable(agent.UsePractice):
                        try:
                            agent.UsePractice("RefreshPractice", duration, interval)
                            response = f"Started advertisement refresh for {duration} seconds with {interval} second intervals"
                        except Exception as e:
                            response = f"Error refreshing advertisements: {str(e)}"
                    else:
                        response = "Agent does not support RefreshPractice practice"
                except ValueError:
                    response = "Duration and interval must be integers"
        else:
            response = f"Unknown command: {data}\nType 'help' for available commands"
        
        # Send the response
        client_socket.sendall(response.encode('utf-8'))
    except Exception as e:
        log(f"Error handling client {client_address}: {str(e)}", level='ERROR')
    finally:
        # Close the client socket
        client_socket.close()

def list_agent_pits(agent: Agent):
    """
    List all pits of an agent.
    
    Args:
        agent: The agent to list pits for
    """
    log(f"\nPits of agent {agent.name}:")
    log("=" * 50)
    
    for pit_name, pit in agent.pits.items():
        if pit_name not in agent.plugs:  # Skip plugs, they'll be listed separately
            pit_type = pit.__class__.__name__ if hasattr(pit, "__class__") else type(pit)
            log(f"  - {pit_name} ({pit_type})")
            if hasattr(pit, "description"):
                log(f"    Description: {pit.description}")
            if hasattr(pit, "practices") and isinstance(pit.practices, dict):
                log(f"    practices:")
                for practice in pit.practices:
                    log(f"      - {practice}")

def list_agent_plugs(agent: Agent):
    """
    List all plugs of an agent.
    
    Args:
        agent: The agent to list plugs for
    """
    log(f"\nPlugs of agent {agent.name}:")
    log("=" * 50)
    
    for plug_name, plug in agent.plugs.items():
        plug_type = plug.__class__.__name__
        log(f"  - {plug_name} ({plug_type})")
        if hasattr(plug, "description"):
            log(f"    Description: {plug.description}")
        if hasattr(plug, "host") and hasattr(plug, "port"):
            log(f"    Host: {plug.host}")
            log(f"    Port: {plug.port}")
        if hasattr(plug, "is_server"):
            log(f"    Server: {plug.is_server}")
        if hasattr(plug, "is_connected"):
            log(f"    Connected: {plug.is_connected()}")
        if hasattr(plug, "practices") and isinstance(plug.practices, dict):
            log(f"    practices:")
            for practice in plug.practices:
                log(f"      - {practice}")

def list_agent_plazas(agent: Agent):
    """
    List all plazas of an agent.
    
    Args:
        agent: The agent to list plazas for
    """
    log(f"\nPlazas of agent {agent.name}:")
    
    if not agent.plazas:
        log("  No plazas found")
        return
    
    for plaza_name, plaza in agent.plazas.items():
        plaza_type = plaza.__class__.__name__
        log(f"  - {plaza_name} ({plaza_type})")
        if hasattr(plaza, "description"):
            log(f"    Description: {plaza.description}")
        if hasattr(plaza, "running"):
            log(f"    Running: {plaza.running}")
        if hasattr(plaza, "pools") and isinstance(plaza.pools, list):
            log(f"    Pools: {len(plaza.pools)}")
            for pool in plaza.pools:
                log(f"      - {pool.name} ({pool.__class__.__name__})")

def handle_grpc_connection(grpc_plug, client_socket, client_address):
    """
    Handle a new grpc connection.
    
    Args:
        grpc_plug: The grpc plug that received the connection
        client_socket: The client socket
        client_address: The client address
    """
    log(f"New connection to {grpc_plug.name} from {client_address}")
    
    # You can add custom connection handling logic here
    # For example, send a welcome message
    try:
        sender = AgentAddress(agent.agent_id, grpc_plug.name)
        recipients = [AgentAddress(None, None)]
        message = StatusMessage("welcome", f"Welcome to {grpc_plug.name}", sender, recipients)
        #grpc_plug.send_message(message)
        # welcome_message = {
        #     "type": "welcome",
        #     "message": f"Welcome to {grpc_plug.name}",
        #     "timestamp": time.time()
        # }
        
        # # Convert message to JSON
        # message_json = json.dumps(welcome_message)
        # message_bytes = message_json.encode('utf-8')
        
        # # Prefix the message with its length
        # message_length = len(message_bytes)
        # length_prefix = struct.pack('!I', message_length)
        
        # # Send the welcome message
        # client_socket.sendall(length_prefix + message_bytes)
        log(f"Sent welcome message to {client_address}")
    except Exception as e:
        log(f"Error sending welcome message to {client_address}: {str(e)}")

def handle_grpc_message(grpc_plug, message, client_socket=None, client_address=None):
    """
    Handle a grpc message.
    
    Args:
        grpc_plug: The grpc plug that received the message
        message: The received message
        client_socket: The client socket
        client_address: The client address (may be None for client mode)
    """
    try:
        #print(f"Received message via {grpc_plug}: {message}")
        # for response, sender is this agent, recipient is the sender of the request, recipients is the sender of the request
        if isinstance(grpc_plug, str):
            log(f"Received message via {grpc_plug}: {message}")
        else:
            log(f"Received message via {grpc_plug.name}: {message}")
        if isinstance(message, str):
            msg = json.loads(message)
        else:
            msg = message
        if isinstance(msg['content'], str):
            msg['content'] = json.loads(msg['content'])
        if msg["content"]["type"] == "UsePracticeRequest":
            log(f"Received UsePracticeRequest: {msg['content']['body']}")
            sender = AgentAddress(agent.agent_id,  "MainPlaza")
            # if "sender" in msg["content"]:
            #     content=msg["content"]["body"]
            # else:
            #     content=json.loads(msg["content"])
            content = msg["content"]
            recipients = []
            # sender of the request is recipient of the response
            if "sender" in content:
                recipients.append(content["sender"])
            else:
                raise ValueError(f"sender not found in content, content: {content}")
            # pass content["body"]["practice_name"] as practice name, content["body"]["arguments"] as **kwargs
            response = agent.UsePractice(content["body"]["practice_name"], **content["body"]["arguments"])
            if "result" in response:
                result = response["result"]
            else:
                result = response
            print(f"Result: {result}")
            log(f"Result: {result}")
            message = UsePracticeResponse(content["body"]["practice_name"],result,sender,recipients, content["msg_id"])
            print(f"Sending UsePracticeResponse: {message}")
            log(f"Sending UsePracticeResponse: {message}")
            agent.SendMessage(message, recipients)
        elif message["type"] == "StatusMessage":
            log(f"Received StatusMessage: {message['body']}")
            if message["body"]["status"] == "error":
                log(f"Error: {message["body"]["message"]}")
            elif message["body"]["status"] == "success":
                log(f"Success: {message["body"]["message"]}")
        elif message["type"] == "UsePracticeResponse":
            if "body" in message:
                log(f"Received UsePracticeResponse: {message['body']}")
                if message["body"]["status"] == "error":
                    log(f"Error: {message["body"]["message"]}")
                elif message["body"]["status"] == "success":
                    log(f"Success: {message["body"]["message"]}")
            else:
                log(f"Received UsePracticeResponse: {message}")
        elif message["type"] == "Message":
            log(f"Received Message: {message['content']}")
        else:
            log(f"Unknown message type: {message['type']}")
    except Exception as e:
        log(f"Error handling message: {str(e)}\n{traceback.format_exc()}","ERROR")

def display_agent_help(agent: Agent):
    """
    Display help information for the agent.
    
    Args:
        agent: The agent to display help for
    """
    response = f"Agent: {agent.name}\n"
    response += f"Description: {agent.description}\n"
    response += f"ID: {agent.agent_id}\n"
    response += f"Pits: {', '.join(agent.pits.keys())}\n"
    response += f"Plugs: {', '.join(agent.plugs.keys())}\n"
    response += f"Plazas: {', '.join(agent.plazas.keys())}\n"
    response += f"practices: {', '.join(agent.practices.keys())}\n"
    
    log(response)

def handle_log_event(event, verbose_level: str, log_level: str):
    """
    Handle log events from the agent.
    
    Args:
        event: LogEvent object containing log information
        verbose_level: Level for console output (DEBUG, INFO, WARNING, ERROR)
        log_level: Level for file logging (DEBUG, INFO, WARNING, ERROR)
    """
    # Define log levels order for comparison
    level_order = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
    
    # Format the message with component context
    timestamp = event.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    formatted_msg = f"{timestamp} - {event.pit_name} - {event.level} - {event.message}"
    
    # Get numeric levels for comparison
    event_level_num = getattr(logging, event.level, 0) 
    verbose_level_num = getattr(logging, verbose_level.upper(), 0)
    log_level_num = getattr(logging, log_level.upper(), 0)
    
    # Check if we should log to file based on log_level
    if event_level_num >= log_level_num:
        # Pass directly to our file handler instead of using the log function
        # to avoid duplicate logging
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                if handler.level <= event_level_num:
                    record = logging.LogRecord(
                        name=event.pit_name,
                        level=event_level_num,
                        pathname='',
                        lineno=0,
                        msg=event.message,
                        args=(),
                        exc_info=None
                    )
                    handler.emit(record)
    
    # Check if we should print to console based on verbose_level
    if event_level_num >= verbose_level_num:
        if event.level in ['WARNING', 'ERROR']:
            print(f"\033[91m{formatted_msg}\033[0m")  # Red text for warnings and errors
        else:
            print(f"{formatted_msg}")
            
    # Always force flush stdout to ensure messages appear immediately
    sys.stdout.flush()

def main():
    """Main function."""
    # Parse command line arguments
    global running
    global agent
    parser = argparse.ArgumentParser(description="Create and run an agent from a JSON configuration file.")
    parser.add_argument("--config", help="Path to the agent configuration file", required=True)
    parser.add_argument("--list-practices", help="List agent practices", action="store_true")
    parser.add_argument("--list-pits", help="List agent pits", action="store_true")
    parser.add_argument("--list-plugs", help="List agent plugs", action="store_true")
    parser.add_argument("--list-plazas", help="List agent plazas", action="store_true")
    parser.add_argument("--list-all", help="List all agent components", action="store_true")
    parser.add_argument("--refresh", help="Enable automatic advertisement refresh (every 10 seconds by default)", action="store_true", default=False)
    parser.add_argument("--refresh-interval", help="Interval between advertisement refreshes in seconds (default: 10)", type=int, default=10)
    parser.add_argument("--use-practice", help="Use a practice and exit (format: practice_name or pit_name/practice_name)", type=str)
    parser.add_argument("--practice-args", help="Arguments for the practice in Python syntax", type=str, default="{}")
    parser.add_argument("--help-practice", help="Display help for a practice and exit (format: pit_name or pit_name/practice_name)", type=str)
    parser.add_argument("--verbose-level", 
                      help="Set console output verbosity level (DEBUG shows all messages, INFO shows info and above, WARNING shows only warnings and errors, ERROR shows only errors)", 
                      type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='WARNING')
    parser.add_argument("--log-level", 
                      help="Set log file verbosity level (what gets written to the log file)", 
                      type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    
    # redirect stderr to nothing
    #sys.stderr = open(os.devnull, 'w')
    args = parser.parse_args()
    
    # Initialize logging with specified levels
    init_logging(args.verbose_level, args.log_level)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create the agent
    #global agent
    agent = create_agent_from_config(args.config)
    if not agent:
        log("Failed to create agent")
        return 1
    
    # Subscribe to all component log events
    agent.subscribe_to_component_logs(lambda event: handle_log_event(event, args.verbose_level, args.log_level))
    log("Subscribed to all component log events", level='DEBUG')
    
    # Check if we need to display help for a practice
    if args.help_practice:
        display_practice_help(agent, args.help_practice)
        return 0
    
    # Check if we need to use a practice
    if args.use_practice:
        result = use_practice(agent, args.use_practice, args.practice_args)
        print(f"Result: {result}")
        return 0 if result is not None else 1
    
    # List agent practices if requested
    if args.list_practices or args.list_all:
        list_agent_practices(agent)
        if args.list_practices and not args.list_all:
            return 0
    
    # List agent pits if requested
    if args.list_pits or args.list_all:
        list_agent_pits(agent)
        if args.list_pits and not args.list_all:
            return 0
    
    # List agent plugs if requested
    if args.list_plugs or args.list_all:
        list_agent_plugs(agent)
        if args.list_plugs and not args.list_all:
            return 0
    
    # List agent plazas if requested
    if args.list_plazas or args.list_all:
        list_agent_plazas(agent)
        if (args.list_plazas or args.list_all) and not args.list_all:
            sys.exit(0)
            
    # If we're just listing all components, exit now
    if args.list_all:
        return 0
    
    # Start the agent
    log(f"Starting agent {agent.name}...", level='INFO')
    
    # Log grpc plug details before starting
    for plug_name, plug in agent.plugs.items():
        if hasattr(plug, 'is_server'):
            log(f"grpc Plug {plug_name} is_server: {plug.is_server}")
            log(f"grpc Plug {plug_name} host: {plug._host}")
            log(f"grpc Plug {plug_name} port: {plug._port}")
    
    agent.start()
    
    # Explicitly connect grpc plugs
    for plug_name, plug in agent.plugs.items():
        if hasattr(plug, 'connect'):
            try:
                log(f"Explicitly connecting plug {plug_name}...")
                plug.connect()
            except Exception as e:
                log(f"Error connecting plug {plug_name}: {str(e)}")
    
    # Register event handlers for grpc plugs
    for plug_name, plug in agent.plugs.items():
        if hasattr(plug, 'register_event_handler'):
            try:
                log(f"Registering event handlers for plug {plug_name}...")
                plug.register_event_handler('connection', handle_grpc_connection)
                plug.register_event_handler('message', handle_grpc_message)
                log(f"Event handlers registered for plug {plug_name}")
            except Exception as e:
                log(f"Error registering event handlers for plug {plug_name}: {str(e)}")
    
    # Log grpc plug connection status after starting
    for plug_name, plug in agent.plugs.items():
        if hasattr(plug, 'is_connected'):
            log(f"grpc Plug {plug_name} connected: {plug.is_connected()}")
    
    # Start automatic advertisement refresh
    if args.refresh:
        try:
            # Print a clear status message
            log(f"Starting automatic advertisement refresh process...", level='INFO')
            
            # First try a single advertisement cycle to make sure it works
            for plaza_name in agent.plazas.keys():
                try:
                    log(f"Testing advertisement on plaza {plaza_name}...", level='DEBUG')
                    if hasattr(agent, 'Advertise') and callable(agent.Advertise):
                        agent.Advertise(plaza_name)
                    else:
                        agent.UsePractice("Advertise", plaza_name)
                    log(f"✓ Successfully advertised on plaza {plaza_name}", level='DEBUG')
                except Exception as e:
                    log(f"✗ Failed to advertise on plaza {plaza_name}: {str(e)}", level='ERROR')
                    traceback.print_exc()
            
            # Now start the automatic refresh thread
            log(f"Starting continuous refresh thread with interval {args.refresh_interval} seconds...", level='DEBUG')
            refresh_thread = refresh_advertisements(agent, duration=0, interval=args.refresh_interval)
            
            if refresh_thread:
                log(f"✓ Advertisement refresh thread started (name={refresh_thread.name})", level='DEBUG')
                # Verify thread is running
                if refresh_thread.is_alive():
                    log(f"✓ Advertisement refresh thread is running and active", level='DEBUG')
                else:
                    log(f"✗ WARNING: Advertisement refresh thread failed to start!", level='WARNING')
            else:
                log("✗ Failed to start automatic advertisement refresh - no plazas available", level='ERROR')
        except Exception as e:
            log(f"✗ Error starting advertisement refresh: {str(e)}", level='ERROR')
            traceback.print_exc()
    else:
        log("Automatic advertisement refresh disabled")
    
    log(f"Agent {agent.name} started")
    
    # Run the agent in a loop
    global running
    while running:
        try:
            # Sleep for a short time to avoid busy waiting
            time.sleep(0.1)
        except KeyboardInterrupt:
            log("Keyboard interrupt received, stopping agent...", level='INFO')
            traceback.print_exc()
            return True
        except Exception as e:
            log(f"Error running agent: {str(e)}", level='ERROR')
            traceback.print_exc()
            return False
    
    # Stop the agent
    log(f"Stopping agent {agent.name}...", level='INFO')
    
    # Stop the refresh thread if it exists
    if hasattr(agent, '_refresh_stop_event') and agent._refresh_stop_event:
        log("Stopping advertisement refresh thread...", level='DEBUG')
        agent._refresh_stop_event.set()
        if hasattr(agent, '_refresh_thread') and agent._refresh_thread:
            agent._refresh_thread.join(2)  # Wait up to 2 seconds for thread to finish
    
    agent.stop()
    
    log(f"Agent {agent.name} stopped")
    
    return 0

if __name__ == "__main__":
    main()