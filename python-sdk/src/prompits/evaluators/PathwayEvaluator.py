# PathwayEvaluator is a class that evaluates the similarity between two values use a Pathway
 

from prompits import Pathway
from prompits.Profiler import Evaluator
from prompits.Pathfinder import Pathfinder
class PathwayEvaluator(Evaluator):
    def __init__(self, pathfinder: Pathfinder, pathway: Pathway) -> None:
        super().__init__("PathwayEvaluator", "PathwayEvaluator")
        self.pathfinder = pathfinder
        self.pathway = pathway

    def Evaluate(self, value1, value2) -> float:
        return self.pathfinder.evaluate_pathway(self.pathway, answer, result)