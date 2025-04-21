#!/usr/bin/env python3
"""
Base Runner Classes

This module defines the abstract base classes for runners that execute
fuzzed inputs and the outcome classification for execution results.
"""

import subprocess
from typing import Any, Tuple


class Outcome:
    """Base class for the outcome of a program execution."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"
    # Extended by SQLiteOutcome in sqlite_runner.py with:
    # CRASH = "CRASH"
    # LOGIC_BUG = "LOGIC_BUG"


class Runner:
    """Base class to run external programs."""
    
    def run(self, input_data: str) -> Tuple[subprocess.CompletedProcess, str]:
        """
        Run the program with the given input.
        
        Args:
            input_data: String input to feed to the program
            
        Returns:
            Result of the process run and outcome
        """
        raise NotImplementedError("Subclasses must implement this method")


class PrintRunner(Runner):
    """Simple runner that prints the input."""
    
    def run(self, input_data: str) -> Tuple[subprocess.CompletedProcess, str]:
        """
        Print the input and return an empty result.
        
        Args:
            input_data: String input to print
            
        Returns:
            A CompletedProcess instance and outcome
        """
        print(input_data)
        print(20 * "-")
        return subprocess.CompletedProcess(args="", returncode=0, stdout="", stderr=""), Outcome.PASS
    