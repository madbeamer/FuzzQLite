#!/usr/bin/env python3
"""
Base Fuzzer Class

This module defines the abstract base class for all fuzzers.
"""

import abc
from typing import List, Optional, Tuple, Union


class Fuzzer(abc.ABC):
    """
    Abstract base class for fuzzers.
    
    This class defines the interface that all fuzzer implementations
    must follow.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the fuzzer.
        
        Args:
            seed: Optional seed for random number generation
        """
        self.seed = seed
        self.corpus = []
    
    @abc.abstractmethod
    def fuzz(self) -> Union[str, Tuple[str, str]]:
        """
        Generate a fuzz input.
        
        Returns:
            A tuple containing (db_path, mutated_sql_query)
        """
        return "", ""
    
    def add_to_corpus(self, item: str) -> None:
        """
        Add an item to the corpus.
        
        Args:
            item: String to add to corpus
        """
        self.corpus.append(item)
    
    def load_corpus(self, corpus_items: List[str]) -> None:
        """
        Load multiple items into the corpus.
        
        Args:
            corpus_items: List of strings to add to corpus
        """
        self.corpus.extend(corpus_items)
