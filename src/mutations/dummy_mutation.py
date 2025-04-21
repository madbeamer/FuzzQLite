#!/usr/bin/env python3
"""
Dummy Mutation

This module implements a simple dummy mutation that capitalizes input strings.
"""

from mutations.base_mutation import Mutation


class CapitalizeMutation(Mutation):
    """
    A simple mutation that capitalizes the input string.
    
    This is a basic example mutation used for testing the fuzzer framework.
    """
    
    def mutate(self, input_data: str) -> str:
        """
        Apply capitalization mutation to the input.
        
        Args:
            input_data: The input string to mutate
            
        Returns:
            The capitalized string
        """
        return input_data.upper()
    
    @property
    def name(self) -> str:
        """
        Get the name of this mutation operator.
        
        Returns:
            String name of the mutation
        """
        return "capitalize"
    