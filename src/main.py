import argparse
import sys
import os
from typing import List

# from fuzzer.mutation_fuzzer import MutationFuzzer
from fuzzer.mutation_coverage_fuzzer import MutationCoverageFuzzer

# from runner.sqlite_runner import SQLiteRunner
from runner.sqlite_coverage_runner import SQLiteCoverageRunner

# from mutator.identity_mutator import IdentitiyMutator
from mutator.sql_randomize_mutator import SQLRandomizeMutator

from utils.generator.query_generator import QueryGenerator
from utils.generator.db_generator import DBGenerator
from utils.generator.seed_generator import SeedGenerator


# SQLITE_VERSIONS = {
#     "3.26.0": "/usr/bin/sqlite3-3.26.0",
#     "3.39.4": "/usr/bin/sqlite3-3.39.4"
# }

TARGET_SQLITE_PATHS = [
    "/usr/bin/sqlite3-3.26.0",
    "/usr/bin/sqlite3-3.39.4"
]

REFERENCE_SQLITE_PATH = "/usr/bin/sqlite3-3.49.1"

def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue

def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="FuzzQLite - SQLite Fuzzer")
    
    # parser.add_argument( # FIXME: Add this logic later
    #     "--version",
    #     choices=list(SQLITE_VERSIONS.keys()),
    #     default="3.26.0",
    #     help="SQLite version to test (default: 3.26.0)"
    # )
    
    parser.add_argument( # FIXME: Add this logic later
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--trials",
        type=positive_int,
        default=10,
        help="Number of fuzzing trials to run (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="bug_reproducers",
        help="Directory to save bug reproducers (default: bug_reproducers)"
    )
    
    parser.add_argument(
        "--databases-dir",
        default="databases",
        help="Directory for generated databases (default: databases)"
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

    # Check if all target SQLite paths exist
    for sqlite_path in TARGET_SQLITE_PATHS:
        if not os.path.exists(sqlite_path):
            print(f"Error: Target SQLite binary not found at {sqlite_path}")
            return 1
    
    # Check if reference SQLite path exists
    if not os.path.exists(REFERENCE_SQLITE_PATH):
        print(f"Error: Reference SQLite binary not found at {REFERENCE_SQLITE_PATH}")
        return 1
    
    # Generate databases
    db_generator = DBGenerator(db_dir=parsed_args.databases_dir)
    db_paths = db_generator.generate_databases()

    # Generate queries
    query_generator = QueryGenerator()
    seed_queries = query_generator.generate_queries()

    # Generate seed pairs (SQL query, database path)
    seed_generator = SeedGenerator()
    seed = seed_generator.generate_seed(
        sql_queries=seed_queries,
        db_paths=db_paths
    )

    # Create a runner for SQLite
    runner = SQLiteCoverageRunner(
        target_sqlite_paths=TARGET_SQLITE_PATHS,
        reference_sqlite_path=REFERENCE_SQLITE_PATH,
        total_trials=parsed_args.trials,
    )
    
    # Create the fuzzer
    fuzzer = MutationCoverageFuzzer(
        seed=seed,
        output_dir=parsed_args.output_dir,
        mutators=[SQLRandomizeMutator()], # IdentityMutation()
        min_mutations=1,
        max_mutations=1 # FIXME: For now, only do one mutation
    )
    
    # Run the fuzzer
    fuzzer.runs(runner=runner, trials=parsed_args.trials)
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
    