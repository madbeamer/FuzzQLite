#!/usr/bin/env python3
"""
Base Fuzzer Class

This module defines the abstract base class for all fuzzers in the system,
based on examples from fuzzingbook.org and adapted for SQLite fuzzing.
"""

import abc
import subprocess
from typing import List, Optional, Tuple, Any, Dict

from utils.base_runner import Runner, PrintRunner, Outcome


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
    def fuzz(self) -> str:
        """
        Generate a fuzz input.
        
        Returns:
            A string containing the fuzzed input
        """
        return ""
    
    def run(self, runner: Runner) -> Tuple[subprocess.CompletedProcess, str]:
        """
        Run `runner` with fuzz input.
        
        Args:
            runner: The runner to execute the fuzzing input
            
        Returns:
            A tuple containing the process result and outcome
        """
        return runner.run(self.fuzz())
    
    def runs(self, runner: Runner = PrintRunner(), trials: int = 10) -> List[Tuple[subprocess.CompletedProcess, str]]:
        """
        Run `runner` with fuzz input, `trials` times.
        
        Args:
            runner: The runner to execute the fuzzing input
            trials: Number of times to run the fuzzer
            
        Returns:
            A list of tuples containing the process results and outcomes
        """
        return [self.run(runner) for i in range(trials)]
    
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
