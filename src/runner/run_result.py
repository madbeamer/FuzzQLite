from typing import Dict, Any

class RunResult:
    """Class to encapsulate the result of running a program with fuzzed input."""
    
    def __init__(self,
                 outcome: str,
                 sql_query: str,
                 db_path: str,
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
            target_sqlite_version: Version of the target SQLite
            target_result: Result from target SQLite
            reference_sqlite_version: Version of the reference SQLite
            reference_result: Result from reference SQLite
        """
        self.outcome = outcome
        self.sql_query = sql_query
        self.db_path = db_path
        self.target_sqlite_version = target_sqlite_version
        self.target_result = target_result
        self.reference_sqlite_version = reference_sqlite_version
        self.reference_result = reference_result
