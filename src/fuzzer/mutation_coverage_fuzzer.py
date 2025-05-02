import random
from typing import List, Optional, Tuple, Dict, Set

from runner.sqlite_coverage_runner import SQLiteCoverageRunner
from runner.outcome import Outcome
from runner.run_result import RunResult

from mutator.mutator import Mutator
from mutator.identity_mutator import IdentitiyMutator

from utils.bug_tracker import BugTracker
from utils.coverage import Location

class MutationCoverageFuzzer:
    """
    A coverage-based fuzzer that mutates existing inputs to generate new test cases.
    """
    
    def __init__(self, seed: List[Tuple[str, str]],
                 output_dir: str,
                 mutators: Optional[List[Mutator]] = [IdentitiyMutator()],
                 min_mutations: int = 1,
                 max_mutations: int = 10) -> None:
        """
        Initialize the coverage-based mutation fuzzer.
        
        Args:
            seed: List of (sql_query, db_path) pairs to mutate
            output_dir: Directory to save the bug reproducers
            mutators: List of mutator to use
            min_mutations: Minimum number of mutations to apply
            max_mutations: Maximum number of mutations to apply
        """
        self.seed = seed
        self.bug_tracker = BugTracker(output_dir=output_dir) # Create a bug tracker to save reproducers
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
    
    def update_population(self, run_results: Dict[str, RunResult], new_coverage: Set[Location]) -> None:
        """
        Update the population with new inputs if:
        1. The outcome is PASS and
        2. The coverage is increased
        """
        new_coverage = frozenset(new_coverage)

        addToPopulation = False
        for run_result in run_results.values():
            # FIXME: Currently it is added if it is a PASS for at least one target.
            # Might change this such that it is added iff it is a PASS for all targets
            if run_result.outcome == Outcome.PASS and new_coverage not in self.coverages_seen:
                addToPopulation = True
                break
        
        if addToPopulation:
            self.population.append(self.inp)
            self.coverages_seen.add(new_coverage)
    
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
    
    def run(self, runner: SQLiteCoverageRunner) -> Tuple[Dict[str, RunResult], Set[Location]]:
        """Run `runner` with fuzz input"""
        return runner.run(self.fuzz())

    def runs(self, runner: SQLiteCoverageRunner, trials: int = 10) -> None:
        try:
            # Start the fuzzing session with real-time display
            runner.start_fuzzing_session()
            
            # Run the fuzzer iteratively to update display in real-time
            for _ in range(trials):
                # Run the input on all target SQLite binaries
                run_results, new_coverage = self.run(runner)

                # Update the population
                self.update_population(run_results, new_coverage)
                
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
        self.population = []
        self.seed_index = 0
        self.coverages_seen: Set[frozenset] = set()
