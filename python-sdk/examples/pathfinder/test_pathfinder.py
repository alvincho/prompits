# create a Pathway from a json file
# this is a simple example to test the Pathfinder
# the Pathfinder is a stand-alone tool that use agent to find the best way to run a pathway
# it can be used as a standalone tool or as a component of an agent

import os
from prompits.Pathway import Pathway
from prompits.Pathfinder import Pathfinder
from prompits.Agent import Agent, AgentInfo
from prompits.services.Ollama import Ollama

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

    with open('pathfinder_agent.json', 'r') as f:
        json_data = json.load(f)
    
    agent_info = AgentInfo.FromJson(json_data)
    agent = Agent.FromJson(agent_info)
    
    # Start the gRPC server component
    if 'plugs' in agent.pits and 'grpc_server' in agent.pits['plugs']:
        agent.pits['plugs']['grpc_server'].start()
    
    # Subscribe to log events
    agent.subscribe_to_component_logs(log_handler)
    

    print("In Prompits, agent has capability(practice) and advertise it on a plaza")
    print("The pathfinder will find the best way to run each post")
    print("This example is use a Pathfinder to find the best way to run a pathway")
    print("\nThe pathway has two steps(posts):")
    print("1. Send prompt to an LLM agent and return the response")
    print("2. Translate the response of the first post to Chinese")
    
    #print(agent.UsePractice("MainPlaza/ListActiveAgents"))
    # Create Pathfinder
    pathfinder = Pathfinder(agent)
    pathfinder.subscribe_to_logs(log_handler)
    
    # Load pathway
    with open('pathway_demo.json', 'r') as f:
        json_data = json.load(f)
    pathway = Pathway.FromJson(json_data)
    
    # Run the pathway
    input_vars = {"prompt": "What is the capital of France?"}
    result = pathfinder.Run(pathway, **input_vars)
    
    print(f"\nPathway Result: {result}")

if __name__ == "__main__":
    main()