import random
from typing import List, Optional, Tuple, Dict, Set

from runner.sqlite_path_coverage_runner import SQLitePathCoverageRunner
from runner.utils.outcome import Outcome
from runner.utils.run_result import RunResult

from mutator.mutator import Mutator
from mutator.identity_mutator import IdentitiyMutator

from utils.bug_tracker import BugTracker
from fuzzer.utils.seed import Seed

from fuzzer.utils.afl_fast_schedule import AFLFastSchedule
from fuzzer.utils.power_schedule import getPathID

from generator.grammar_based.grammar_query_generator import GrammarQueryGenerator
from generator.grammar_based.pggc_query_generator import PGGCQueryGenerator


class GreyboxPathCoverageFuzzer:
    """
    A coverage-guided mutational fuzzer that counts how often individual paths are exercised.
    """
    
    def __init__(self, seeds: List[Tuple[str, str]],
                 schedule: AFLFastSchedule,
                 query_generator: GrammarQueryGenerator,
                 mutators: Optional[List[Mutator]] = [IdentitiyMutator()],
                 min_mutations: int = 1,
                 max_mutations: int = 10) -> None:
                
        """
        Initialize the coverage-based mutation fuzzer.
        
        Args:
            seeds: List of (sql_query, db_path) pairs to mutate
            schedule: Power schedule to use for selecting seeds
            query_generator: Grammar-based query generator to generate new queries
            mutators: List of mutator to use
            min_mutations: Minimum number of mutations to apply
            max_mutations: Maximum number of mutations to apply
        """
        self.seeds = seeds
        self.mutators = mutators
        self.min_mutations = min_mutations
        self.max_mutations = max_mutations
        self.schedule = schedule

        self.query_generator = query_generator
        self.times_to_mutate = random.randint(1, 10)
        self.times_to_query_gen = random.randint(1, 10)

        self.bug_tracker = BugTracker() # Create a bug tracker to save reproducers

        self.reset()

    def create_candidate(self) -> Tuple[str, str]:
        """Create a new candidate by mutating a population member"""
        seed = self.schedule.choose(self.population)
        candidate = seed.data
        trials = random.randint(self.min_mutations, self.max_mutations)
        for _ in range(trials):
            mutator = random.choice(self.mutators)
            candidate = mutator.mutate(candidate)
        return candidate
    
    def update_population(self, run_results: Dict[str, RunResult], path_id: str, is_new_path: bool) -> None:
        """
        Update the population with new seeds based on the run results.
        """
        for run_result in run_results.values():
            if run_result.outcome == Outcome.PASS and is_new_path:
            # FIXME: Currently it is added if it is a PASS for at least one target.
            # Might change this such that it is added iff it is a PASS for all targets
                seed = Seed(data=self.inp)
                seed.path_id = path_id
                self.population.append(seed)
                break
    
    def fuzz(self) -> Tuple[str, str]:
        """
        Generate a fuzz input by mutating an item from the corpus.
        
        Returns:
            A tuple containing (mutated_sql_query, db_path)
        """
        if self.seed_index < len(self.seeds):
            # Seeding
            self.inp = self.seeds[self.seed_index]
            self.seed_index += 1
        elif self.times_to_mutate > 0:
            # Mutating
            self.inp = self.create_candidate()
            self.times_to_mutate -= 1
        else:
            # Query generation
            query = self.query_generator.fuzz()
            db_path = random.choice(['databases/edge_cases.db', 'databases/small.db'])
            self.inp = (query, db_path)
            self.times_to_query_gen -= 1

            # Reset both counters
            if self.times_to_query_gen <= 0:
                self.times_to_query_gen = random.randint(1, 10)
                self.times_to_mutate = random.randint(1, 10)
        
        return self.inp
    
    def run(self, runner: SQLitePathCoverageRunner) -> Tuple[Dict[str, RunResult], Set[Tuple[str, int]]]:
        """Run `runner` with fuzz input"""
        return runner.run(self.fuzz())

    def runs(self, runner: SQLitePathCoverageRunner, trials: int) -> None:
        try:
            # Start the fuzzing session with real-time display
            runner.start_fuzzing_session()
            
            # Run the fuzzer iteratively to update display in real-time
            for _ in range(trials):
                # Run the input on all target SQLite binaries
                run_results, new_coverage = self.run(runner)

                # Update the path frequency
                is_new_path = False
                path_id = getPathID(new_coverage)
                if path_id not in self.schedule.path_frequency:
                    self.schedule.path_frequency[path_id] = 1
                    is_new_path = True
                else:
                    self.schedule.path_frequency[path_id] += 1

                # Update the population
                self.update_population(run_results, path_id, is_new_path)
                
                # Record the results with bug tracking
                grammar_coverage = None
                if isinstance(self.query_generator, PGGCQueryGenerator):
                    grammar_coverage = self.query_generator.get_grammar_coverage_percentage()
                runner.record_results(run_results=run_results, bug_tracker=self.bug_tracker, grammar_coverage=grammar_coverage)
                
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
        self.schedule.path_frequency = {}
