import argparse
import sys
import os
from typing import List

# from fuzzer.greybox_fuzzer import GreyboxFuzzer
from fuzzer.counting_greybox_fuzzer import CountingGreyboxFuzzer

# from runner.sqlite_coverage_runner import SQLiteCoverageRunner
from runner.counting_sqlite_coverage_runner import CountingSQLiteCoverageRunner

# from mutator.sql_randomize_mutator import SQLRandomizeMutator
from mutator.enhanced_sql_mutator import EnhancedSQLMutator
from mutator.improved_mutator import ImprovedMutator

from utils.generator.query_generator import QueryGenerator
from utils.generator.db_generator import DBGenerator
from utils.generator.seed_generator import SeedGenerator

# from utils.power_schedule import PowerSchedule
from utils.afl_fast_schedule import AFLFastSchedule
from utils.grammar import USE_NAMES_BNF_SQL_GRAMMAR, trim_grammar

# from fuzzer.grammar_fuzzer import GrammarFuzzer
# from fuzzer.generator_grammar_fuzzer import GeneratorGrammarFuzzer
# from fuzzer.grammar_coverage_fuzzer import GrammarCoverageFuzzer
# from fuzzer.probabilistic_grammar_coverage_fuzzer import ProbabilisticGrammarCoverageFuzzer
from fuzzer.pggc_fuzzer import PGGCFuzzer


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
    
    # Initialize Table Generation Fuzzer
    # create_table_fuzzer = GeneratorGrammarFuzzer(
    #     grammar=trim_grammar(SAVE_NAMES_CREATE_TABLE_BNF_SQL_GRAMMAR),
    #     start_symbol="<start>",
    #     min_nonterminals=0,
    #     max_nonterminals=10,
    #     # disp=True,
    #     # log=True,
    # )

    # Initialize Random Query Generator Fuzzer which creates queries containing the same
    # table names, column names, etc. as used in the Table Generation Fuzzer
    
    # Generate databases
    db_generator = DBGenerator(db_dir=parsed_args.databases_dir)
    db_paths = db_generator.generate_databases()

    # Generate queries
    query_generator = QueryGenerator()
    seed_queries = query_generator.generate_queries()

    # Generate seed pairs (SQL query, database path)
    seed_generator = SeedGenerator()
    seeds = seed_generator.generate_seed(
        sql_queries=seed_queries,
        db_paths=db_paths
    )

    # Create a runner for SQLite
    # runner = SQLiteCoverageRunner(
    #     target_sqlite_paths=TARGET_SQLITE_PATHS,
    #     reference_sqlite_path=REFERENCE_SQLITE_PATH,
    #     total_trials=parsed_args.trials,
    #     timeout=3
    # )

    runner = CountingSQLiteCoverageRunner(
        target_sqlite_paths=TARGET_SQLITE_PATHS,
        reference_sqlite_path=REFERENCE_SQLITE_PATH,
        total_trials=parsed_args.trials,
        timeout=3
    )

    # min_nonterminals = 0
    # max_nonterminals = 30
    # Coverage: 48.11% after 20,000 queries (Time: 1:33:03)
    query_fuzzer = PGGCFuzzer(
        grammar=trim_grammar(USE_NAMES_BNF_SQL_GRAMMAR),
        start_symbol="<start>",
        min_nonterminals=0,
        max_nonterminals=30,
        # disp=True,
        # log=True,
    )

    # fuzzer = GreyboxFuzzer(
    #     seeds=seeds,
    #     output_dir=parsed_args.output_dir,
    #     schedule=PowerSchedule(),
    #     query_fuzzer=query_fuzzer,
    #     mutators=[EnhancedSQLMutator(), ImprovedMutator()],
    #     min_mutations=1,
    #     max_mutations=1 # FIXME: Currently just one consecutive mutation is done
    # )

    fuzzer = CountingGreyboxFuzzer(
        seeds=seeds,
        output_dir=parsed_args.output_dir,
        schedule=AFLFastSchedule(exponent=5),
        query_fuzzer=query_fuzzer,
        mutators=[ImprovedMutator()], # EnhancedSQLMutator()
        min_mutations=1,
        max_mutations=3
    )
    
    # Run the fuzzer
    fuzzer.runs(runner=runner, trials=parsed_args.trials)
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
    