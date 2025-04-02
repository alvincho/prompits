# PathwayEvaluator is a class that evaluates the similarity between two values use a Pathway
 

from prompits import Pathway
from prompits.Profiler import Evaluator
from prompits.Pathfinder import Pathfinder

class PathwayEvaluator(Evaluator):
    """
    Evaluator that uses a Pathway to compute the similarity between two values.
    
    This evaluator delegates the evaluation to a Pathfinder instance, which
    executes a specified Pathway to determine the similarity or difference
    between two values.
    """
    
    def __init__(self, pathfinder: Pathfinder, pathway: Pathway) -> None:
        """
        Initialize a PathwayEvaluator.
        
        Args:
            pathfinder: The Pathfinder instance to use for pathway execution
            pathway: The Pathway to use for evaluation
        """
        super().__init__("PathwayEvaluator", "PathwayEvaluator")
        self.pathfinder = pathfinder
        self.pathway = pathway

    def Evaluate(self, value1, value2) -> float:
        """
        Evaluate the similarity between two values using a Pathway.
        
        Args:
            value1: First value to compare
            value2: Second value to compare
            
        Returns:
            float: Similarity score as determined by the pathway
        """
        return self.pathfinder.evaluate_pathway(self.pathway, value1, value2)