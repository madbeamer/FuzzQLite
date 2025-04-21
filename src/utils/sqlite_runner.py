#!/usr/bin/env python3
"""
SQLite Runner

Utility class to run SQLite with fuzzed inputs and perform differential testing.
"""

import subprocess
import tempfile
from typing import Optional, Tuple, Dict, Any

from utils.base_runner import Runner, Outcome


class SQLiteOutcome(Outcome):
    """Extended outcome class for SQLite-specific results."""
    CRASH = "CRASH"         # SQLite crashed
    LOGIC_BUG = "LOGIC_BUG" # Different result from reference version
    PASS = "PASS"           # Executed successfully with same result as reference
    FAIL = "FAIL"           # Execution failed but not crashed


class SQLiteRunner(Runner):
    """
    Runner for SQLite database inputs with differential testing capability.
    """
    
    def __init__(self, 
                 sqlite_path: str,
                 reference_sqlite_path: str = "/usr/bin/sqlite3-latest",
                 db_path: Optional[str] = None,
                 timeout: int = 30):
        """
        Initialize the SQLite runner.
        
        Args:
            sqlite_path: Path to the SQLite executable to test
            reference_sqlite_path: Path to the reference SQLite executable
            db_path: Path to the database file (uses :memory: if None)
            timeout: Timeout in seconds for the SQLite process
        """
        self.sqlite_path = sqlite_path
        self.reference_sqlite_path = reference_sqlite_path
        self.db_path = db_path if db_path else ":memory:"
        self.timeout = timeout
    
    def _run_sqlite(self, sqlite_path: str, input_data: str) -> Dict[str, Any]:
        """
        Run a specific SQLite version with the given input.
        
        Args:
            sqlite_path: Path to the SQLite executable
            input_data: SQL query or command to run
            
        Returns:
            A dictionary with execution result information
        """
        # Create a temporary file for the SQL input
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sql') as temp_file:
            temp_file.write(input_data)
            temp_file.flush()
            
            result = {
                'crashed': False,
                'returncode': None,
                'stdout': None,
                'stderr': None,
                'timeout': False,
                'exception': None
            }
            
            try:
                # Run SQLite with the input file
                cmd = [sqlite_path, self.db_path, ".read " + temp_file.name]
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                result['returncode'] = process.returncode
                result['stdout'] = process.stdout
                result['stderr'] = process.stderr
                    
            except subprocess.TimeoutExpired:
                # Handle timeouts
                result['timeout'] = True
                result['crashed'] = True
            except Exception as e:
                # Handle other exceptions
                result['exception'] = str(e)
                result['crashed'] = True
                
            return result
    
    def run(self, input_data: str) -> Tuple[subprocess.CompletedProcess, str]:
        """
        Run SQLite with the given input and compare with reference version.
        
        Args:
            input_data: SQL query or command to run
            
        Returns:
            A tuple containing the CompletedProcess and an Outcome
        """
        # Run the test target SQLite version
        target_result = self._run_sqlite(self.sqlite_path, input_data)
        
        # Create a CompletedProcess object for return value compatibility
        process = subprocess.CompletedProcess(
            args=[self.sqlite_path, self.db_path],
            returncode=target_result.get('returncode', -1),
            stdout=target_result.get('stdout', ''),
            stderr=target_result.get('stderr', '')
        )
        
        # Check for crashes
        if target_result['crashed']:
            return process, SQLiteOutcome.CRASH
        
        # If not a crash, check for logic bugs by comparing with reference
        if target_result['returncode'] == 0:
            # Only run reference if target didn't crash
            reference_result = self._run_sqlite(self.reference_sqlite_path, input_data)
            
            # Skip comparison if reference crashed or failed
            # (Focus on bugs in target, not in reference)
            if not reference_result['crashed'] and reference_result['returncode'] == 0:
                if reference_result['stdout'] != target_result['stdout']:
                    # Output differs - potential logic bug
                    process.reference_stdout = reference_result['stdout']
                    return process, SQLiteOutcome.LOGIC_BUG
                return process, SQLiteOutcome.PASS
            return process, SQLiteOutcome.PASS
        
        # Non-zero return code but not a crash
        return process, SQLiteOutcome.FAIL
    