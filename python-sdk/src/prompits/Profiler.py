# Profiler is a class that profiles the execution of a pathway
# Each PostStep is profiled
# Evaluators are used to evaluate the execution of a PostStep

from abc import ABC, abstractmethod

from prompits.services.Pouch import PathRun
from prompits.Pit import Pit

class Evaluator(ABC):
    """
    Abstract base class for evaluators used in profiling.
    
    An Evaluator compares two values (often expected vs. actual) 
    and produces a similarity or accuracy score. Different evaluator
    implementations handle different data types and comparison methods.
    """
    
    def __init__(self, name: str, description: str, method: str=None) -> None:
        """
        Initialize an Evaluator.
        
        Args:
            name: Name of the evaluator
            description: Description of the evaluator's purpose
            method: Optional default evaluation method if the evaluator
                   supports multiple methods
        """
        self.name = name
        self.description = description
        self.method = method  

    @abstractmethod
    def Evaluate(self, value1, value2, method=None) -> float:
        """
        Evaluate the similarity or accuracy between two values.
        
        This abstract method must be implemented by subclasses to provide
        specific evaluation logic for different types of comparisons.
        
        Args:
            value1: First value (often the expected value)
            value2: Second value (often the actual result)
            method: Optional evaluation method to use, overrides the default
            
        Returns:
            float: A score representing the similarity/accuracy (typically 0.0-1.0)
            
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("Evaluate is not implemented")    

class Profiler(Pit):
    """
    !!! This is a work in progress !!!
    Pit that profiles the execution of pathways.
    
    A Profiler analyzes PathRun objects and evaluates the performance
    and accuracy of each step's execution using various Evaluator instances.
    """
    
    def __init__(self) -> None:
        """
        Initialize a Profiler instance.
        """
        super().__init__("Profiler", "Profiler")
        self.AddPractice("ProfilePathRun", self.ProfilePathRun)

    def ProfilePathRun(self, pathrun: PathRun):
        """
        Profile the execution of a pathway.
        
        Analyzes a PathRun object to evaluate the performance and
        accuracy of each step's execution.
        
        Args:
            pathrun: The PathRun object containing information about
                    the pathway execution
                    
        Raises:
            NotImplementedError: If not implemented by a subclass
        """
        raise NotImplementedError("ProfilePathRun is not implemented")
