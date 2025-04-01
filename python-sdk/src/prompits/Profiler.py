# Profiler is a class that profiles the execution of a pathway
# Each PostStep is profiled
# Evaluators are used to evaluate the execution of a PostStep

from abc import ABC, abstractmethod

from prompits.services.Pouch import PathRun

class Evaluator(ABC):
    def __init__(self, name: str, description: str, method: str=None) -> None:
        self.name = name
        self.description = description
        self.method = method  

    @abstractmethod
    def Evaluate(self, value1, value2, method=None) -> float:
        raise NotImplementedError("Evaluate is not implemented")    

class Profiler(Pit):
    def __init__(self) -> None:
        super().__init__("Profiler", "Profiler")
        self.AddPractice("ProfilePathRun", self.ProfilePathRun)

    def ProfilePathRun(self, pathrun: PathRun):
        raise NotImplementedError("ProfilePathRun is not implemented")
