import argparse
import sys
import os
from typing import List

from fuzzer import MutationFuzzer
from runner import SQLiteRunner
from utils import QueryGenerator, DBGenerator, BugTracker
# from mutator import IdentityMutation
from mutator import SQLRandomizeMutation


# Available SQLite versions for testing
SQLITE_VERSIONS = {
    "3.26.0": "/usr/bin/sqlite3-3.26.0",
    "3.39.4": "/usr/bin/sqlite3-3.39.4"
}

# Reference SQLite version
REFERENCE_SQLITE = "/usr/bin/sqlite3-3.49.1"


def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="FuzzQLite - SQLite Fuzzer")
    
    parser.add_argument(
        "--version",
        choices=list(SQLITE_VERSIONS.keys()),
        default="3.26.0",
        help="SQLite version to test (default: 3.26.0)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--trials",
        type=int,
        default=10,
        help="Number of fuzzing trials to run (default: 10)"
    )
    
    parser.add_argument(
        "--bugs-dir",
        default="bug_reproducers",
        help="Directory to save bug reproducers (default: bug_reproducers)"
    )
    
    parser.add_argument(
        "--databases-dir",
        default="databases",
        help="Directory for generated databases (default: databases)"
    )
    
    parser.add_argument(
        "--regenerate-dbs",
        action="store_true",
        help="Regenerate the database files"
    )
    
    return parser.parse_args(args)


def main(args: List[str] = None) -> int:
    """
    Main entry point for FuzzQLite.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    # Check if the selected SQLite version exists
    target_sqlite_path = SQLITE_VERSIONS[parsed_args.version]
    if not os.path.exists(target_sqlite_path):
        print(f"Error: SQLite binary not found at {target_sqlite_path}")
        return 1
        
    # Check if the reference SQLite version exists
    if not os.path.exists(REFERENCE_SQLITE):
        print(f"Error: Reference SQLite binary not found at {REFERENCE_SQLITE}")
        return 1
    
    # Generate or regenerate databases
    db_generator = DBGenerator(db_dir=parsed_args.databases_dir)
    
    # Check if databases need to be generated
    db_files = []
    if os.path.exists(parsed_args.databases_dir):
        db_files = [f for f in os.listdir(parsed_args.databases_dir) if f.endswith('.db')]
    
    if parsed_args.regenerate_dbs or not db_files:
        db_paths = db_generator.generate_databases()
    else:
        db_paths = [
            os.path.join(parsed_args.databases_dir, db_file)
            for db_file in db_files
        ]

    # Generate seed corpus
    query_generator = QueryGenerator()
    seed_queries = query_generator.generate_seed_queries()
    
    # Create a runner with improved display
    runner = SQLiteRunner(
        target_sqlite_path=target_sqlite_path,
        reference_sqlite_path=REFERENCE_SQLITE
    )
    
    # Create a bug tracker to save reproducers
    bug_tracker = BugTracker(output_dir=parsed_args.bugs_dir)
    
    # Create the fuzzer
    fuzzer = MutationFuzzer(
        seed=parsed_args.seed,
        mutations=[SQLRandomizeMutation()], # IdentityMutation()
        db_paths=db_paths
    )

    # Load the corpus
    fuzzer.load_corpus(seed_queries)
    
    try:
        # Start the fuzzing session with real-time display
        runner.start_fuzzing_session(
            total_trials=parsed_args.trials,
            version=parsed_args.version
        )
        
        # Run the fuzzer iteratively to update display in real-time
        for _ in range(parsed_args.trials):
            # Get the next input
            input_data = fuzzer.fuzz()
            
            # Run the input and get result
            result = runner.run(input_data)
            
            # Record the result with bug tracking
            runner.record_result(result, bug_tracker=bug_tracker)
            
        # Finish the fuzzing session with final stats
        runner.finish_fuzzing_session(bug_tracker=bug_tracker)
        
    except KeyboardInterrupt:
        print("\nFuzzing interrupted by user.")
        # Still show summary of findings so far
        runner.finish_fuzzing_session(bug_tracker=bug_tracker)
    finally:
        # Cleanup resources
        runner.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
    