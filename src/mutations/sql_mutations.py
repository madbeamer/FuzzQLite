#!/usr/bin/env python3
"""
SQL-specific Mutations

This module implements SQL-specific mutations for fuzzing SQLite.
"""

import random
import re
from typing import List

from .base_mutation import Mutation


class SQLRandomizeMutation(Mutation):
    """
    A mutation that modifies parts of SQL queries to trigger bugs.
    
    This mutation applies various SQL-specific mutations such as:
    - Adding/removing quotes
    - Changing numeric values
    - Inserting/replacing SQL keywords
    - Duplicating clauses
    """
    
    def __init__(self):
        """Initialize the SQL randomize mutation."""
        super().__init__()
        self.sql_keywords = [
            "SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
            "LIMIT", "OFFSET", "UNION", "UNION ALL", "INTERSECT", "EXCEPT",
            "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN",
            "CROSS JOIN", "NATURAL JOIN"
        ]
        
        self.sql_operators = [
            "=", "<>", "!=", ">", "<", ">=", "<=", "IS", "IS NOT", 
            "IN", "NOT IN", "LIKE", "NOT LIKE", "GLOB", "NOT GLOB", 
            "BETWEEN", "NOT BETWEEN"
        ]
        
        self.sql_functions = [
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "COALESCE",
            "LENGTH", "LOWER", "UPPER", "SUBSTR", "REPLACE",
            "RANDOM", "ROUND", "HEX", "TYPEOF"
        ]
    
    def mutate(self, input_data: str) -> str:
        """
        Apply SQL-specific mutation to the input.
        
        Args:
            input_data: The input SQL to mutate
            
        Returns:
            The mutated SQL string
        """
        # Choose a random mutation strategy
        strategies = [
            self._flip_quotes,
            self._change_numeric_value,
            self._insert_keyword,
            self._duplicate_clause,
            self._modify_operator,
            self._insert_function,
            self._add_comment,
            self._toggle_all_some_any
        ]
        
        # Use one of the strategies or just capitalize (fallback)
        strategy = random.choice(strategies + [lambda x: x.upper()])
        return strategy(input_data)
    
    def _flip_quotes(self, input_data: str) -> str:
        """Change single quotes to double quotes or vice versa."""
        if "'" in input_data:
            return input_data.replace("'", "\"")
        elif "\"" in input_data:
            return input_data.replace("\"", "'")
        return input_data
    
    def _change_numeric_value(self, input_data: str) -> str:
        """Find numeric values and change them."""
        # Find numbers in the SQL
        numbers = re.findall(r'\b\d+\b', input_data)
        if not numbers:
            return input_data
            
        # Pick a random number to change
        num_to_change = random.choice(numbers)
        
        # Choose a modification strategy
        strategies = [
            lambda x: str(int(x) + 1),                       # Increment
            lambda x: str(int(x) - 1) if int(x) > 0 else x,  # Decrement
            lambda x: str(-int(x)),                          # Negate
            lambda x: str(int(x) * 10),                      # Multiply by 10
            lambda x: str(2**31 - 1),                        # MAX_INT
            lambda x: str(-2**31),                           # MIN_INT
            lambda x: "0"                                    # Zero
        ]
        
        new_num = random.choice(strategies)(num_to_change)
        
        # Replace just one occurrence (not all)
        parts = input_data.split(num_to_change, 1)
        if len(parts) > 1:
            return parts[0] + new_num + parts[1]
        return input_data
    
    def _insert_keyword(self, input_data: str) -> str:
        """Insert or replace a SQL keyword."""
        keyword = random.choice(self.sql_keywords)
        
        # Choose between inserting and replacing
        if random.choice([True, False]) and any(k in input_data.upper() for k in self.sql_keywords):
            # Replace an existing keyword
            for existing_keyword in self.sql_keywords:
                if existing_keyword in input_data.upper():
                    return input_data.upper().replace(existing_keyword, keyword, 1)
        else:
            # Insert a new keyword at a random position
            pos = random.randint(0, len(input_data))
            return input_data[:pos] + " " + keyword + " " + input_data[pos:]
            
        return input_data
    
    def _duplicate_clause(self, input_data: str) -> str:
        """Duplicate a clause in the SQL statement."""
        # Look for common clauses
        clauses = ["WHERE", "GROUP BY", "ORDER BY", "LIMIT"]
        for clause in clauses:
            clause_pos = input_data.upper().find(clause)
            if clause_pos >= 0:
                # Find the end of the clause
                next_clause_pos = len(input_data)
                for next_clause in clauses:
                    pos = input_data.upper().find(next_clause, clause_pos + len(clause))
                    if pos > clause_pos:
                        next_clause_pos = min(next_clause_pos, pos)
                
                # Extract the clause
                clause_text = input_data[clause_pos:next_clause_pos]
                
                # Duplicate it
                return input_data[:next_clause_pos] + " " + clause_text + input_data[next_clause_pos:]
        
        return input_data
    
    def _modify_operator(self, input_data: str) -> str:
        """Replace an operator with another operator."""
        for op in self.sql_operators:
            if op in input_data.upper():
                new_op = random.choice(self.sql_operators)
                return input_data.upper().replace(op, new_op, 1)
        
        return input_data
    
    def _insert_function(self, input_data: str) -> str:
        """Insert a SQL function around a column or expression."""
        # Look for column references
        # This is a simplistic approach - in real SQL parsing would be better
        # Try to find a column reference
        match = re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', input_data)
        if match:
            column = match.group(0)
            func = random.choice(self.sql_functions)
            # Replace column with func(column)
            return input_data.replace(column, f"{func}({column})", 1)
        
        return input_data
    
    def _add_comment(self, input_data: str) -> str:
        """Add an SQL comment to potentially break parsing."""
        comment_types = ["--", "/**/", "/**//**/"]
        comment = random.choice(comment_types)
        
        # Insert at a random position
        pos = random.randint(0, len(input_data))
        return input_data[:pos] + comment + input_data[pos:]
    
    def _toggle_all_some_any(self, input_data: str) -> str:
        """Toggle between ALL, SOME, and ANY in subqueries."""
        keywords = ["ALL", "SOME", "ANY"]
        for keyword in keywords:
            if keyword in input_data.upper():
                new_keyword = random.choice([k for k in keywords if k != keyword])
                return input_data.upper().replace(keyword, new_keyword, 1)
        
        return input_data
    
    @property
    def name(self) -> str:
        """
        Get the name of this mutation operator.
        
        Returns:
            String name of the mutation
        """
        return "SQLRandomize"
    