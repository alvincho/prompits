# NumericDifference is a class that evaluates the numeric Difference between two values

from enum import Enum
from prompits.services.Pouch import Pit
from prompits.Profiler import Evaluator

class NumericDifferenceMethod(Enum):
    """
    Enumeration of different methods to calculate numeric differences.
    
    Each method provides a different approach to measuring the difference
    between two numeric values.
    """
    ABSOLUTE_DIFFERENCE = "absolute_difference"
    RELATIVE_DIFFERENCE = "relative_difference"
    PERCENTAGE_DIFFERENCE = "percentage_difference"
    RATIO = "ratio"
    LOGARITHMIC_DIFFERENCE = "logarithmic_difference"

class NumericDifference(Evaluator):
    """
    Evaluator that calculates the difference between two numeric values.
    
    This class provides multiple methods for comparing numeric values,
    including absolute, relative, and percentage differences.
    """
    
    def __init__(self, method: NumericDifferenceMethod=NumericDifferenceMethod.ABSOLUTE_DIFFERENCE) -> None:
        """
        Initialize a NumericDifference evaluator.
        
        Args:
            method: The method to use for calculating differences,
                   defaulting to absolute difference
        """
        super().__init__("NumericDifference", "NumericDifference", method)

    def Evaluate(self, value1, value2, method: NumericDifferenceMethod=None) -> float:
        """
        Evaluate the difference between two numeric values.
        
        Args:
            value1: First numeric value
            value2: Second numeric value
            method: Optional method override for this specific evaluation
            
        Returns:
            float: The calculated difference according to the specified method
            
        Raises:
            ValueError: If an invalid method is specified
        """
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
        """
        Calculate the absolute difference between two values.
        
        Returns:
            float: |value1 - value2|
        """
        return abs(value1 - value2)

    def relative_difference(self, value1, value2) -> float:
        """
        Calculate the relative difference between two values.
        
        Returns:
            float: |value1 - value2| / value2
        """
        return abs(value1 - value2) / value2

    def percentage_difference(self, value1, value2) -> float:
        """
        Calculate the percentage difference between two values.
        
        Returns:
            float: |value1 - value2| / value2 * 100
        """
        return abs(value1 - value2) / value2 * 100

