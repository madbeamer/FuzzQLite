import subprocess
import tempfile
import shutil
import os
import time
import datetime
from typing import Tuple, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
import rich.box

from .outcome import Outcome
from .run_result import RunResult
from utils import BugTracker


class SQLiteRunner:
    """
    Runner for SQLite database inputs with differential testing capability.
    """
    
    def __init__(self, 
                 target_sqlite_path: str,
                 reference_sqlite_path: str,
                 timeout: int = 30):
        """
        Initialize the SQLite runner.
        
        Args:
            target_sqlite_path: Path to the SQLite executable to test
            reference_sqlite_path: Path to the reference SQLite executable
            timeout: Timeout in seconds for the SQLite process
        """
        self.target_sqlite_path = target_sqlite_path
        self.reference_sqlite_path = reference_sqlite_path
        self.timeout = timeout
        self.temp_dir = tempfile.mkdtemp(prefix="fuzzqlite_")
        self.console = Console()
        
        # Initialize stats with the allowed outcomes
        self.stats = {
            "PASS": 0,
            "CRASH": 0,
            "LOGIC_BUG": 0,
            "REFERENCE_ERROR": 0,
            "INVALID_QUERY": 0,
        }
        
        # For progress tracking
        self.start_time = None
        self.total_trials = 0
        self.current_trial = 0
        self.results = []
        self.live_display = None
        
        # Define outcome styling
        self.outcome_styles = {
            Outcome.PASS: "green",
            Outcome.CRASH: "red",
            Outcome.LOGIC_BUG: "red",
            Outcome.REFERENCE_ERROR: "yellow",
            Outcome.INVALID_QUERY: "blue",
        }
    
    def _save_database_state(self, db_path: str, prefix: str) -> str:
        """
        Save a copy of the database before executing the query.
        
        Args:
            db_path: Path to the original database
            prefix: Prefix for the saved database filename
        
        Returns:
            Path to the saved copy or None if database doesn't exist
        """
        if db_path and db_path != ":memory:" and os.path.exists(db_path):
            # Create a copy of the database
            saved_db_path = os.path.join(self.temp_dir, f"{prefix}_{os.path.basename(db_path)}")
            shutil.copy2(db_path, saved_db_path)
            return saved_db_path
        return None
    
    def _run_sqlite(self, sqlite_path: str, sql_query: str, db_path: str) -> Dict[str, Any]:
        """
        Run a specific SQLite version with the given input.
        
        Args:
            sqlite_path: Path to the SQLite executable
            sql_query: SQL query
            db_path: Path to the database file
            
        Returns:
            A dictionary with execution result information
        """
        # Create a temporary file for the SQL input
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.sql', delete=False) as temp_file:
            temp_file.write(sql_query)
            temp_file.flush()
            
            result = {
                'returncode': None,
                'stdout': None,
                'stderr': None,
            }
            
            try:
                # Run SQLite with the input file
                cmd = [sqlite_path, db_path]
                with open(temp_file.name, 'r') as sql_file:
                    process = subprocess.run(
                        cmd,
                        stdin=sql_file,
                        capture_output=True,
                        text=True,
                        timeout=self.timeout
                    )
                
                result['returncode'] = process.returncode
                result['stdout'] = process.stdout
                result['stderr'] = process.stderr
                    
            except subprocess.TimeoutExpired as e:
                result['returncode'] = -1
                result['stdout'] = e.stdout
                result['stderr'] = e.stderr
            except Exception as e:
                result['returncode'] = -1
                result['stderr'] = str(e)
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file.name)
                except:
                    pass  # Ignore cleanup errors
                
            return result
    
    def _normalize_output(self, output: str) -> str:
        """
        Normalize output to handle floating point differences and other variations.
        
        Args:
            output: Raw SQLite output
            
        Returns:
            Normalized output
        """
        lines = output.strip().split('\n')
        normalized_lines = []
        
        for line in lines:
            # Handle empty lines
            if not line.strip():
                continue
                
            # Split by common delimiters
            parts = line.split('|')
            normalized_parts = []
            
            for part in parts:
                part = part.strip()
                
                # Try to handle floating point numbers
                try:
                    float_val = float(part)
                    # Round to a reasonable precision (e.g., 10 decimal places)
                    if '.' in part:
                        normalized_parts.append(f"{float_val:.10f}")
                    else:
                        normalized_parts.append(part)
                except ValueError:
                    normalized_parts.append(part)
            
            normalized_lines.append('|'.join(normalized_parts))
        
        return '\n'.join(normalized_lines)
    
    def run(self, inp: Tuple[str, str]) -> RunResult:
        """
        Run SQLite with the given input and compare with reference version.
        
        Args:
            inp: Tuple of (sql_query, db_path)
            
        Returns:
            A RunResult containing process result and outcome
        """
        sql_query, db_path = inp

        # Create a fresh copy of the database for reference testing
        reference_db_path = self._save_database_state(db_path, prefix="reference")
        
        # Save the database state before running the query (for reproducibility)
        saved_db_path = self._save_database_state(db_path, prefix="saved")
        
        # Run on target version
        target_result = self._run_sqlite(self.target_sqlite_path, sql_query, db_path)
        target_sqlite_version = self.target_sqlite_path.split('-')[-1] if '-' in self.target_sqlite_path else "unknown"
        
        # Run on reference version
        reference_result = self._run_sqlite(self.reference_sqlite_path, sql_query, reference_db_path)
        reference_sqlite_version = self.reference_sqlite_path.split('-')[-1] if '-' in self.reference_sqlite_path else "unknown"
        
        # Determine outcome based on:
        # CRASH: target crashed (non-zero return code) AND reference did not crash (return code is 0)
        # LOGIC_BUG: both target and reference did not crash (return code 0) AND results differ
        # REFERENCE_ERROR: target did not crash (return code 0) AND reference crashed (non-zero return code)
        # INVALID_QUERY: both target and reference crashed (non-zero return code)
        # PASS: both target and reference did not crash (return code 0) AND results match
        
        target_crashed = target_result['returncode'] != 0
        reference_crashed = reference_result['returncode'] != 0
        
        if target_crashed and not reference_crashed:
            # Target crashed, reference succeeded
            outcome = Outcome.CRASH
        elif not target_crashed and reference_crashed:
            # Target succeeded, reference crashed
            outcome = Outcome.REFERENCE_ERROR
        elif not target_crashed and not reference_crashed:
            # Both succeeded, compare outputs
            normalized_output_target = self._normalize_output(target_result['stdout'])
            normalized_output_reference = self._normalize_output(reference_result['stdout'])
            
            if normalized_output_target != normalized_output_reference:
                outcome = Outcome.LOGIC_BUG
            else:
                outcome = Outcome.PASS
        else:
            # Both crashed
            outcome = Outcome.INVALID_QUERY
            
        return RunResult(
            outcome=outcome,
            sql_query=sql_query,
            db_path=db_path,
            saved_db_path=saved_db_path,
            target_sqlite_version=target_sqlite_version,
            target_result=target_result,
            reference_sqlite_version=reference_sqlite_version,
            reference_result=reference_result,
        )
    
    def start_fuzzing_session(self, total_trials: int, version: str):
        """
        Start a new fuzzing session.
        
        Args:
            total_trials: Total number of trials planned
            version: SQLite version being tested
        """
        self.start_time = time.time()
        self.total_trials = total_trials
        self.current_trial = 0
        self.results = []
        
        # Reset stats
        for outcome in self.stats:
            self.stats[outcome] = 0
        
        # Print header
        self.console.rule(style="bold")
        self.console.print("FuzzQLite - SQLite Fuzzer", style="bold")
        self.console.rule(style="bold")
        self.console.print(f"Target SQLite version: {version} ({self.target_sqlite_path})")
        self.console.print(f"Reference SQLite version: {self.reference_sqlite_path.split('-')[-1] if '-' in self.reference_sqlite_path else 'unknown'} ({self.reference_sqlite_path})")
        self.console.print(f"Number of trials: {total_trials}")
        self.console.rule(style="bold")
        self.console.print()
        
        # Create the live display
        self.live_display = Live(self._generate_progress_display(), refresh_per_second=4)
        self.live_display.start()
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into a more readable time string."""
        return str(datetime.timedelta(seconds=int(seconds)))
    
    def _calculate_rate(self) -> float:
        """Calculate the trials per second rate."""
        if not self.start_time or self.current_trial == 0:
            return 0.0
        
        elapsed = max(1, time.time() - self.start_time)
        return self.current_trial / elapsed
    
    def _estimate_completion(self) -> str:
        """Estimate completion time."""
        if not self.start_time or self.current_trial == 0:
            return "N/A"
        
        rate = self._calculate_rate()
        if rate == 0:
            return "N/A"
        
        remaining_trials = self.total_trials - self.current_trial
        remaining_seconds = remaining_trials / rate
        
        return self._format_time(remaining_seconds)
    
    def _generate_progress_display(self) -> Layout:
        """Generate the progress display layout."""
        layout = Layout()
        layout.split(
            Layout(name="stats"),
            Layout(name="trials"),
            Layout(name="results"),
        )
        
        # Create the stats part
        if self.start_time:
            elapsed = time.time() - self.start_time
            trials_per_sec = self._calculate_rate()
            
            stats_panel = Panel(
                f"[bold]Progress:[/] {self.current_trial}/{self.total_trials} trials ({self.current_trial/self.total_trials*100:.1f}%)\n"
                f"[bold]Elapsed:[/] {self._format_time(elapsed)}\n"
                f"[bold]Speed:[/] {trials_per_sec:.2f} trials/sec\n"
                f"[bold]Est. Remaining:[/] {self._estimate_completion()}",
                title="FuzzQLite Stats",
                border_style="blue",
                padding=(1, 2),
            )
            layout["stats"].update(stats_panel)
        else:
            layout["stats"].update(Panel("Starting...", title="FuzzQLite"))
        
        # Create the recent trials list
        if self.results:
            # Get the last 12 results (or fewer if there are less)
            recent_results = self.results[-12:]
            
            result_lines = []
            for i, result in enumerate(recent_results):
                outcome = result.outcome
                sql_query = result.sql_query
                
                # Truncate long queries
                query = sql_query.strip()
                if len(query) > 100:
                    query = query[:97] + "..."
                    
                # Format the line with emoji based on outcome
                emoji = "✓" if outcome == Outcome.PASS else "✗"
                style = self.outcome_styles.get(outcome, "default")
                
                # Add the basic outcome line
                result_line = f"[{style}]{emoji} {outcome}:[/] {query}"
                result_lines.append(result_line)
                
                # Add error details based on outcome
                if outcome == Outcome.CRASH:
                    target_stderr = result.target_result.get('stderr', '')
                    if target_stderr:
                        result_lines.append(f"  └─ {target_stderr.strip()}")
                
                elif outcome == Outcome.REFERENCE_ERROR:
                    reference_stderr = result.reference_result.get('stderr', '')
                    if reference_stderr:
                        result_lines.append(f"  └─ Reference: {reference_stderr.strip()}")
            
            results_text = "\n".join(result_lines)
            layout["trials"].update(Panel(results_text, title="Recent Trials", border_style="yellow"))
        else:
            layout["trials"].update(Panel("No results yet", title="Recent Trials"))

        # Create the results table
        results_table = Table(box=rich.box.SIMPLE_HEAVY, padding=(0, 3), collapse_padding=False)
        results_table.add_column("OUTCOME", style="bold")
        results_table.add_column("COUNT", justify="right", style="bold cyan")
        results_table.add_column("PERCENT", justify="right", style="bold magenta")
        
        outcome_groups = [
            ("green", [outcome for outcome in self.stats.keys() if outcome == Outcome.PASS]),
            ("yellow", [outcome for outcome in self.stats.keys() if outcome == Outcome.REFERENCE_ERROR]),
            ("red", [outcome for outcome in self.stats.keys() if outcome in (Outcome.CRASH, Outcome.LOGIC_BUG)]),
            ("blue", [outcome for outcome in self.stats.keys() if outcome == Outcome.INVALID_QUERY]),
        ]

        # Add rows to the table by outcome groups
        for i, (style, outcomes) in enumerate(outcome_groups):
            if not outcomes:
                continue
                
            for outcome in outcomes:
                count = self.stats.get(outcome, 0)
                percentage = (count / self.current_trial) * 100 if self.current_trial > 0 else 0
                results_table.add_row(
                    Text(outcome, style=style),
                    str(count),
                    f"{percentage:.2f}%"
                )
            
            # Add a separator between groups if there are more groups to come
            remaining_groups = [group for _, group in outcome_groups[i+1:] if group]
            if remaining_groups:
                table_has_next_group = any(len(group) > 0 for group in remaining_groups)
                if table_has_next_group:
                    results_table.add_section()
        
        layout["results"].update(Panel(results_table, title="Results Summary", border_style="green"))
        
        return layout
    
    def record_result(self, result: RunResult, bug_tracker: BugTracker) -> None:
        """
        Record a result and update the display.
        
        Args:
            result: The RunResult to record
            bug_tracker: Bug tracker for saving reproducers
        """
        self.current_trial += 1
        self.results.append(result)
        outcome = result.outcome
        self.stats[outcome] = self.stats.get(outcome, 0) + 1
        
        # Update the display
        if self.live_display:
            self.live_display.update(self._generate_progress_display())
        
        # Handle bug saving for reproducability
        if outcome in (Outcome.CRASH, Outcome.LOGIC_BUG, Outcome.REFERENCE_ERROR):
            bug_dir = bug_tracker.save_reproducer(
                bug_type=outcome,
                sql_query=result.sql_query,
                db_path=result.db_path,
                saved_db_path=result.saved_db_path,
                target_sqlite_version=result.target_sqlite_version,
                target_result=result.target_result,
                reference_sqlite_version=result.reference_sqlite_version,
                reference_result=result.reference_result
            )
            # Set bug_dir directly on the result
            result.bug_dir = bug_dir
    
    def finish_fuzzing_session(self, bug_tracker: BugTracker) -> None:
        """
        Finish the fuzzing session and display final stats.
        
        Args:
            bug_tracker: BugTracker for bug summary
        """
        # Stop the live display
        if self.live_display:
            self.live_display.stop()
        
        # Display bug summary if applicable
        bug_count = self.stats.get(Outcome.CRASH, 0) + self.stats.get(Outcome.LOGIC_BUG, 0) + self.stats.get(Outcome.REFERENCE_ERROR, 0)
        
        if bug_count > 0:
            self.console.print(f"[bold]Found {bug_count} bug{'s' if bug_count > 1 else ''}![/]")
            if bug_tracker:
                self.console.print(f"Bug reproducers saved to: {bug_tracker.output_dir}")
        else:
            self.console.print("[bold]No bugs found![/]")
        
        # Print elapsed time
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.console.print(f"Total time: {self._format_time(elapsed)}")
            self.console.print(f"Average speed: {self.total_trials / elapsed:.2f} trials/sec")
        
        self.console.print()
    
    def cleanup(self):
        """Clean up temporary directories."""
        if self.live_display:
            try:
                self.live_display.stop()
            except:
                pass
            
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
