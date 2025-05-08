import random
import re
import os
import json
from typing import Tuple, List

from mutator.mutator import Mutator


class ImprovedMutator(Mutator):
    """
    A mutator that modifies parts of SQL queries to trigger bugs.
    """
    
    def __init__(self, schema_path: str = "databases/schema_info.json"):
        """Initialize the SQL mutator."""
        super().__init__()

        self.weights = [0.2, 0.1, 0.1, 0.15, 0.25, 0.2]
        
        self.sql_keywords = [
            "SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
            "LIMIT", "OFFSET", "UNION", "UNION ALL", "INTERSECT", "EXCEPT",
            "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN",
            "CROSS JOIN", "NATURAL JOIN", "INSERT", "UPDATE", "DELETE",
            "CREATE", "DROP", "ALTER", "BEGIN", "COMMIT", "ROLLBACK"
        ]
        
        self.sql_operators = [
            "=", "<>", "!=", ">", "<", ">=", "<=", "IS", "IS NOT", 
            "IN", "NOT IN", "LIKE", "NOT LIKE", "GLOB", "NOT GLOB", 
            "BETWEEN", "NOT BETWEEN"
        ]
        
        self.sql_functions = [
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "COALESCE",
            "LENGTH", "LOWER", "UPPER", "SUBSTR", "REPLACE", "HEX", "TYPEOF" # remove "ROUND"
        ]

        # Load table names from schema JSON file
        self.db_tables = self._load_table_names(schema_path)

        self.pragma_statements = [
            "PRAGMA foreign_keys = ON;",
            "PRAGMA foreign_keys = OFF;",
            "PRAGMA synchronous = FULL;",
            "PRAGMA encoding = 'UTF8';",
            "PRAGMA encoding = 'UTF16';",
            "PRAGMA encoding = 'UTF16be';",
        ]
    
    def _load_table_names(self, schema_path: str) -> List[str]:
        try:
            if not os.path.exists(schema_path):
                print(f"Warning: Schema file not found at {schema_path}.")
                return []
                
            with open(schema_path, 'r') as f:
                schema_info = json.load(f)
            
            # Extract table names (exclude views)
            table_names = [table_name for table_name, info in schema_info.items() 
                          if not info.get("is_view", False)]
            
            if not table_names:
                print("Warning: No tables found in schema file.")
                return []
                
            return table_names
            
        except Exception as e:
            print(f"Error loading table names from schema: {e}.")
            return []

    def mutate(self, inp: Tuple[str, str]) -> Tuple[str, str]:
        """
        Apply SQL-specific mutation to the input.
        
        Args:
            inp: (sql_query, db_path) tuple
            
        Returns:
            The mutated input data (sql_query, db_path)
        """
        sql_query, db_path = inp

        self._reset()
        mutated_sql_query = self._find_strategy(sql_query, self.weights)
        
        return (mutated_sql_query, db_path)
    
    def _reset(self) -> None:
        """Reset the mutator state."""
        self.weights = [0.2, 0.1, 0.1, 0.15, 0.25, 0.2]
    
    def _find_strategy(self, sql_query: str, probabilities: list) -> str:
        strategies = [
            self._change_numeric_value,
            self._insert_keyword,
            self._modify_operator,
            self._insert_function,
            self._modify_strings,
            self._nest_select
        ]
        if sum(self.weights) == 0:
            pragma = random.choice(self.pragma_statements)
            return pragma + sql_query
        strategy = random.choices(strategies, k=1, weights=probabilities)[0]
        return strategy(sql_query)
    
    def _change_numeric_value(self, input_data: str) -> str:
        """Find numeric values and change them."""
        # Find numbers in the SQL
        numbers = re.findall(r'\b\d+\b', input_data)
        if not numbers:
            self.weights[0] = 0.0
            return self._find_strategy(input_data, self.weights)
            
        # Pick a random number to change
        num_to_change = random.choice(numbers)
        
        # Choose a modification strategy
        strategies = [
            lambda x: str(int(x) + 1),    # Increment
            lambda x: str(int(x) - 1),    # Decrement
            lambda x: str(-int(x)),       # Negate
            lambda x: str(2**31 - 1),     # MAX_INT
            lambda x: str(-2**31),        # MIN_INT
            lambda x: "0",                # Zero
            lambda x: "-0",               # Negative Zero
            lambda x: "NULL"
        ]
        
        new_num = random.choice(strategies)(num_to_change)
        
        # Replace just one occurrence (not all)
        parts = input_data.split(num_to_change, 1)
        return parts[0] + new_num + parts[1]

    def _insert_keyword(self, input_data: str) -> str:
        """Insert or replace a SQL keyword."""
        keyword = random.choice(self.sql_keywords)
        
        # Choose between inserting and replacing
        if random.choice([True, False]) and any(k in input_data.upper() for k in self.sql_keywords):
            found_keywords = []
            for existing_keyword in self.sql_keywords:
                if existing_keyword in input_data.upper() and existing_keyword not in ["SELECT", "FROM", "WHERE"] and existing_keyword != keyword:
                    found_keywords.append(existing_keyword)

            if not found_keywords:
                self.weights[1] = 0.0
                return self._find_strategy(input_data, self.weights)

            to_replace = random.choice(found_keywords)

            positions = []
            start_pos = 0
            while True:
                pos = input_data.find(to_replace, start_pos)
                if pos == -1:
                    break
                positions.append(pos)
                start_pos = pos + len(to_replace)
            if not positions:
                self.weights[1] = 0.0
                return self._find_strategy(input_data, self.weights)
            random_pos = random.choice(positions)
            return input_data[:random_pos] + keyword + " " + input_data[random_pos + len(to_replace):]
        else:
            # Insert a new keyword at a random position
            # But avoid breaking the basic structure
            if keyword in ["AND", "OR"]:
                # Only insert logical operators in WHERE clauses
                if "WHERE" in input_data.upper():
                    where_pos = input_data.upper().find("WHERE")
                    pos = random.randint(where_pos, len(input_data))
                    return input_data[:pos] + " " + keyword + " " + input_data[pos:]
            
        self.weights[1] = 0.0
        return self._find_strategy(input_data, self.weights) 
    
    def _modify_operator(self, input_data: str) -> str:
        found_operators = []
        for op in self.sql_operators:
            if f" {op} " in input_data:
                found_operators.append(op)
        
        if not found_operators:
            self.weights[2] = 0.0
            return self._find_strategy(input_data, self.weights) 
        
        op_to_replace = random.choice(found_operators)

        positions = []
        start_pos = 0
        while True:
            pos = input_data.find(op_to_replace, start_pos)
            if pos == -1:
                break
            positions.append(pos)
            start_pos = pos + len(op_to_replace)
        
        random_pos = random.choice(positions)

        while True:
            new_op = random.choice(self.sql_operators)
            # Avoid replacing with incompatible operators
            if (new_op in ["BETWEEN", "NOT BETWEEN"] and 
                op_to_replace not in ["BETWEEN", "NOT BETWEEN"]):
                continue
            if new_op != op_to_replace:  # Avoid replacing with the same operator
                break
            
        return (input_data[:random_pos] + new_op + input_data[random_pos + len(op_to_replace):])
    
    def _insert_function(self, input_data: str) -> str:
        """Insert a SQL function around a column or expression."""
        # Look for column references but avoid SQL keywords
        # Updated regex to be more specific to column names
        match = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)\b', input_data)
        if match:
            column = match.group(0)
            # Check if it's not a SQL keyword
            if column.upper() not in [k.upper() for k in self.sql_keywords]:
                func = random.choice(self.sql_functions)
                rnd = random.randint(0, 1)
                if rnd == 0:
                    # Replace column with func(NULL)
                    return input_data.replace(column, f"{func}(NULL)", 1)
                else:
                    # Replace column with func(column) and add a space
                    return input_data.replace(column, f"{func}({column}) ", 1)

        self.weights[3] = 0.0
        return self._find_strategy(input_data, self.weights)
    
    def _modify_strings(self, input_data: str) -> str:
        """Modify string literals in the SQL query."""
        # Look for string literals
        string_literals = re.findall(r'\'[^\']*\'|"[^"]*"', input_data)
        if not string_literals:
            self.weights[4] = 0.0
            return self._find_strategy(input_data, self.weights)
        
        # Pick a random string literal to modify
        str_to_modify = random.choice(string_literals)
        
        # Choose a modification strategy
        strategies = [
            lambda x: "''",  # Empty string
            lambda x: """""",
            lambda x: "NULL",  # NULL value
            lambda x: "\n",  # New line
            lambda x: "\t",  # Tab
            lambda x: "\\",  # Backslash
            lambda x: "\00",
            lambda x: x + "%",
            lambda x: "%_",
            lambda x: x + "?",
            lambda x: "?*",
            lambda x: ":",
            lambda x: "@$",
            lambda x: ";",
        ]
        
        new_str = random.choice(strategies)(str_to_modify)
        
        # Replace just one occurrence (not all)
        parts = input_data.split(str_to_modify, 1)
        return parts[0] + "'" + new_str + "'" + parts[1]

    def _nest_select(self, input_data: str) -> str:
        if 'FROM' in input_data.upper():
            positions = []
            start_pos = 0
            while True:
                pos = input_data.find('FROM', start_pos)
                if pos == -1:
                    break
                positions.append(pos)
                start_pos = pos + len('FROM')
            
            rand_pos = random.choice(positions)
            table = random.choice(self.db_tables)

            if not table:
                self.weights[5] = 0.0
                return self._find_strategy(input_data, self.weights)

            subquery = f"(SELECT * FROM {table})"

            # Extract content after FROM, then remove the first word and add the subquery
            after_from = input_data[rand_pos + 4:].strip()
            first_word_match = re.search(r'\s+', after_from)
            if first_word_match:
                # Found a space, which means there's more than one word
                first_word_end = first_word_match.start()
                return input_data[:rand_pos + 4] + " " + subquery + after_from[first_word_end:]
            else:
                # Only one word after FROM, replace it entirely
                return input_data[:rand_pos + 4] + " " + subquery
        else:
            self.weights[5] = 0.0
            return self._find_strategy(input_data, self.weights)
        