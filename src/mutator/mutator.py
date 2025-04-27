import abc


class Mutator(abc.ABC):
    """
    Abstract base class for mutators.
    
    This class defines the interface that all mutation implementations
    must follow.
    """
    
    def __init__(self):
        """Initialize the mutation operator."""
        pass
    
    @abc.abstractmethod
    def mutate(self, input_data: str) -> str:
        """
        Apply the mutation to the input data.
        
        Args:
            input_data: The input string to mutate
            
        Returns:
            The mutated string
        """
        pass
    
    @property
    def name(self) -> str:
        """
        Get the name of this mutation operator.
        
        Returns:
            String name of the mutation
        """
        return self.__class__.__name__
    