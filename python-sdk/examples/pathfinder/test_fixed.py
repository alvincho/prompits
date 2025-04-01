from prompits.Pathway import Pathway, Post
from prompits.Pathfinder import Pathfinder
from prompits.Agent import Agent, AgentInfo
from prompits.LogEvent import LogEvent
from prompits.services.Ollama import Ollama
from prompits.Practice import Practice
import json
import argparse
import logging
import sys
import types
import traceback
import time

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

# Define a mock Chat function that doesn't need the actual Ollama server
def mock_chat(self, prompt, model=None, full_response=False):
    """Mock implementation of Chat that doesn't require an Ollama server"""
    self.log(f"Mock Chat called with prompt: {prompt}", "INFO")
    # Return a mock response with practice info for debugging
    response = {
        "result": {
            "complete_text": f"This is a mock response to: {prompt}",
            "from_practice": "Chat"
        }
    }
    return response

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test Pathfinder with configurable verbosity")
    parser.add_argument("--verbose-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='DEBUG', help="Set verbosity level")
    args = parser.parse_args()
    
    # Completely disable standard logging and use only our custom handler
    logger = disable_standard_logging()
    logger.setLevel(getattr(logging, args.verbose_level.upper()))
    print(f"Log level set to: {args.verbose_level}")
    
    # Load agent from JSON
    with open('pathfinder_agent.json', 'r') as f:
        json_data = json.load(f)
    
    agent_info = AgentInfo.FromJson(json_data)
    agent = Agent.FromJson(agent_info)
    
    # Create and add Ollama service with Chat practice
    print("Creating Ollama service for testing...")
    ollama = Ollama("ollama", "Ollama LLM service", default_model="llama3")
    
    # Replace Chat method with our mock
    ollama.Chat = types.MethodType(mock_chat, ollama)
    print("Replaced Ollama.Chat with mock implementation")
    
    # Print Ollama practices to verify Chat is there
    print(f"Ollama practices: {list(ollama.practices.keys())}")
    
    # Explicitly add the Chat practice again to ensure it's there
    if "Chat" not in ollama.practices:
        print("Adding Chat practice to Ollama")
        ollama.AddPractice(Practice("Chat", ollama.Chat))
    
    # Add to agent's pits
    if not hasattr(agent, "pits"):
        agent.pits = {}
    
    if not hasattr(agent.pits, "services"):
        agent.pits["services"] = {}
    
    agent.pits["services"]["ollama"] = ollama
    
    # Debug: List all of agent's practices
    print("\nDEBUG: Agent practices:")
    all_practices = list(agent.practices.keys())
    print(f"Total practices: {len(all_practices)}")
    print(f"Practices: {all_practices}")
    
    # Explicitly register the Chat practice with the agent
    print("Explicitly adding ollama/Chat practice to agent:")
    agent.AddPractice(Practice("ollama/Chat", ollama.Chat))
    print(f"Added practice ollama/Chat to agent {agent.name}")
    
    # Also add plain "Chat" practice to agent (without prefix)
    agent.AddPractice(Practice("Chat", ollama.Chat))
    print(f"Added practice Chat to agent {agent.name}")
    
    # Debug: List all practices again
    print("\nDEBUG: Updated agent practices:")
    all_practices = list(agent.practices.keys())
    print(f"Total practices: {len(all_practices)}")
    print(f"Practices: {all_practices}")
    
    # Define a log handler
    def log_handler(event):
        handle_log_event(event, args.verbose_level)
    
    # Subscribe to log events
    agent.subscribe_to_component_logs(log_handler)
    
    # Create Pathfinder
    print("\nCreating Pathfinder and connecting to agent...")
    pathfinder = Pathfinder(agent)
    
    # Override Pathfinder._find_agent_practice to find local practices
    original_find_agent_practice = pathfinder._find_agent_practice
    
    def patched_find_agent_practice(self, practice: str):
        # First check if the agent has the practice directly 
        if practice in agent.practices:
            print(f"Found practice {practice} directly in agent")
            # Return agent_address but use the same format for the practice
            return {"agent_address": "local", "practice": practice}
        
        # If not found directly, try the original method
        result = original_find_agent_practice(practice)
        return result
        
    pathfinder._find_agent_practice = types.MethodType(patched_find_agent_practice, pathfinder)
    
    # Also patch run_post to use UsePractice instead of UsePracticeRemote
    original_run_post = pathfinder.run_post
    
    def patched_run_post(self, pathway, post, variables):
        """Modified run_post that handles local practices"""
        self.log(f"Starting post execution: {post.name}", 'INFO')
        start_time = time.time()
        
        try:
            # Find suitable agent for this practice
            self.log(f"Finding agent for practice: {post.practice}", 'DEBUG')
            agent_info = self._find_agent_practice(post.practice)
            
            # Process parameters and prepare practice input
            variables_copy = variables.copy()  # Create a copy to avoid modifying the original
            
            if agent_info:
                self.log(f"Found agent for practice {post.practice}: {agent_info}", 'DEBUG')
                # Prepare practice input by processing parameters
                practice_input = {}
                for key, value in post.parameters.items():
                    practice_input[key] = value
                
                self.log(f"Calling practice {agent_info['practice']} with inputs: {practice_input}", 'DEBUG')
                
                # For local practices
                if agent_info['agent_address'] == "local":
                    response = agent.UsePractice(agent_info['practice'], **practice_input)
                    self.log(f"Local practice {agent_info['practice']} returned: {response}", 'DEBUG')
                else:
                    # This would be UsePracticeRemote for remote practices
                    self.log(f"Would use UsePracticeRemote for {agent_info['practice']} on {agent_info['agent_address']}", 'DEBUG')
                    response = agent.UsePractice(agent_info['practice'], **practice_input)
                
                # Process outputs and update variables
                if 'result' in response:
                    variables_copy.update(response['result'])
                    self.log(f"Updated variables with result: {response['result']}", 'DEBUG')
                else:
                    self.log(f"Warning: No 'result' field in response: {response}", 'WARNING')
                
                self.log(f"Post {post.name} completed successfully", 'INFO')
                return variables_copy
            else:
                error_msg = f"No agent found for practice {post.practice}"
                self.log(error_msg, 'WARNING')
                return variables
                
        except Exception as e:
            error_msg = f"Error in patched post execution: {str(e)}\n{traceback.format_exc()}"
            self.log(error_msg, 'ERROR')
            raise
        finally:
            duration = time.time() - start_time
            self.log(f"Post execution took {duration:.4f} seconds", 'DEBUG')
    
    # Replace the method
    pathfinder.run_post = types.MethodType(patched_run_post, pathfinder)
    
    # Subscribe to Pathfinder log events
    print("Subscribing to Pathfinder log events...")
    pathfinder.subscribe_to_logs(log_handler)
    
    # First test: Direct call to Ollama.Chat
    print("\nDirect test: Calling Ollama.Chat directly...")
    chat_result = ollama.Chat("What is the capital of France?")
    print(f"Chat result: {chat_result}")
    
    # Create simple pathway with Chat practice
    print("\nCreating pathway with Chat practice...")
    entrance_post = Post(
        post_id="post_1",
        name="Preprocess Input",
        practice="Chat",
        parameters={"prompt": "What is the capital of France?"}
    )
    
    pathway = Pathway(
        pathway_id="test_pathway",
        name="Test Pathway",
        entrance_post=entrance_post,
        exit_posts=["post_1"],
        posts=[],
        description="Simple test pathway"
    )
    
    # Run the pathway
    print("\nRunning the pathway...")
    result = pathfinder.Run(pathway, {"prompt": "What is the capital of France?"})
    
    print(f"\nPathway Result: {result}")

if __name__ == "__main__":
    main() 