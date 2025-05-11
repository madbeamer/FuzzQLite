import os
import datetime
import shutil
from typing import Dict, Any

from runner.utils.outcome import Outcome

class BugTracker:
    """
    Class to track and save bug reproducers.
    
    When a bug or crash is found, this class creates a directory with all
    required files for reproducing the issue. Bug reproducers are organized by
    SQLite version and bug type.
    """
    
    def __init__(self, output_dir: str = "bug_reproducers"):
        """
        Initialize the bug tracker.
        
        Args:
            output_dir: Directory to store bug reproducers
        """
        self.output_dir = output_dir
        
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def save_reproducer(self, 
                        bug_type: str, 
                        sql_query: str, 
                        db_path: str,
                        target_sqlite_version: str,
                        target_result: Dict[str, Any],
                        reference_sqlite_version: str,
                        reference_result: Dict[str, Any]) -> str:
        """
        Save a bug reproducer.
        
        Args:
            bug_type: Type of bug (CRASH, LOGIC_BUG, or REFERENCE_ERROR)
            sql_query: The SQL query that triggered the bug
            db_path: Path to the original database file
            target_sqlite_version: SQLite version where the bug was found
            target_result: Result from the target SQLite
            reference_sqlite_version: SQLite version of the reference (for logic bugs or reference errors)
            reference_result: Result from the reference SQLite (for logic bugs or reference errors)
            
        Returns:
            Path to the created bug reproducer directory
        """
        # Determine which version to use for the directory structure
        version_for_dir = target_sqlite_version
        if bug_type == Outcome.REFERENCE_ERROR:
            version_for_dir = reference_sqlite_version
        
        # Create version directory if it doesn't exist
        version_dir = os.path.join(self.output_dir, version_for_dir)
        if not os.path.exists(version_dir):
            os.makedirs(version_dir)
        
        # Create bug type directory if it doesn't exist
        bug_type_lower = bug_type.lower()
        if bug_type == Outcome.CRASH:
            bug_type_dir = os.path.join(version_dir, "crashes")
        elif bug_type == Outcome.LOGIC_BUG:
            bug_type_dir = os.path.join(version_dir, "logic_bugs")
        elif bug_type == Outcome.REFERENCE_ERROR:
            bug_type_dir = os.path.join(version_dir, "reference_errors")
        else:
            bug_type_dir = os.path.join(version_dir, bug_type_lower)
        
        if not os.path.exists(bug_type_dir):
            os.makedirs(bug_type_dir)
        
        # Create a unique directory for this bug with bug type prefix, version and microseconds for uniqueness
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        bug_dir = os.path.join(bug_type_dir, f"{bug_type.lower()}_{version_for_dir}_{timestamp}")
        
        # Additional safety: if directory still exists (extremely unlikely), add a counter
        counter = 1
        original_bug_dir = bug_dir
        while os.path.exists(bug_dir):
            bug_dir = f"{original_bug_dir}_{counter}"
            counter += 1
        
        os.makedirs(bug_dir)
        
        # 1. Save original_test.sql
        with open(os.path.join(bug_dir, "original_test.sql"), "w") as f:
            f.write(sql_query)
        
        # 2. Create reduced_test.sql
        with open(os.path.join(bug_dir, "reduced_test.sql"), "w") as f:
            f.write(sql_query)
            # FIXME: Write a query reducer
        
        # 3. Copy the saved database state
        if db_path and os.path.exists(db_path):
            # Copy the pre-execution database state
            shutil.copy2(db_path, os.path.join(bug_dir, "test.db"))
        elif db_path and db_path != ":memory:" and os.path.exists(db_path):
            # Fallback to current database state if saved state not available
            shutil.copy2(db_path, os.path.join(bug_dir, "test.db"))
        else:
            # If no database is available, create a text file indicating this issue
            with open(os.path.join(bug_dir, "missing_db.txt"), "w") as f:
                f.write("No database file available for this bug reproducer.\n")
                f.write("Original database path was: {}\n".format(db_path))
        
        # 4. Create README.md
        self._create_readme(bug_dir, bug_type, sql_query, target_sqlite_version, target_result, reference_sqlite_version, reference_result)
        
        # 5. Save version.txt
        with open(os.path.join(bug_dir, "version.txt"), "w") as f:
            f.write(target_sqlite_version if bug_type != "REFERENCE_ERROR" else reference_sqlite_version)
        
        return bug_dir
    
    def _create_readme(self,
                    bug_dir: str,
                    bug_type: str,
                    sql_query: str,
                    target_sqlite_version: str,
                    target_result: Dict[str, Any],
                    reference_sqlite_version: str,
                    reference_result: Dict[str, Any],
                    ) -> None:
        """
        Create a README.md file describing the bug.
        
        Args:
            bug_dir: Directory to save the README
            bug_type: Type of bug (CRASH, LOGIC_BUG, or REFERENCE_ERROR)
            sql_query: The SQL query that triggered the bug
            target_sqlite_version: SQLite version where the bug was found
            target_result: Result from the target SQLite
            reference_sqlite_version: SQLite version of the reference (for logic bugs or reference errors)
            reference_result: Result from the reference SQLite (for logic bugs or reference errors)
        """

        # Process stdout and stderr to limit to 50 lines max
        def limit_output(output, max_lines=50):
            if not output:
                return "No output available"
            
            lines = output.splitlines()
            if len(lines) <= max_lines:
                return output
            
            limited_lines = lines[:max_lines]
            limited_output = "\n".join(limited_lines)
            return limited_output + f"\n\n[Output truncated to {max_lines} lines.]"

        target_stdout = limit_output(target_result.get('stdout', ''))
        target_stderr = limit_output(target_result.get('stderr', ''))
        reference_stdout = limit_output(reference_result.get('stdout', ''))
        reference_stderr = limit_output(reference_result.get('stderr', ''))

        with open(os.path.join(bug_dir, "README.md"), "w") as f:
            # Write header
            f.write(f"# SQLite {bug_type} \n\n")
            f.write(f"This bug was found by FuzzQLite on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n")
            
            # Write SQL query
            f.write("## SQL Query\n\n")
            f.write("```sql\n")
            f.write(sql_query)
            f.write("\n```\n\n")
            
            # Write expected vs actual behavior
            f.write(f"## Expected vs. Actual Behavior\n\n")
            
            if bug_type == Outcome.CRASH:
                f.write("### Expected Behavior\n\n")
                f.write("The query should execute without crashing the SQLite process.\n\n")
                f.write(f"Reference SQLite Behavior (reference version: {reference_sqlite_version}):\n\n")
                f.write("```\n")
                f.write(reference_stdout)
                f.write("\n```\n\n")
                
                f.write("### Actual Behavior\n\n")
                f.write("The query causes SQLite to crash with the following error:\n\n")
                f.write("```\n")
                f.write(target_stderr)
                f.write("\n```\n\n")
            
            elif bug_type == Outcome.LOGIC_BUG:
                if reference_result:
                    f.write(f"### Expected Behavior (reference version: {reference_sqlite_version})\n\n")
                    f.write("```\n")
                    f.write(reference_stdout)
                    f.write("\n```\n\n")
                
                f.write(f"### Actual Behavior (target version: {target_sqlite_version})\n\n")
                f.write("```\n")
                f.write(target_stdout)
                f.write("\n```\n\n")
            
            elif bug_type == Outcome.REFERENCE_ERROR:
                f.write(f"### Target SQLite Behavior (target version: {target_sqlite_version})\n\n")
                f.write("The target SQLite version executed the query successfully:\n\n")
                f.write("```\n")
                f.write(target_stdout)
                f.write("\n```\n\n")
                
                f.write(f"### Reference SQLite Error (reference version: {reference_sqlite_version})\n\n")
                f.write("The reference SQLite version failed to execute the query with the following error:\n\n")
                f.write("```\n")
                f.write(reference_stderr)
                f.write("\n```\n\n")
            
            # Write reproduction steps
            f.write("## Steps to Reproduce\n\n")
            f.write("1. Create a test database using the included `test.db` file\n")
            f.write("2. Run the SQL query in `reduced_test.sql` against this database\n")
            f.write("3. Observe the bug/crash\n\n")
            
            # Write additional notes
            f.write("## Notes\n\n")
            f.write("- `original_test.sql` contains the original query that triggered the bug\n")
            f.write("- `reduced_test.sql` contains a minimized version that still triggers the bug\n")
            f.write("- `test.db` is the database file used when the bug was discovered\n")
            f.write("- `version.txt` contains the SQLite version where this bug was found\n")
            