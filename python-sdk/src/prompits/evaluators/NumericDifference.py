# NumericDifference is a class that evaluates the numeric Difference between two values

from prompits.services.Pouch import Pit
from prompits.Profiler import Evaluator

class NumericDifferenceMethod(Enum):
    ABSOLUTE_DIFFERENCE = "absolute_difference"
    RELATIVE_DIFFERENCE = "relative_difference"
    PERCENTAGE_DIFFERENCE = "percentage_difference"
    RATIO = "ratio"
    LOGARITHMIC_DIFFERENCE = "logarithmic_difference"

class NumericDifference(Evaluator):
    def __init__(self, method: NumericDifferenceMethod=NumericDifferenceMethod.ABSOLUTE_DIFFERENCE) -> None:
        super().__init__("NumericDifference", "NumericDifference", method)

    def Evaluate(self, value1, value2, method: NumericDifferenceMethod=None) -> float:
        if method is None:
            method = self.method

        if method == NumericDifferenceMethod.ABSOLUTE_DIFFERENCE:
            return self.absolute_difference(value1, value2)
        elif method == NumericDifferenceMethod.RELATIVE_DIFFERENCE:
            return self.relative_difference(value1, value2)
        elif method == NumericDifferenceMethod.PERCENTAGE_DIFFERENCE:
            return self.percentage_difference(value1, value2)
        elif method == NumericDifferenceMethod.RATIO:
            return self.ratio(value1, value2)
        elif method == NumericDifferenceMethod.LOGARITHMIC_DIFFERENCE:
            return self.logarithmic_difference(value1, value2)
        else:
            raise ValueError(f"Invalid method: {method}")

    def absolute_difference(self, value1, value2) -> float:
        return abs(value1 - value2)

    def relative_difference(self, value1, value2) -> float:
        return abs(value1 - value2) / value2

    def percentage_difference(self, value1, value2) -> float:
        return abs(value1 - value2) / value2 * 100

