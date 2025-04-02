# StringSimilarity is a class that evaluates a string
# It is used to evaluate the execution of a PostStep
# when comparing strings, we can use the Levenshtein distance
# to evaluate the similarity between the value1 and the value2
# or we can use the Jaccard similarity coefficient
# 

from prompits.Profiler import Evaluator
from enum import Enum
from fuzzywuzzy import fuzz

class StringSimilarityMethod(Enum):
    """
    Enumeration of different methods to calculate string similarity.
    
    Each method provides a different approach to measuring the similarity
    between two strings, varying in precision and performance characteristics.
    """
    LEVENSHTEIN = "levenshtein"
    ABSOLUTE = "absolute"
    JACCARD = "jaccard"
    COSINE = "cosine"
    FUZZY = "fuzzy"

class StringSimilarity(Evaluator):
    """
    Evaluator that calculates the similarity between two strings.
    
    This class provides multiple methods for comparing string values,
    including Levenshtein distance, Jaccard similarity, cosine similarity,
    fuzzy matching, and absolute equality.
    """
    
    def __init__(self, method: StringSimilarityMethod=StringSimilarityMethod.LEVENSHTEIN, case_sensitive: bool=True) -> None:
        """
        Initialize a StringSimilarity evaluator.
        
        Args:
            method: The method to use for calculating string similarity,
                   defaulting to Levenshtein distance
            case_sensitive: Whether comparisons should be case-sensitive
        """
        super().__init__("StringSimilarity", "StringSimilarity", method)
        self.case_sensitive = case_sensitive

    def Evaluate(self, value1, value2, method: StringSimilarityMethod=None) -> float:
        """
        Evaluate the similarity between two strings.
        
        Args:
            value1: First string to compare
            value2: Second string to compare
            method: Optional method override for this specific evaluation
            
        Returns:
            float: Similarity score between 0.0 (completely different) and 
                  1.0 (identical), as determined by the specified method
                  
        Raises:
            ValueError: If an invalid method is specified
        """
        if method is None:
            method = self.method

        if method == StringSimilarityMethod.LEVENSHTEIN:
            return self.levenshtein(value1, value2)
        elif method == StringSimilarityMethod.JACCARD:
            return self.jaccard(value1, value2)
        elif method == StringSimilarityMethod.COSINE:
            return self.cosine(value1, value2)
        elif method == StringSimilarityMethod.FUZZY:
            return self.fuzzy(value1, value2)   
        elif method == StringSimilarityMethod.ABSOLUTE:
            return self.absolute(value1, value2)
        else:
            raise ValueError(f"Invalid method: {method}")

    def absolute(self, value1, value2) -> float:
        """
        Calculate absolute equality between two strings.
        
        Returns 1.0 if the strings are identical, 0.0 otherwise.
        Case sensitivity is determined by self.case_sensitive.
        
        Returns:
            float: 1.0 if identical, 0.0 otherwise
        """
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        return 1.0 if value1 == value2 else 0.0

    def levenshtein(self, value1, value2) -> float:
        """
        Calculate similarity using Levenshtein distance.
        
        Levenshtein distance measures the minimum number of single-character edits
        (insertions, deletions, substitutions) required to change one string into another.
        This method returns a normalized similarity score between 0.0 and 1.0.
        
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        # Calculate the Levenshtein distance between the value1 and the value2
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        if value1 == value2:
            return 1.0
        
        # Convert to strings if they aren't already
        value1 = str(value1)
        value2 = str(value2)
        
        if len(value1) == 0 and len(value2) == 0:
            return 1.0
        
        # Create a matrix of size (len(value1)+1) x (len(value2)+1)
        matrix = [[0 for _ in range(len(value2) + 1)] for _ in range(len(value1) + 1)]
        
        # Initialize the first row and column
        for i in range(len(value1) + 1):
            matrix[i][0] = i
        for j in range(len(value2) + 1):
            matrix[0][j] = j
        
        # Fill the matrix
        for i in range(1, len(value1) + 1):
            for j in range(1, len(value2) + 1):
                if value1[i-1] == value2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # deletion
                        matrix[i][j-1] + 1,    # insertion
                        matrix[i-1][j-1] + 1   # substitution
                    )
        
        # Calculate similarity as 1 - normalized distance
        max_len = max(len(value1), len(value2))
        if max_len == 0:
            return 1.0
        
        distance = matrix[len(value1)][len(value2)]
        similarity = 1.0 - (distance / max_len)
        
        return similarity

    def jaccard(self, value1, value2) -> float:
        """
        Calculate similarity using Jaccard similarity coefficient.
        
        The Jaccard similarity measures the size of the intersection divided by the size
        of the union of two sets. For strings, the sets are the unique characters in each.
        
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        # Calculate the Jaccard similarity coefficient between the value1 and the value2
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        if value1 == value2:
            return 1.0
        
        # Convert to sets of characters
        value1_set = set(value1)    
        value2_set = set(value2)
        
        # Calculate the intersection and union of the sets
        intersection = value1_set.intersection(value2_set)
        union = value1_set.union(value2_set)
        
        # Calculate the Jacca   rd similarity coefficient
        if len(union) == 0:
            return 1.0
        
        return len(intersection) / len(union)

    def cosine(self, value1, value2) -> float:
        """
        Calculate similarity using cosine similarity.
        
        Cosine similarity measures the cosine of the angle between two vectors. 
        For strings treated as character sets, this implementation is equivalent
        to the Jaccard coefficient.
        
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        # Calculate the cosine similarity between the value1 and the value2
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        if value1 == value2:
            return 1.0
        
        # Convert to sets of characters
        value1_set = set(value1)
        value2_set = set(value2)
        
        # Calculate the intersection and union of the sets
        intersection = value1_set.intersection(value2_set)
        union = value1_set.union(value2_set)

        # Calculate the cosine similarity
        if len(union) == 0:
            return 1.0
        
        return len(intersection) / len(union)

    # Fuzzy matching using fuzzywuzzy
    # which is a library for fuzzy string matching
    # https://github.com/seatgeek/fuzzywuzzy    
    def fuzzy(self, value1, value2) -> float:
        """
        Calculate similarity using fuzzy string matching.
        
        Uses the fuzzywuzzy library's partial_ratio method which finds the best
        matching substring and calculates the similarity. Results are normalized
        to a value between 0.0 and 1.0.
        
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        # Calculate the fuzzy similarity between the value1 and the value2
        if value1 == value2:
            return 1.0
        
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        return fuzz.partial_ratio(value1, value2)
