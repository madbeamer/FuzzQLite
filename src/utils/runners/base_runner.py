#!/usr/bin/env python3
"""
Base Runner Classes

This module defines the abstract base classes for runners that execute
fuzzed inputs and the outcome classification for execution results.
"""

import abc
from typing import Any, Dict, Tuple, Union


class Outcome:
    """This class defines the possible outcomes of running a fuzzed input."""
    PASS = "PASS"                        # Executed successfully with same result as reference
    REFERENCE_ERROR = "REFERENCE_ERROR"  # Target executed successfully but reference SQLite crashed
    CRASH = "CRASH"                      # Target SQLite crashed, reference didn't
    LOGIC_BUG = "LOGIC_BUG"              # Different result between target and reference (both succeeded)
    INVALID_QUERY = "INVALID_QUERY"      # Both target and reference SQLite crashed


class RunResult:
    """Class to encapsulate the result of running a program with fuzzed input."""
    
    def __init__(self,
                 outcome: str,
                 sql_query: str,
                 db_path: str,
                 saved_db_path: str,
                 target_sqlite_version: str,
                 target_result: Dict[str, Any],
                 reference_sqlite_version: str,
                 reference_result: Dict[str, Any]):
        """
        Initialize a run result with all required attributes.
        
        Args:
            outcome: The outcome classification of the run
            sql_query: The SQL query that was executed
            db_path: Path to the database file
            saved_db_path: Path to the saved database copy
            target_sqlite_version: Version of the target SQLite
            target_result: Result from target SQLite
            reference_sqlite_version: Version of the reference SQLite
            reference_result: Result from reference SQLite
        """
        self.outcome = outcome
        self.sql_query = sql_query
        self.db_path = db_path
        self.saved_db_path = saved_db_path
        self.target_sqlite_version = target_sqlite_version
        self.target_result = target_result
        self.reference_sqlite_version = reference_sqlite_version
        self.reference_result = reference_result


class Runner(abc.ABC):
    """Base class to run external programs."""
    
    @abc.abstractmethod
    def run(self, input_data: Union[str, Tuple[Any, ...]]) -> RunResult:
        """
        Run the program with the given input.
        
        Args:
            input_data: Input to feed to the program (string or tuple)
            
        Returns:
            A RunResult object containing process result and outcome
        """
        pass
    
    def cleanup(self):
        """Clean up any resources. Default implementation does nothing."""
        pass
