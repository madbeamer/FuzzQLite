#!/usr/bin/env python3
"""
Mutation Fuzzer

This module implements a mutation-based fuzzer for SQLite.
"""

import random
from typing import List, Optional, Any

from fuzzer.base_fuzzer import Fuzzer
from mutations.base_mutation import Mutation
from mutations.dummy_mutation import CapitalizeMutation


class MutationFuzzer(Fuzzer):
    """
    A fuzzer that mutates existing inputs to generate new test cases.
    """
    
    def __init__(self, seed: Optional[int] = None, 
                 mutations: Optional[List[Mutation]] = None):
        """
        Initialize the mutation fuzzer.
        
        Args:
            seed: Optional seed for random number generation
            mutations: List of mutation operators to use
        """
        super().__init__(seed=seed)
        
        if mutations is None:
            # Default to using the dummy capitalize mutation
            self.mutations = [CapitalizeMutation()]
        else:
            self.mutations = mutations
            
        # Set the random seed if provided
        if seed is not None:
            random.seed(seed)
    
    def fuzz(self) -> str:
        """
        Generate a fuzz input by mutating an item from the corpus.
        
        Returns:
            A string containing the fuzzed input
        """
        if not self.corpus:
            # If corpus is empty, return an empty string
            return ""
        
        # Select a random item from the corpus
        seed = random.choice(self.corpus)
        
        # Select a random mutation
        mutation = random.choice(self.mutations)
        
        # Apply the mutation
        return mutation.mutate(seed)
    