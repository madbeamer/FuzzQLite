#!/usr/bin/env python3
"""
Identity Mutation

This module implements a simple identity mutation that returns the input unchanged.
"""

from mutations.base_mutation import Mutation

class IdentityMutation(Mutation):
    """
    A simple mutation that returns the input unchanged.
    
    This is a basic pass-through mutation used for testing FuzzQLite.
    """
    
    def __init__(self):
        """Initialize the identity mutation."""
        super().__init__()
    
    def mutate(self, input_data: str) -> str:
        """
        Apply identity mutation to the input (returns unchanged).
        
        Args:
            input_data: The input string to mutate
            
        Returns:
            The original input string unchanged
        """
        return input_data
    
    @property
    def name(self) -> str:
        """
        Get the name of this mutation operator.
        
        Returns:
            String name of the mutation
        """
        return "Identity"
    