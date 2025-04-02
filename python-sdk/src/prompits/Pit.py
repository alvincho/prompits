# Pit is the basic element of a multi-agent system.
# It provides a way to store and retrieve information.
# An agent can contain multiple pits.
# A pit has a list of practices.
# practices are the actions that a pit can perform.
# practice associated with a function.
# Other pits can use the practices though a function UsePractice()
# Pit is an abstract class.
# Pit can be described as a JSON object ToJson()
# Pit can be initialized from a JSON object __init__(json)
# Sample JSON:
# {
#     "name": "Pit1",
#     "description": "Pit1 description"
# }

from abc import ABC, abstractmethod
import traceback
from typing import Dict, Any, List, Optional, Callable
import inspect  
import logging
from datetime import datetime
from .Practice import Practice
from .LogEvent import LogEvent

# Setup logging
logger = logging.getLogger('prompits')
logger.setLevel(logging.DEBUG)

# Create console handler if it doesn't exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class Pit(ABC):
    """
    Abstract base class for all Pit components in the Prompits framework.
    
    A Pit is the basic element of a multi-agent system. It provides a way to 
    store and retrieve information. An agent can contain multiple pits, and 
    each pit has a list of practices (actions) that it can perform.
    
    Other pits can use these practices through the UsePractice() method.
    Pits can be serialized to and from JSON format.
    """
    
    def __init__(self, name, description):
        """
        Initialize a Pit with a name and description.
        
        Args:
            name: The name of the pit
            description: A description of the pit's purpose and functionality
        """
        self.name = name
        self.description = description
        self.practices = {}
        self.logger = logging.getLogger(f'prompits.Pit.{self.name}')
        self.log_subscribers = []
        
        # Add standard practices
        practice = Practice("ListPractices", self.ListPractices)
        self.log(f"Adding practice: {practice}", 'DEBUG')
        self.AddPractice(practice)
        practice = Practice("PracticeInfo", self.PracticeInfo)
        self.AddPractice(practice)

    def subscribe_to_logs(self, callback: Callable[[LogEvent], None]):
        """
        Subscribe to log events.
        
        This method adds a callback function that will be called whenever
        a log event occurs in this Pit.
        
        Args:
            callback: The callback function to be called with a LogEvent
        """
        if callback not in self.log_subscribers:
            self.log_subscribers.append(callback)
            # Test the subscription with a test event
            # test_event = LogEvent(self.name, 'DEBUG', f"Subscription test for {callback}")
            # try:
            #     callback(test_event)
            # except Exception as e:
            #     pass
        
    def emit_log_event(self, message: str, level: str = 'INFO'):
        """
        Create and emit a log event directly to all subscribers.
        
        This method ensures that a log event is created and all subscribers
        are notified, without relying on the normal logging mechanism.
        
        Args:
            message: The message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        # Create the event
        event = LogEvent(self.name, level, message)
        
        # Send to all subscribers
        for subscriber in self.log_subscribers:
            try:
                subscriber(event)
            except Exception:
                pass
                
    def log(self, message: str, level: str = 'INFO'):
        """
        Log a message with the pit's prefix and trigger log event.
        
        Args:
            message: The message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        try:
            # Regular logging
            log_func = getattr(self.logger, level.lower(), self.logger.info)
            log_func(f"[{self.name}] {message}")
            
            # Also use the direct event emission method to ensure subscribers are notified
            self.emit_log_event(message, level)
        except Exception as e:
            # Fallback if logging fails
            print(f"[{self.name}] {level}: {message} (Logging error: {str(e)})")
            # Try to emit event anyway
            try:
                self.emit_log_event(message, level)
            except:
                pass

    def unsubscribe_from_logs(self, callback: Callable[[LogEvent], None]):
        """
        Unsubscribe from log events.
        
        This method removes a callback function from the list of subscribers.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self.log_subscribers:
            self.log_subscribers.remove(callback)

    def UsePractice(self, practice_name, *args, **kwargs):
        """
        Call the practice function with the arguments.
        
        Args:
            practice_name: Name of the practice to use
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Any: Result of the practice
        """
        # Direct print statements that will show up regardless of logging config
        #print(f"**** DIRECT PRINT: {self.name}.UsePractice({practice_name}) STARTED ****")
        
        # Log the practice start using our direct event emission
        #self.log(f"Using practice {practice_name} with args {args} and kwargs {kwargs}", 'DEBUG')
        
        if practice_name in self.practices:
            try:
                # Get the practice
                practice = self.practices[practice_name]
                
                # Add our subscribers to the practice
                for sub in self.log_subscribers:
                    if hasattr(practice, 'subscribe_to_logs'):
                        if sub not in practice.log_subscribers:
                            practice.subscribe_to_logs(sub)
                
                # Call the practice
                result = practice.Use(*args, **kwargs)
                
                # Log the completion using direct event emission
                #self.log(f"Practice {practice_name} completed successfully, result: {result}", 'DEBUG')
                
                # Direct print for completion
                #print(f"**** DIRECT PRINT: {self.name}.UsePractice({practice_name}) COMPLETED ****")
                #print(f"**** Result: {result}")
                
                return result
            except Exception as e:
                # Log the error using direct event emission
                error_msg = f"Error in practice {practice_name}: {str(e)}\n{traceback.format_exc()}"
                self.emit_log_event(error_msg, 'ERROR')
                
                # Direct print for error
                #print(f"**** DIRECT PRINT: {self.name}.UsePractice({practice_name}) ERROR: {str(e)} ****")
                
                raise
        else:
            # Log the not found error using direct event emission
            error_msg = f"Practice {practice_name} not found"
            self.emit_log_event(error_msg, 'ERROR')
            
            # Direct print for not found
            #print(f"**** DIRECT PRINT: {self.name}.UsePractice({practice_name}) NOT FOUND ****")
            
            raise ValueError(error_msg)

    def AddPractice(self, practice: Practice):
        """
        Add a practice to the pit.
        
        Args:
            practice: Practice object to add
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            #print(f"**** DIRECT PRINT: {self.name}.AddPractice({practice.name}) STARTED ****")
            self.practices[practice.name] = practice
            self.log(f"Added practice {practice.name}", 'DEBUG')
            #print(f"**** DIRECT PRINT: {self.name}.AddPractice({practice.name}) COMPLETED ****")
            return True
        except Exception as e:
            self.log(f"Error adding practice {practice.name}: {str(e)}", 'ERROR')
            return False

    def ListPractices(self, name_only=False):
        """
        List all practices of the pit.
        
        Args:
            name_only: If True, return only practice names
            
        Returns:
            Union[List[str], Dict[str, Dict]]: List of practice names or dict of practice info
        """
        try:
            if name_only:
                practices = list(self.practices.keys())
            else:
                practices = {practice: self.practices[practice].ToJson() for practice in self.practices.keys()}
            
            self.log(f"Listed {len(self.practices)} practices", 'DEBUG')
            return practices
        except Exception as e:
            self.log(f"Error listing practices: {str(e)}", 'ERROR')
            raise

    def PracticeInfo(self, practice: str):
        """
        Get information about a specific practice.
        
        Args:
            practice: Name of the practice
            
        Returns:
            dict: Information about the practice
        """
        try:
            if practice not in self.practices:
                self.log(f"Practice {practice} not found", 'ERROR')
                raise ValueError(f"practice {practice} not found")
            
            practice_func = self.practices[practice]
            
            if isinstance(practice_func, Callable):
                signature = str(inspect.signature(practice_func))
                docstring = practice_func.__doc__ or "No documentation available"
            else:
                signature = "No signature available"
                docstring = "No documentation available"
            
            info = {
                "name": practice,
                "description": self.practices[practice].description,
                "input_schema": self.practices[practice].input_schema,
                "signature": signature,
                "docstring": docstring,
                "callable": callable(practice_func)
            }
            
            self.log(f"Retrieved info for practice {practice}", 'DEBUG')
            return info
        except Exception as e:
            self.log(f"Error getting practice info for {practice}: {str(e)}", 'ERROR')
            raise

    def ToJson(self):
        """Convert pit to JSON representation.
        
        Returns:
            dict: JSON object
        """
        try:
            json_data = {
                "name": self.name,
                "description": self.description,
                "type": self.__class__.__name__
            }
            
            # Add practices
            if hasattr(self, "practices") and self.practices:
                json_data["practices"] = {}
                for name, practice in self.practices.items():
                    if hasattr(practice, "ToJson"):
                        json_data["practices"][name] = practice.ToJson()
                    else:
                        json_data["practices"][name] = {
                            "name": practice.name,
                            "description": practice.description
                        }
            
            # Log success using logger's methods directly rather than through self.log
            if hasattr(self, "logger") and self.logger is not None:
                self.logger.debug(f"[{self.name}] Converted pit to JSON")
                
            return json_data
        except Exception as e:
            # Log error using logger's methods directly
            if hasattr(self, "logger") and self.logger is not None:
                self.logger.error(f"[{self.name}] Error converting pit to JSON: {str(e)}")
            raise

    @abstractmethod
    def FromJson(self, json):
        """Initialize pit from JSON representation."""
        self.log("FromJson is not implemented", 'ERROR')
        raise NotImplementedError("FromJson is not implemented")
