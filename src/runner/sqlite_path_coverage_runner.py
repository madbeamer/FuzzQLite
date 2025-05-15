import subprocess
import shutil
import os
import time
import datetime
import re
import gc
from typing import List, Tuple, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
import rich.box

from runner.utils.outcome import Outcome
from runner.utils.run_result import RunResult
from runner.utils.coverage import read_gcov_coverage, read_gcov_coverage_percentage

from utils.bug_tracker import BugTracker


class SQLitePathCoverageRunner:
    """
    Runner for SQLite measuring (approximated) path coverage.
    """
    
    def __init__(self, 
                 target_sqlite_paths: List[str],
                 reference_sqlite_path: str,
                 total_trials: int,
                 timeout: int = 30):
        """
        Initialize the SQLite coverage runner.
        
        Args:
            target_sqlite_paths: Paths to the target SQLite executables
            reference_sqlite_path: Path to the reference SQLite executable
            total_trials: Total number of trials to run
            timeout: Timeout in seconds for the SQLite process
        """
        self.target_sqlite_paths = target_sqlite_paths
        self.reference_sqlite_path = reference_sqlite_path
        self.timeout = timeout
        self.console = Console()
        
        # Initialize stats for each target SQLite path
        self.stats = {}
        for path in self.target_sqlite_paths:
            self.stats[path] = {
                "PASS": 0,
                "CRASH": 0,
                "LOGIC_BUG": 0,
                "REFERENCE_ERROR": 0,
                "INVALID_QUERY": 0,
            }
        
        # For progress tracking
        self.start_time = None
        self.total_trials = total_trials
        self.current_trial = 0
        self.run_results = [] # Store the latest run results for display
        self.coverage = 0 # Store coverage information for display
        self.grammar_coverage = 0 # Store grammar coverage information for display
        self.live_display = None
        
        # Define outcome styling
        self.outcome_styles = {
            Outcome.PASS: "green",
            Outcome.CRASH: "red",
            Outcome.LOGIC_BUG: "red",
            Outcome.REFERENCE_ERROR: "yellow",
            Outcome.INVALID_QUERY: "blue",
        }
        
    def _restore_database(self, db_path: str) -> bool:
        """
        Restore a database from its backup copy.
        
        Args:
            db_path: Path to the database to restore
            
        Returns:
            True if restoration was successful, False otherwise
        """
        base_name = os.path.basename(db_path)
        name_without_ext = os.path.splitext(base_name)[0]
        db_dir = os.path.dirname(db_path)
        backup_path = os.path.join(db_dir, f"{name_without_ext}_copy.db")
        
        if not os.path.exists(backup_path):
            return False
            
        try:
            # Replace the possibly corrupted database with its backup
            shutil.copy2(backup_path, db_path)
            return True
        except Exception:
            return False

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
        modified_query = "BEGIN TRANSACTION;\n" + sql_query + "\n;\nROLLBACK;"
        result = {
            'returncode': None,
            'stdout': None,
            'stderr': None,
            'coverage': None,
        }

        process = None
        try:
            process = subprocess.Popen(
                [sqlite_path, db_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            result['stdout'], result['stderr'] = process.communicate(input=modified_query, timeout=self.timeout)
            result['returncode'] = -1 if result['stderr'] else 0

        except subprocess.TimeoutExpired:
            # Make sure to kill the process if timeout occurs
            if process:
                # First try to terminate gracefully
                process.terminate()
                # Give it a moment to terminate
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate
                    process.kill()
                    process.wait()
                    
            result['returncode'] = -1
            result['stderr'] = f"Process timed out after {self.timeout} seconds"
            
            # Try to collect any output that might be available
            try:
                if process:
                    stdout, stderr = process.communicate(timeout=1)
                    if stdout:
                        result['stdout'] = stdout
                    if stderr:
                        result['stderr'] += "\n" + stderr
            except:
                pass  # Ignore any errors in collecting leftover output
                
        except Exception as e:
            # Make sure to kill the process in case of any other exception
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=1)
                except:
                    # Force kill if needed
                    try:
                        process.kill()
                        process.wait()
                    except:
                        pass  # Last resort, ignore errors
                        
            result['returncode'] = -1
            result['stderr'] = str(e)
                
        finally:
            # Final cleanup to ensure process is terminated
            if process and process.poll() is None:
                try:
                    process.kill()
                    process.wait()
                except:
                    pass  # Ignore errors in final cleanup
                    
        return result
    
    def _normalize_output(self, output: str, query: str) -> str:
        """
        Normalize output to handle floating point differences, whitespace variations, and other differences.
        
        Args:
            output: Raw SQLite output
            query: The SQL query that produced the output
            
        Returns:
            Normalized output
        """
        lines = output.split('\n')
        
        # If no content at all, return empty string
        if not lines:
            return ""
        
        normalized_lines = []
        
        for line in lines:
            # Handle completely empty lines as separate case
            if not line.strip():
                normalized_lines.append("")
                continue
                
            # Split by pipe and handle each part
            parts = line.split('|')
            normalized_parts = []
            
            for part in parts:
                # Strip extra whitespace from each part
                part_stripped = part.strip()
                
                try:
                    # Check if it's a number (float or int)
                    float_val = float(part_stripped)
                    
                    # Only keep 8 decimal places for floats
                    normalized_parts.append(f"{float_val:.8f}")
                except ValueError:
                    normalized_parts.append(part_stripped)
            
            # Join parts with a consistent separator
            normalized_line = '|'.join(normalized_parts)
            normalized_lines.append(normalized_line)
        
        # Sort lines if "ORDER BY" is not in the query (case insensitive)
        if normalized_lines and "order by" not in query.lower():
            normalized_lines.sort()
        
        return '\n'.join(normalized_lines)
    
    def run(self, inp: Tuple[str, str]) -> Dict[str, RunResult]:
        """
        Run SQLite with the given input and compare with reference version.
        Restore database only if a true crash is detected (not for invalid queries).
        
        Args:
            inp: Tuple of (sql_query, db_path)
            
        Returns:
            A dict with target SQLite paths as keys and RunResult as values
        """
        try:
            sql_query, db_path = inp

            # Run on reference version
            reference_result = self._run_sqlite(self.reference_sqlite_path, sql_query, db_path)
            reference_sqlite_version = self.reference_sqlite_path.split('-')[-1] if '-' in self.reference_sqlite_path else "unknown"
            
            # Run on target versions
            run_results = {}
            for target_sqlite_path in self.target_sqlite_paths:
                target_result = self._run_sqlite(target_sqlite_path, sql_query, db_path)
                target_sqlite_version = target_sqlite_path.split('-')[-1] if '-' in target_sqlite_path else "unknown"
            
                # Determine outcome based on:
                # CRASH: target crashed (non-zero return code) AND reference did not crash (return code is 0)
                # LOGIC_BUG: both target and reference did not crash (return code 0) AND results differ
                # REFERENCE_ERROR: target did not crash (return code 0) AND reference crashed (non-zero return code)
                # INVALID_QUERY: both target and reference crashed (non-zero return code)
                # PASS: both target and reference did not crash (return code 0) AND results match
                
                target_crashed = target_result['returncode'] != 0
                reference_crashed = reference_result['returncode'] != 0
                
                if target_crashed and not reference_crashed:
                    # Target crashed, reference succeeded - this is a true crash, restore the database
                    err_msg = target_result['stderr']
                    match_unsupported = re.search(r"(not currently supported)", err_msg)
                    match_syntax_error = re.search(r"(syntax error)", err_msg)
                    match_no_such_function = re.search(r"(no such function)", err_msg)
                    match_parse_error = re.search(r"(Parse error)", err_msg)
                    match_no_query_solution = re.search(r"(no query solution)", err_msg) and "INDEXED BY" in sql_query
                    should_ignore = (match_unsupported or match_syntax_error or match_no_such_function or match_parse_error or match_no_query_solution)
                    if should_ignore:
                        outcome = Outcome.INVALID_QUERY
                    else:
                        outcome = Outcome.CRASH
                        self._restore_database(db_path)
                elif not target_crashed and reference_crashed:
                    # Target succeeded, reference crashed
                    err_msg = reference_result['stderr']
                    match_unsupported = re.search(r"(not currently supported)", err_msg)
                    match_syntax_error = re.search(r"(syntax error)", err_msg)
                    match_no_such_function = re.search(r"(no such function)", err_msg)
                    match_parse_error = re.search(r"(Parse error)", err_msg)
                    match_no_query_solution = re.search(r"(no query solution)", err_msg) and "INDEXED BY" in sql_query
                    should_ignore = (match_unsupported or match_syntax_error or match_no_such_function or match_parse_error or match_no_query_solution)
                    if should_ignore:
                        outcome = Outcome.INVALID_QUERY
                    else: 
                        outcome = Outcome.REFERENCE_ERROR
                    self._restore_database(db_path)
                elif not target_crashed and not reference_crashed:
                    # Both succeeded, compare outputs
                    normalized_output_target = self._normalize_output(target_result['stdout'], sql_query)
                    normalized_output_reference = self._normalize_output(reference_result['stdout'], sql_query)

                    if normalized_output_target != normalized_output_reference:
                        outcome = Outcome.LOGIC_BUG
                    else:
                        outcome = Outcome.PASS
                else:
                    # Both crashed - this is an invalid query, not a true crash, do not restore
                    outcome = Outcome.INVALID_QUERY

                run_result = RunResult(
                    outcome=outcome,
                    sql_query=sql_query,
                    db_path=db_path,
                    target_sqlite_version=target_sqlite_version,
                    target_result=target_result,
                    reference_sqlite_version=reference_sqlite_version,
                    reference_result=reference_result)
                
                run_results[target_sqlite_path] = run_result

            # Add coverage information to all RunResult.target_result
            # Note: We need to do this after all runs to make sure that the gcov files were updated (/home/test/sqlite/sqlite-3.26.0 needs to be run)
            coverage_percentage = read_gcov_coverage_percentage()
            for target_sqlite_path in self.target_sqlite_paths:
                run_result = run_results[target_sqlite_path]
                run_result.target_result['coverage'] = coverage_percentage

            # Note: This must be after read_gcov_coverage_percentage is called so .gcov files are updated
            coverage = read_gcov_coverage(c_file="/home/test/sqlite/sqlite3.c")
                
            return run_results, coverage
        finally:
            self.cleanup_resources()
    
    def start_fuzzing_session(self):
        """Start a new fuzzing session."""
        self.start_time = time.time()
        self.current_trial = 0
        self.run_results = []
        
        # Reset stats for each target
        for path in self.target_sqlite_paths:
            for outcome in self.stats[path]:
                self.stats[path][outcome] = 0

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
        """Generate a progress display layout with fixed size stats/results and collapsible trials."""
        # Create main layout
        layout = Layout()
        
        # Add padding at the top of the layout to prevent display cut-off when terminal shifts
        layout.split(
            Layout(name="padding", size=1),  # Fixed size top padding (1 line to prevent cut-off when terminal shifts after completion)
            Layout(name="content")  # Main content
        )
        
        # Split the main content into two sections - top section with fixed sizing and bottom section that can collapse
        layout["content"].split(
            Layout(name="fixed_panels", ratio=1, minimum_size=13),  # Fixed minimum size for stats/results
            Layout(name="trials", ratio=2, minimum_size=3)  # Collapsible section with minimum height
        )
        
        # Split the fixed panels section into stats and results
        layout["content"]["fixed_panels"].split_row(
            Layout(name="stats", ratio=1, minimum_size=45),  # Fixed minimum width for stats
            Layout(name="results", ratio=2, minimum_size=50)  # Fixed minimum width for results
        )
        
        # Add whitespace padding at the top
        layout["padding"].update("\n")

        # Write stats to JSON file periodically
        if self.current_trial > 0:
            # For the first 1000 queries, write every 100 queries
            # After 1000 queries, write every 1000 queries
            if (self.current_trial < 1000 and self.current_trial % 100 == 0) or \
               (self.current_trial >= 1000 and self.current_trial % 1000 == 0):
                self._write_stats_to_json()
        
        # Create the stats part with fixed size, including target and reference information
        if self.start_time:
            elapsed = time.time() - self.start_time
            trials_per_sec = self._calculate_rate()
            
            # Add target versions information
            target_versions = []
            for path in self.target_sqlite_paths:
                version = path.split('-')[-1] if '-' in path and path.split('-')[-1] else 'unknown'
                target_versions.append(f"{version}")
            
            # Add reference version information
            ref_version = self.reference_sqlite_path.split('-')[-1] if '-' in self.reference_sqlite_path and self.reference_sqlite_path.split('-')[-1] else 'unknown'
            
            stats_text = (
                f"[bold]FuzzQLite - SQLite Fuzzer[/]\n\n"
                f"[bold]Target:[/] {', '.join(target_versions)}\n"
                f"[bold]Reference:[/] {ref_version}\n\n"
                f"[bold]Progress:[/] {self.current_trial}/{self.total_trials} ({self.current_trial/self.total_trials*100:.1f}%)\n"
                f"[bold]Stmt Coverage:[/] {f'{self.coverage:.2f}%' if isinstance(self.coverage, (int, float)) else self.coverage}\n"
                f"[bold]Grammar Coverage:[/] {f'{self.grammar_coverage:.2f}%' if isinstance(self.grammar_coverage, (int, float)) else self.grammar_coverage}\n"
                f"[bold]Time:[/] {self._format_time(elapsed)}\n"
                f"[bold]Speed:[/] {trials_per_sec:.2f} queries/s (per version)\n"
                f"[bold]ETA:[/] {self._estimate_completion()}"
            )
            stats_panel = Panel(
                stats_text,
                title="Stats",
                border_style="blue",
                padding=(0, 1),
            )
            layout["content"]["fixed_panels"]["stats"].update(stats_panel)
        else:
            layout["content"]["fixed_panels"]["stats"].update(Panel("Starting...", title="FuzzQLite"))
        
        # Create compact results display for all targets in one panel with fixed size
        results_table = Table(box=rich.box.SIMPLE, padding=(0, 1), collapse_padding=True)
        results_table.add_column("TARGET", style="bold")
        
        # Add outcome columns with full names
        outcomes = ["PASS", "CRASH", "LOGIC_BUG", "REFERENCE_ERROR", "INVALID_QUERY"]
        outcome_styles = {
            "PASS": "green",
            "CRASH": "red",
            "LOGIC_BUG": "red",
            "REFERENCE_ERROR": "yellow",
            "INVALID_QUERY": "blue",
        }
        
        for outcome in outcomes:
            results_table.add_column(outcome, style=outcome_styles.get(outcome, "default"))
        
        # Add a row for each target
        for target_path in self.target_sqlite_paths:
            version = target_path.split('-')[-1] if '-' in target_path else "unknown"
            version_stats = self.stats[target_path]
            
            row_data = [version]
            total_version_trials = sum(version_stats.values())
            
            for outcome in outcomes:
                count = version_stats.get(outcome, 0)
                percentage = (count / total_version_trials) * 100 if total_version_trials > 0 else 0
                row_data.append(f"{count} ({percentage:.1f}%)")
            
            results_table.add_row(*row_data)
        
        layout["content"]["fixed_panels"]["results"].update(Panel(results_table, title="Results", border_style="green", padding=(0, 1)))
        
        # Create the recent trials list (collapsible)
        if self.run_results:
            # Get the last 20 results
            recent_results = self.run_results[-20:]
            
            # Calculate available width for query display based on terminal size
            # Use the console's width or fallback to a reasonable default
            console_width = self.console.width if hasattr(self.console, 'width') else 100
            # Account for panel borders, padding, and prefix text (outcome and version info)
            # Prefix is typically like "[red]✗ CRASH[/] (v1): " which is roughly 25 chars with styling
            available_width = max(30, console_width - 30)  # Ensure at least 30 chars for the query
            
            result_lines = []
            for result_entry in recent_results:
                target_path, result = result_entry
                version = target_path.split('-')[-1] if '-' in target_path else "unknown"
                
                outcome = result.outcome
                sql_query = result.sql_query
                
                # Truncate long queries based on available width
                query = sql_query.strip()
                if len(query) > available_width:
                    query = query[:available_width - 3] + "..."
                    
                # Format with emoji
                emoji = "✓" if outcome == Outcome.PASS else "✗"
                style = self.outcome_styles.get(outcome, "default")
                
                result_line = f"[{style}]{emoji} {outcome[:5]}[/] ({version}): {query}"
                result_lines.append(result_line)
                
                # Only add error details for crashes
                if outcome == Outcome.CRASH:
                    target_stderr = result.target_result.get('stderr', '')
                    if target_stderr:
                        # Get just the first line of the error
                        error_line = target_stderr.strip().split('\n')[0]
                        if len(error_line) > available_width:
                            error_line = error_line[:available_width - 3] + "..."
                        result_lines.append(f"  └─ {error_line}")
            
            results_text = "\n".join(result_lines)
            layout["content"]["trials"].update(Panel(results_text, title="Recent Trials", border_style="yellow", padding=(0, 1)))
        else:
            layout["content"]["trials"].update(Panel("No results yet", title="Recent Trials"))
        
        return layout
    
    def _write_stats_to_json(self):
        """Write current stats to a JSON file."""
        import json
        import os
        from datetime import datetime
        
        # Create stats directory if it doesn't exist
        stats_dir = os.path.join("/app/databases")
        os.makedirs(stats_dir, exist_ok=True)
        
        # Generate timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stats_{timestamp}_{self.current_trial}.json"
        filepath = os.path.join(stats_dir, filename)
        
        # Prepare stats data
        if self.start_time:
            elapsed = time.time() - self.start_time
            trials_per_sec = self._calculate_rate()
        else:
            elapsed = 0
            trials_per_sec = 0
        
        # Get target versions
        target_versions = []
        for path in self.target_sqlite_paths:
            version = path.split('-')[-1] if '-' in path and path.split('-')[-1] else 'unknown'
            target_versions.append(version)
        
        # Get reference version
        ref_version = self.reference_sqlite_path.split('-')[-1] if '-' in self.reference_sqlite_path and self.reference_sqlite_path.split('-')[-1] else 'unknown'
        
        # Build stats dictionary
        stats_data = {
            "timestamp": datetime.now().isoformat(),
            "current_trial": self.current_trial,
            "total_trials": self.total_trials,
            "progress_percentage": round(self.current_trial/self.total_trials*100, 1),
            "elapsed_seconds": elapsed,
            "elapsed_formatted": self._format_time(elapsed),
            "queries_per_second": round(trials_per_sec, 2),
            "coverage": self.coverage,
            "grammar_coverage": self.grammar_coverage,
            "target_versions": target_versions,
            "reference_version": ref_version,
            "results": {}
        }
        
        # Add detailed results for each target
        for target_path in self.target_sqlite_paths:
            version = target_path.split('-')[-1] if '-' in target_path else "unknown"
            version_stats = self.stats[target_path]
            
            total_version_trials = sum(version_stats.values())
            stats_data["results"][version] = {
                "total_trials": total_version_trials,
                "outcomes": {}
            }
            
            # Add counts and percentages for each outcome
            for outcome, count in version_stats.items():
                percentage = (count / total_version_trials) * 100 if total_version_trials > 0 else 0
                stats_data["results"][version]["outcomes"][outcome] = {
                    "count": count,
                    "percentage": round(percentage, 1)
                }
        
        # Write to JSON file
        with open(filepath, 'w') as f:
            json.dump(stats_data, f, indent=2)
    
    def record_results(self, run_results: Dict[str, RunResult], bug_tracker: BugTracker, grammar_coverage: float) -> None:
        """
        Record RunResults and update the display accordingly.
        
        Args:
            run_results: Dictionary of RunResults keyed by target SQLite path
            bug_tracker: Bug tracker for saving reproducers
            grammar_coverage: Coverage percentage from the grammar-based query generator
        """
        self.current_trial += 1
        
        values_list = list(run_results.values())
        coverage = values_list[0].target_result['coverage'] if values_list else None
        self.coverage = coverage if coverage is not None else "N/A"
        self.grammar_coverage = "N/A [Still seeding...]" if grammar_coverage == 0.0 else grammar_coverage if grammar_coverage is not None else "N/A" 
        
        # Process each target's result
        for target_path, run_result in run_results.items():
            # Update stats for this target
            outcome = run_result.outcome
            self.stats[target_path][outcome] = self.stats[target_path].get(outcome, 0) + 1
            
            # Store recent results for display
            # We'll store tuples of (target_path, run_result) to track which target produced which result
            self.run_results.append((target_path, run_result))
            
            # Handle bug saving for reproducibility
            if outcome in (Outcome.CRASH, Outcome.LOGIC_BUG, Outcome.REFERENCE_ERROR):
                bug_dir = bug_tracker.save_reproducer(
                    bug_type=outcome,
                    sql_query=run_result.sql_query,
                    db_path=run_result.db_path,
                    target_sqlite_version=run_result.target_sqlite_version,
                    target_result=run_result.target_result,
                    reference_sqlite_version=run_result.reference_sqlite_version,
                    reference_result=run_result.reference_result
                )
                # Set bug_dir directly on the result
                run_result.bug_dir = bug_dir
        
        # Keep only the most recent results for display (to avoid memory issues)
        max_results_to_keep = 50
        if len(self.run_results) > max_results_to_keep:
            self.run_results = self.run_results[-max_results_to_keep:]
            
        # Update the display
        if self.live_display:
            self.live_display.update(self._generate_progress_display())
    
    def finish_fuzzing_session(self) -> None:
        """Finish the fuzzing session and display final stats."""
        # Stop the live display
        if self.live_display:
            self.live_display.stop()

    def cleanup_resources(self):
        """
        Explicitly clean up resources to prevent memory leaks.
        """
        # Clear the run_results list if it's too large
        if hasattr(self, 'run_results') and len(self.run_results) > 100:
            # Keep only the most recent results
            self.run_results = self.run_results[-50:]
        
        # Force garbage collection
        gc.collect()
    
    def cleanup(self):
        """Clean up temporary directories."""
        if self.live_display:
            try:
                self.live_display.stop()
            except:
                pass
