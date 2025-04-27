from typing import Tuple

from mutator import Mutator


class IdentitiyMutator(Mutator):
    """A simple mutator that returns the input unchanged."""
    
    def __init__(self):
        """Initialize the identity mutator."""
        super().__init__()
    
    def mutate(self, input_data: Tuple[str, str]) -> Tuple[str, str]:
        """
        Apply identity mutator to the input (returns unchanged).
        
        Args:
            input_data: The input to mutate
            
        Returns:
            The original input unchanged
        """
        return input_data
    