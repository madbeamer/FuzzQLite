import abc
from typing import Any


class Mutator(abc.ABC):
    """
    Abstract base class for mutators.
    
    This class defines the interface that all mutation implementations
    must follow.
    """
    
    def __init__(self):
        """Initialize the mutator."""
        pass
    
    @abc.abstractmethod
    def mutate(self, input_data: Any) -> Any:
        """
        Apply the mutation to the input data.
        
        Args:
            input_data: The input to mutate
            
        Returns:
            The mutated input
        """
        pass
    
    @property
    def name(self) -> str:
        """
        Get the name of this mutator.
        
        Returns:
            String name of the mutator
        """
        return self.__class__.__name__
    