# Practice is not a Pit
# contains a function can be used by other agents

import asyncio
import inspect
import traceback
from typing import Any, Callable, Dict, Optional
from .LogEvent import LogEvent
import logging


class Practice:
    """Class representing a practice that can be performed by a pit."""
    
    def __init__(self, name: str, function: Callable, description: str = "", input_schema: Optional[Dict] = None, is_async: bool = False,parameters: Optional[Dict] = None):
        """
        Initialize a Practice.
        
        Args:
            name: Name of the practice
            function: Function to call when using the practice
            description: Description of what the practice does
            input_schema: Schema describing the expected input format
        """
        self.name = name
        self.function = function
        self.description = description
        self.is_async = is_async
        self.parameters = parameters
        #print(f"Practice init parameters: {name}\ninput_schema: {input_schema}\nparameters: {parameters}\n")
        if input_schema is None:
            # generate input schema from function signature
            sig = inspect.signature(function)   
            self.input_schema = {}
            for param in sig.parameters.values():
                if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    self.input_schema[param.name] = str(param.annotation)
        else:
            self.input_schema = input_schema
        #print(f"Practice init: {self.name}\nself.input_schema: {self.input_schema}\nself.parameters: {self.parameters}\n")
        self.logger = logging.getLogger(f"prompits.Practice.{name}")
        self.log_subscribers = []

    def subscribe_to_logs(self, callback: Callable[[LogEvent], None]) -> None:
        """Subscribe to log events."""
        self.log_subscribers.append(callback)

    def unsubscribe_from_logs(self, callback: Callable[[LogEvent], None]) -> None:
        """Unsubscribe from log events."""
        if callback in self.log_subscribers:
            self.log_subscribers.remove(callback)

    def log(self, message: str, level: str = 'INFO') -> None:
        """Log a message and trigger log events."""
        # Create the event
        event = LogEvent(self.name, level, message)
        
        # Notify all subscribers
        for subscriber in self.log_subscribers:
            try:
                subscriber(event)
            except Exception as e:
                self.logger.error(f"Error in log subscriber: {e}")

    def Use(self, *args, **kwargs) -> Any:
        """Execute the practice with given arguments."""
        # TODO: Add a timeout to the practice
        # TODO: Add a retry mechanism to the practice
        # TODO: Add async support to the practice
        try:
            # Log start
            #start_msg = f"Using practice {self.name} with args: {args} and kwargs: {kwargs}"
            #self.log(start_msg, 'DEBUG')
            if self.is_async:
                result = asyncio.run(self.function(*args, **kwargs))
            else:
                result = self.function(*args, **kwargs)
            
            # Log completion
            complete_msg = f"Practice {self.name} completed successfully"
            self.log(complete_msg, 'DEBUG')
            
            return result
        except Exception as e:
            # Log error
            error_msg = f"Error in practice {self.name}: {e}\n{traceback.format_exc()}"
            self.log(error_msg, 'ERROR')
            
            raise

    def Info(self) -> Dict:
        """Get information about the practice."""
        try:
            self.log("Getting practice info", 'DEBUG')
            info = self.ToJson()
            self.log(f"Practice info retrieved: {info}", 'DEBUG')
            return info
        except Exception as e:
            self.log(f"Error getting practice info: {e}", 'ERROR')
            raise

    def ToJson(self) -> Dict:
        """Convert practice to JSON representation."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "parameters": self.parameters,
            "is_async": self.is_async
        }
        
    
    def FromJson(self, json):
        """
        Initialize this Practice instance from a JSON dictionary.
        
        Args:
            json: Dictionary containing the serialized Practice data
            
        Returns:
            Practice: Self reference for method chaining
        """
        self.name = json["name"]
        self.description = json["description"] 
        self.function = json["function"]
        self.args = json["args"]
        return self
