#!/usr/bin/env python3
"""
Corpus Generator

This module generates a seed corpus containing a specific SQL query for testing.
"""

from typing import List

class CorpusGenerator:
    """
    Class to generate a seed corpus with a single SQL query.
    """
    
    @staticmethod
    def generate_seed_corpus() -> List[str]:
        """
        Generate a seed corpus with only the specified SQL query.
        
        Returns:
            List of SQL queries
        """
        corpus = [
            # Test case for case-insensitive UNIQUE constraints and column renaming
            "CREATE TABLE t1(aaa, UNIQUE(aaA), UNIQUE(aAa), UNIQUE(aAA), CHECK(Aaa>0));",
            "ALTER TABLE t1 RENAME aaa TO bbb;"
        ]
        
        return corpus
    