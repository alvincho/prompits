# test mcp client

import os
from prompits.Agent import Agent, AgentInfo


import json
import argparse
import logging

def disable_standard_logging():
    """Disable standard Python logging to prevent duplicate messages"""
    # Remove any existing handlers from the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add a null handler to prevent "No handlers found" warnings
    null_handler = logging.NullHandler()
    root_logger.addHandler(null_handler)
    
    # Set the prompits logger level according to command line args
    # but redirect output to the null handler
    prompits_logger = logging.getLogger('prompits')
    for handler in prompits_logger.handlers[:]:
        prompits_logger.removeHandler(handler)
    prompits_logger.addHandler(null_handler)
    
    return prompits_logger

def handle_log_event(event, verbose_level='INFO'):
    """Handle log events from the agent"""
    # Define log levels and their order
    log_levels = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
    
    # Get the numeric value of the event's level and the verbose level
    event_level_value = log_levels.get(event.level, 0)
    verbose_level_value = log_levels.get(verbose_level, 1)  # Default to INFO
    
    # Only display log events at or above the specified verbose level
    if event_level_value >= verbose_level_value:
        # Format the message with timestamp and source
        timestamp = event.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        formatted_msg = f"{timestamp} - {event.pit_name} - {event.level} - {event.message}"
        
        # print the message with color for warnings and errors
        if event.level in ['WARNING', 'ERROR']:
            print(f"\033[91m{formatted_msg}\033[0m")  # Red text 
        else:
            print(formatted_msg)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Pathfinder with configurable verbosity")
    parser.add_argument("--verbose-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help="Set verbosity level")
    args = parser.parse_args()
    
    # Completely disable standard logging and use only our custom handler
    logger = disable_standard_logging()
    logger.setLevel(getattr(logging, args.verbose_level.upper()))
    print(f"Log level set to: {args.verbose_level}")
    
    # Load agent from JSON
    
    def log_handler(event):
        handle_log_event(event, args.verbose_level)

    ## Modify start here below

    with open('mcp_client_agent.json', 'r') as f:
        json_data = json.load(f)
    
    agent_info = AgentInfo.FromJson(json_data)
    agent = Agent.FromJson(agent_info)
    
    # Start the gRPC server component
    if 'plugs' in agent.pits and 'grpc_server' in agent.pits['plugs']:
        agent.pits['plugs']['grpc_server'].start()
    
    # Subscribe to log events
    agent.subscribe_to_component_logs(log_handler)
    
    # Create MCPClient
    arguments = {"tool_name":"list_directory","arguments":{"path":"/Users/alvincho/Downloads/temp"}}
    result = agent.UsePracticeRemote("filesystem/list_directory","Agent1@MainPlaza",arguments )
    print(f"\nResult: {result}")
    content=json.loads(result[0]["content"])
    files = content["body"]["result"]["content"][0]
    print(f"File: {files["text"]}")

if __name__ == "__main__":
    main()