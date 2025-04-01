# StringSimilarity is a class that evaluates a string
# It is used to evaluate the execution of a PostStep
# when comparing strings, we can use the Levenshtein distance
# to evaluate the similarity between the value1 and the value2
# or we can use the Jaccard similarity coefficient
# 

from Profiler import Evaluator
from enum import Enum
from fuzzywuzzy import fuzz

class StringSimilarityMethod(Enum):
    LEVENSHTEIN = "levenshtein"
    ABSOLUTE = "absolute"
    JACCARD = "jaccard"
    COSINE = "cosine"
    FUZZY = "fuzzy"

class StringSimilarity(Evaluator):
    def __init__(self, method: StringSimilarityMethod=StringSimilarityMethod.LEVENSHTEIN, case_sensitive: bool=True) -> None:
        super().__init__("StringSimilarity", "StringSimilarity", method)
        self.case_sensitive = case_sensitive

    def Evaluate(self, value1, value2, method: StringSimilarityMethod=None) -> float:
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
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        return 1.0 if value1 == value2 else 0.0

    def levenshtein(self, value1, value2) -> float:
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
        # Calculate the fuzzy similarity between the value1 and the value2
        if value1 == value2:
            return 1.0
        
        if not self.case_sensitive:
            value1 = value1.lower()
            value2 = value2.lower()

        return fuzz.partial_ratio(value1, value2)
