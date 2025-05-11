import random
from typing import List, Tuple

class SeedGenerator:
    """Class to generate seed."""
    
    def generate_seed(self, sql_queries: List[str], db_paths: List[str]) -> List[Tuple[str, str]]:
        """
        Generate a seed corpus with SQL queries and database paths.

        Args:
            sql_queries: List of SQL queries
            db_paths: List of database file paths
        Returns:
            List of tuples containing (sql_query, db_path)
        """
        if not sql_queries or not db_paths:
            return []

        # Assign a db_path to each SQL query
        extended_db_paths = db_paths
        if len(db_paths) < len(sql_queries):
            # If there are fewer databases than queries, extend the database paths
            while len(extended_db_paths) < len(sql_queries):
                extended_db_paths.extend(db_paths)

            extended_db_paths = extended_db_paths[:len(sql_queries)]
            random.shuffle(extended_db_paths)
        else:
            # If there are more databases than queries, randomly select databases
            extended_db_paths = random.sample(db_paths, len(sql_queries))
        
        inp_seed = list(zip(sql_queries, extended_db_paths))
        
        return inp_seed
    