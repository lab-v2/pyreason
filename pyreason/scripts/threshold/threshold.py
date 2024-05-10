class Threshold:  
    """  
    A class representing a threshold for a clause in a rule.  
  
    Attributes:  
        quantifier (str): The comparison operator, e.g., 'greater_equal', 'less', etc.  
        quantifier_type (tuple): A tuple indicating the type of quantifier, e.g., ('number', 'total').  
        thresh (int): The numerical threshold value to compare against.  
  
    Methods:  
        to_tuple(): Converts the Threshold instance into a tuple compatible with numba types.  
    """  
  
    def __init__(self, quantifier, quantifier_type, thresh):  
        """  
        Initializes a Threshold instance.  
  
        Args:  
            quantifier (str): The comparison operator for the threshold.  
            quantifier_type (tuple): The type of quantifier ('number' or 'percent', 'total' or 'available').  
            thresh (int): The numerical value for the threshold.  
        """

        if quantifier not in ("greater_equal", "greater", "less_equal", "less", "equal"):
            raise ValueError("Invalid quantifier")

        if quantifier_type[0] not in ("number", "percent") or quantifier_type[1] not in ("total", "available"):
            raise ValueError("Invalid quantifier type")

        self.quantifier = quantifier
        self.quantifier_type = quantifier_type
        self.thresh = thresh

    def to_tuple(self):  
        """  
        Converts the Threshold instance into a tuple compatible with numba types.  
  
        Returns:  
            tuple: A tuple representation of the Threshold instance.  
        """  
        return (self.quantifier, self.quantifier_type, self.thresh)