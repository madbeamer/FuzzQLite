import random
from typing import List, Optional, Tuple

from mutator import Mutator, IdentityMutation


class MutationFuzzer:
    """
    A fuzzer that mutates existing inputs to generate new test cases.
    """
    
    def __init__(self, seed: Optional[int] = None, 
                 mutations: Optional[List[Mutator]] = None,
                 db_paths: Optional[List[str]] = None):
        """
        Initialize the mutation fuzzer.
        
        Args:
            seed: Optional seed for random number generation
            mutations: List of mutator to use
            db_paths: List of database file paths to use
        """
        self.seed = seed
        self.corpus = []
        
        if mutations is None:
            self.mutations = [IdentityMutation()]
        else:
            self.mutations = mutations
        
        # Store database paths
        self.db_paths = db_paths if db_paths else []
        
        # FIXME: We might validate the queries later
        # Initialize validator
        # self.validator = SQLiteValidator()
            
        # Set the random seed if provided
        if seed is not None:
            random.seed(seed)
    
    def fuzz(self) -> Tuple[str, str]:
        """
        Generate a fuzz input by mutating an item from the corpus.
        
        Returns:
            A tuple containing (db_path, mutated_sql_query)
        """
        if not self.corpus or not self.db_paths:
            # Return empty defaults if no corpus or databases
            return "", ""
        

        db_path = random.choice(self.db_paths)
        seed_query = random.choice(self.corpus)

        mutation = random.choice(self.mutations)
        mutated_query = mutation.mutate(seed_query)

        return db_path, mutated_query
    
    def add_to_corpus(self, item: str) -> None:
        """
        Add an item to the corpus.
        
        Args:
            item: String to add to corpus
        """
        self.corpus.append(item)
    
    def load_corpus(self, corpus_items: List[str]) -> None:
        """
        Load multiple items into the corpus.
        
        Args:
            corpus_items: List of strings to add to corpus
        """
        self.corpus.extend(corpus_items)
