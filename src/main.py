#!/usr/bin/env python3
"""
SQLite Fuzzer Main Entry Point

This script serves as the entry point for the SQLite fuzzer application
designed to test different versions of SQLite (3.26.0 and 3.39.4) against
the latest version to identify crashes and logic bugs.
"""

import argparse
import sys
import os
from typing import List, Dict, Any

from fuzzer.mutation_fuzzer import MutationFuzzer
from fuzzer.generation_fuzzer import GenerationFuzzer
from utils.sqlite_runner import SQLiteRunner, SQLiteOutcome
from mutations.dummy_mutation import CapitalizeMutation
from mutations.sql_mutations import SQLRandomizeMutation

from utils.base_runner import PrintRunner

# Available SQLite versions for testing
SQLITE_VERSIONS = {
    "3.26.0": "/usr/bin/sqlite3-3.26.0",
    "3.39.4": "/usr/bin/sqlite3-3.39.4"
}

# Reference SQLite version
REFERENCE_SQLITE = "/usr/bin/sqlite3-latest"


def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="SQLite Fuzzer for academic project")
    
    parser.add_argument(
        "--mode",
        choices=["mutation", "generation"],
        default="mutation",
        help="Fuzzing mode (default: mutation)"
    )
    
    parser.add_argument(
        "--version",
        choices=list(SQLITE_VERSIONS.keys()),
        default="3.26.0",
        help="SQLite version to test (default: 3.26.0)"
    )
    
    parser.add_argument(
        "--db-path",
        default=":memory:",
        help="Path to the database file (default: :memory:)"
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
        "--corpus",
        nargs="+",
        default=["SELECT * FROM sqlite_master;", 
                 "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT);",
                 "INSERT INTO test VALUES (1, 'test');",
                 "SELECT * FROM test;"],
        help="Initial corpus of SQL inputs"
    )
    
    return parser.parse_args(args)


def main(args: List[str] = None) -> int:
    """
    Main entry point for the SQLite fuzzer.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    # Check if the selected SQLite version exists
    sqlite_path = SQLITE_VERSIONS[parsed_args.version]
    if not os.path.exists(sqlite_path):
        print(f"Error: SQLite binary not found at {sqlite_path}")
        return 1
        
    # Check if the reference SQLite version exists
    if not os.path.exists(REFERENCE_SQLITE):
        print(f"Error: Reference SQLite binary not found at {REFERENCE_SQLITE}")
        return 1
    
    # Create a runner
    # runner = SQLiteRunner(
    #     sqlite_path=sqlite_path,
    #     reference_sqlite_path=REFERENCE_SQLITE,
    #     db_path=parsed_args.db_path
    # )
    runner = PrintRunner()
    
    # Create a fuzzer based on the selected mode
    if parsed_args.mode == "mutation":
        fuzzer = MutationFuzzer(
            seed=parsed_args.seed,
            # mutations=[CapitalizeMutation(), SQLRandomizeMutation()]
        )
    else:  # generation mode
        fuzzer = GenerationFuzzer(seed=parsed_args.seed)
    
    # Load the corpus
    fuzzer.load_corpus(parsed_args.corpus)
    
    # Run the fuzzer
    results = fuzzer.runs(runner=runner, trials=parsed_args.trials)
    
    # Track statistics
    stats = {
        "PASS": 0,
        "FAIL": 0,
        "CRASH": 0,
        "LOGIC_BUG": 0,
        "UNRESOLVED": 0
    }
    
    # Print results
    print(f"\nTesting SQLite version {parsed_args.version} ({sqlite_path})")
    print(f"Reference version: {REFERENCE_SQLITE}\n")
    
    for i, (process, outcome) in enumerate(results):
        stats[outcome] = stats.get(outcome, 0) + 1
        
        print(f"Trial {i+1}: {outcome}")
        
        # Print additional information based on outcome
        if outcome == SQLiteOutcome.CRASH:
            print(f"  CRASH detected!")
            print(f"  Stderr: {process.stderr}")
        elif outcome == SQLiteOutcome.LOGIC_BUG:
            print(f"  LOGIC BUG detected!")
            print(f"  Target output: {process.stdout}")
            print(f"  Reference output: {process.reference_stdout}")
        elif outcome != SQLiteOutcome.PASS:
            print(f"  Stderr: {process.stderr}")
    
    # Print summary
    print("\nSummary:")
    for outcome, count in stats.items():
        if count > 0:
            print(f"  {outcome}: {count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
