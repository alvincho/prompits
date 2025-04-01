"""
Prompits package initialization.

This module initializes the Prompits package and imports all the necessary modules.
"""

# Import core components
from .Pit import Pit
from .AgentAddress import AgentAddress
from .Agent import Agent, AgentInfo
from .plazas.AgentPlaza import AgentPlaza
# Remove non-existent module
# from .Advertisement import Advertisement
from .Plug import Plug
from .Pool import Pool, MemoryPool
from .Message import Message
from .Schema import Schema, TableSchema, DataType
from .Plaza import Plaza
from .Practice import Practice
from .messages.StatusMessage import StatusMessage
from .messages.UsePracticeMessage import UsePracticeResponse

# Import specific implementations
from .pools.PostgresPool import PostgresPool
from .pools.DatabasePool import DatabasePool

# Import plugs
from .plugs.HTTPPlug import HTTPPlug
from .plugs.TCPPlug import TCPPlug

__all__ = [
    'Pit',
    'AgentAddress',
    'Agent',
    'AgentInfo',
    'Practice',
    # 'Advertisement',
    'Plug',
    'HTTPPlug',
    'TCPPlug',
    'Pool',
    'MemoryPool',
    'PostgresPool',
    'DatabasePool',
    'Message',
    'Schema',
    'TableSchema',
    'DataType',
    'Plaza',
    'AgentPlaza',
    'StatusMessage',
    'UsePracticeResponse'
]

# Instead, provide a function to get the classes
def get_class(class_name):
    """
    Get a class by name.
    
    Args:
        class_name: Name of the class to get
        
    Returns:
        The class, or None if not found
    """
    import importlib
    
    # Map of class names to module paths
    class_map = {
        "TCPPlug": "prompits.plugs.TCPPlug",
        "HTTPPlug": "prompits.plugs.HTTPPlug",
        "PostgresPool": "prompits.pools.PostgresPool",
        "AgentPlaza": "prompits.plazas.AgentPlaza",
        # Add more classes as needed
    }
    
    if class_name in class_map:
        try:
            module_path = class_map[class_name]
            module_name, class_name = module_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(f"Error importing {class_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    return None

