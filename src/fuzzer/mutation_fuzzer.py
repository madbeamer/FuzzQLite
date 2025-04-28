import random
from typing import List, Optional, Tuple, Dict

from runner.sqlite_runner import SQLiteRunner
from runner.run_result import RunResult

from mutator.mutator import Mutator
from mutator.identity_mutator import IdentitiyMutator

from utils.bug_tracker import BugTracker

class MutationFuzzer:
    """
    A fuzzer that mutates existing inputs to generate new test cases.
    """
    
    def __init__(self, seed: List[Tuple[str, str]],
                 output_dir: str,
                 mutators: Optional[List[Mutator]] = None,
                 min_mutations: int = 1,
                 max_mutations: int = 10) -> None:
        """
        Initialize the mutation fuzzer.
        
        Args:
            seed: List of (sql_query, db_path) pairs to mutate
            output_dir: Directory to save the bug reproducers
            mutators: List of mutator to use
            min_mutations: Minimum number of mutations to apply
            max_mutations: Maximum number of mutations to apply
        """
        self.seed = seed
        self.bug_tracker = BugTracker(output_dir=output_dir) # Create a bug tracker to save reproducers
        if mutators is None:
            self.mutators = [IdentitiyMutator()]
        else:
            self.mutators = mutators
        self.min_mutations = min_mutations
        self.max_mutations = max_mutations

        self.reset()

    def create_candidate(self) -> Tuple[str, str]:
        """Create a new candidate by mutating a population member"""
        candidate = random.choice(self.population)
        trials = random.randint(self.min_mutations, self.max_mutations)
        for _ in range(trials):
            mutator = random.choice(self.mutators)
            candidate = mutator.mutate(candidate)
        return candidate
    
    def fuzz(self) -> Tuple[str, str]:
        """
        Generate a fuzz input by mutating an item from the corpus.
        
        Returns:
            A tuple containing (mutated_sql_query, db_path)
        """
        if self.seed_index < len(self.seed):
            # Seeding
            self.inp = self.seed[self.seed_index]
            self.seed_index += 1
        else:
            # Mutating
            self.inp = self.create_candidate()
        
        return self.inp
    
    def run(self, runner: SQLiteRunner) -> Dict[str, RunResult]:
        """Run `runner` with fuzz input"""
        return runner.run(self.fuzz())

    def runs(self, runner: SQLiteRunner, trials: int = 10) -> None:
        try:
            # Start the fuzzing session with real-time display
            runner.start_fuzzing_session()
            
            # Run the fuzzer iteratively to update display in real-time
            for _ in range(trials):
                # Run the input on all target SQLite binaries
                run_results = self.run(runner)
                
                # Record the results with bug tracking
                runner.record_results(run_results=run_results, bug_tracker=self.bug_tracker)
                
            # Finish the fuzzing session with final stats
            runner.finish_fuzzing_session()
        except KeyboardInterrupt:
            print("\nFuzzing interrupted by user.")
            # Still show summary of findings so far
            runner.finish_fuzzing_session()
        finally:
            # Cleanup resources
            runner.cleanup()

    def reset(self) -> None:
        """Set population to initial seed."""
        self.population = self.seed
        self.seed_index = 0
