#!/usr/bin/env python3

import argparse
import sys
import os
import random
from typing import List

# Focus on maximizing SQLite3 source code path coverage
from fuzzer.greybox_path_coverage_fuzzer import GreyboxPathCoverageFuzzer
from runner.sqlite_path_coverage_runner import SQLitePathCoverageRunner
from fuzzer.utils.afl_fast_schedule import AFLFastSchedule

# Focus on maximizing SQLite3 source code stmt coverage (more speed)
from fuzzer.greybox_stmt_coverage_fuzzer import GreyboxStmtCoverageFuzzer
from runner.sqlite_stmt_coverage_runner import SQLiteStmtCoverageRunner
from fuzzer.utils.power_schedule import PowerSchedule

from mutator.improved_mutator import ImprovedMutator

from generator.schema_based.schema_query_generator import SchemaQueryGenerator
from generator.schema_based.db_generator import DBGenerator
from generator.schema_based.seed_generator import SeedGenerator

from generator.grammar_based.utils.grammar import USE_NAMES_BNF_SQL_GRAMMAR, trim_grammar

# Focus on maximizing SQLite3 grammar coverage
from generator.grammar_based.pggc_query_generator import PGGCQueryGenerator

# Focus on fast generation
from generator.grammar_based.pre_post_grammar_query_generator import PrePostGrammarQueryGenerator


TARGET_SQLITE_PATHS = [
    "/home/test/sqlite/sqlite3-3.26.0", # Keep this first so it will be used first. This ensures that the gcov coverage is updated.
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
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--trials",
        type=positive_int,
        default=1000,
        help="Number of fuzzing trials to run (default: 1000)"
    )

    parser.add_argument(
        "--path-coverage",
        action="store_true",
        help="Maximize source code path coverage (if not set, statement coverage is used)"
    )
    
    parser.add_argument(
        "--grammar-coverage",
        action="store_true",
        help="Maximize SQLite grammar coverage (if not set, grammar coverage is not used)"
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

    # Set global random seed if provided
    if parsed_args.seed is not None:
        random.seed(parsed_args.seed)

    # Check if all target SQLite paths exist
    for sqlite_path in TARGET_SQLITE_PATHS:
        if not os.path.exists(sqlite_path):
            print(f"Error: Target SQLite binary not found at {sqlite_path}")
            return 1
    
    # Check if reference SQLite path exists
    if not os.path.exists(REFERENCE_SQLITE_PATH):
        print(f"Error: Reference SQLite binary not found at {REFERENCE_SQLITE_PATH}")
        return 1
    
    ########################### Generate initial seed for mutator ###########################
    # Generate databases (tables, columns, etc.)
    db_generator = DBGenerator(db_dir="databases")
    db_paths = db_generator.generate_databases()

    # Generate seed queries based on the generated databases
    query_generator = SchemaQueryGenerator()
    seed_queries = query_generator.generate_queries()

    # Generate seed pairs (SQL query, database path)
    seed_generator = SeedGenerator()
    seeds = seed_generator.generate_seed(
        sql_queries=seed_queries,
        db_paths=db_paths
    )

    ########################### Initialize runner and fuzzer #############################
    runner = None
    fuzzer = None

    # Create the runner for SQLite
    if parsed_args.path_coverage:
        grammar_based_query_generator = None

        runner = SQLitePathCoverageRunner(
            target_sqlite_paths=TARGET_SQLITE_PATHS,
            reference_sqlite_path=REFERENCE_SQLITE_PATH,
            total_trials=parsed_args.trials,
            timeout=1
        )

        if parsed_args.grammar_coverage:
            grammar_based_query_generator = PGGCQueryGenerator(
                grammar=trim_grammar(USE_NAMES_BNF_SQL_GRAMMAR),
                start_symbol="<start>",
                min_nonterminals=0,
                max_nonterminals=30
            )
        else:
            grammar_based_query_generator = PrePostGrammarQueryGenerator(
                grammar=trim_grammar(USE_NAMES_BNF_SQL_GRAMMAR),
                start_symbol="<start>",
                min_nonterminals=0,
                max_nonterminals=30
            )

        fuzzer = GreyboxPathCoverageFuzzer(
            seeds=seeds,
            schedule=AFLFastSchedule(exponent=5),
            query_generator=grammar_based_query_generator,
            mutators=[ImprovedMutator()],
            min_mutations=1,
            max_mutations=1
        )
    else:
        grammar_based_query_generator = None

        runner = SQLiteStmtCoverageRunner(
            target_sqlite_paths=TARGET_SQLITE_PATHS,
            reference_sqlite_path=REFERENCE_SQLITE_PATH,
            total_trials=parsed_args.trials,
            timeout=1
        )

        if parsed_args.grammar_coverage:
            grammar_based_query_generator = PGGCQueryGenerator(
                grammar=trim_grammar(USE_NAMES_BNF_SQL_GRAMMAR),
                start_symbol="<start>",
                min_nonterminals=0,
                max_nonterminals=30
            )
        else:
            grammar_based_query_generator = PrePostGrammarQueryGenerator(
                grammar=trim_grammar(USE_NAMES_BNF_SQL_GRAMMAR),
                start_symbol="<start>",
                min_nonterminals=0,
                max_nonterminals=30
            )

        fuzzer = GreyboxStmtCoverageFuzzer(
            seeds=seeds,
            schedule=PowerSchedule(),
            query_generator=grammar_based_query_generator,
            mutators=[ImprovedMutator()],
            min_mutations=1,
            max_mutations=1
        )
    
    ##################################### Run the fuzzer ######################################
    fuzzer.runs(runner=runner, trials=parsed_args.trials)
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
    