import random
from typing import List, Optional, Tuple

from mutator import Mutator, IdentitiyMutator


class MutationFuzzer:
    """
    A fuzzer that mutates existing inputs to generate new test cases.
    """
    
    def __init__(self, seed: List[Tuple[str, str]],
                 mutators: Optional[List[Mutator]] = None,
                 min_mutations: int = 1,
                 max_mutations: int = 10,):
        """
        Initialize the mutation fuzzer.
        
        Args:
            seed: List of (sql_query, db_path) pairs to mutate
            mutators: List of mutator to use
            min_mutations: Minimum number of mutations to apply
            max_mutations: Maximum number of mutations to apply
        """
        self.seed = seed
        self.min_mutations = min_mutations
        self.max_mutations = max_mutations

        if mutators is None:
            self.mutators = [IdentitiyMutator()]
        else:
            self.mutators = mutators

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

    def reset(self) -> None:
        """Set population to initial seed."""
        self.population = self.seed
        self.seed_index = 0
