import random
import re
import string
from typing import Tuple

from mutator.mutator import Mutator


class EnhancedSQLMutator(Mutator):
    """
    An enhanced mutator that modifies SQL queries to trigger edge cases and bugs in SQLite
    while maintaining query validity.
    """
    
    def __init__(self):
        """Initialize the enhanced SQL mutator."""
        super().__init__()
        
        self.sql_keywords = [
            "SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
            "LIMIT", "OFFSET", "UNION", "UNION ALL", "INTERSECT", "EXCEPT",
            "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN",
            "CROSS JOIN", "NATURAL JOIN", "INSERT", "UPDATE", "DELETE",
            "CREATE", "DROP", "ALTER", "BEGIN", "COMMIT", "ROLLBACK",
            "WITH", "RECURSIVE", "INDEXED BY", "NOT INDEXED", "AS", "ON", "USING"
        ]
        
        self.sql_operators = [
            "=", "<>", "!=", ">", "<", ">=", "<=", "IS", "IS NOT", 
            "IN", "NOT IN", "LIKE", "NOT LIKE", "GLOB", "NOT GLOB", 
            "BETWEEN", "NOT BETWEEN", "AND", "OR", "NOT"
        ]
        
        self.sql_functions = [
            "COUNT", "SUM", "AVG", "MIN", "MAX", "ABS", "COALESCE",
            "LENGTH", "LOWER", "UPPER", "SUBSTR", "REPLACE", "HEX", "TYPEOF", "IFNULL", "NULLIF", "JULIANDAY", # remove "ROUND"
            "DATE", "TIME", "DATETIME", "STRFTIME", "RANDOM", "TOTAL"
        ]
        
        # Edge case constants for numeric values - valid SQLite values
        self.edge_case_numbers = [
            "0", "-0", "0.0", "-0.0",
            str(2**31 - 1),     # MAX_INT
            str(-2**31),        # MIN_INT
            str(2**63 - 1),     # MAX_BIGINT
            str(-2**63),        # MIN_BIGINT
            "9223372036854775807", # Max 64-bit integer
            "-9223372036854775808", # Min 64-bit integer
            "9223372036854775808",  # Overflow by 1
            "1.7976931348623157e+308", # Max double
            "2.2250738585072014e-308", # Min positive normal double
            "-1e308",           # Large negative
            "1.0/0.0"           # Division by zero (will be evaluated at runtime)
        ]
        
        # Problematic but valid string values
        self.edge_case_strings = [
            "''",                     # Empty literal
            "' '",                    # Space
            "'%'",                    # Wildcard
            "'_'",                    # Single character wildcard
            "'\\''",                  # Escaped single quote
            "'\\\\'",                 # Backslash
            "'\\n'",                  # Newline
            "'\\r'",                  # Carriage return
            "'\\t'",                  # Tab
            "'\\Z'",                  # EOF character
            "x'00'",                  # Binary null
            "x'FF'",                  # Binary 0xFF
            "NULL",                   # NULL value
            "CURRENT_TIMESTAMP",      # Current timestamp
            "'-1 day'",               # Date negative offset
            "'9999-12-31'",           # Far future date
            "'0000-01-01'",           # Far past date
            "'2038-01-19 03:14:07'",  # Unix timestamp limit
            "(SELECT 1)",             # Subquery
            "CAST(NULL AS TEXT)",     # Cast expressions
            "json('\"string\"')"      # JSON string
        ]
        
        # Common UTF-8 characters (valid in SQLite)
        self.utf8_edge_cases = [
            "'Ä'", "'ñ'", "'€'", "'北'", "'😀'",
            "'éèêë'", "'\\u0000'"
        ]
        
        # SQLite-specific pragmas (valid)
        self.sqlite_pragmas = [
            "PRAGMA case_sensitive_like=TRUE",
            "PRAGMA case_sensitive_like=FALSE",
            "PRAGMA foreign_keys=OFF",
            "PRAGMA foreign_keys=ON",
            "PRAGMA journal_mode=WAL",
            "PRAGMA journal_mode=DELETE",
            "PRAGMA synchronous=OFF",
            "PRAGMA recursive_triggers=ON",
            "PRAGMA recursive_triggers=OFF"
        ]
    
    def mutate(self, inp: Tuple[str, str]) -> Tuple[str, str]:
        """
        Apply enhanced SQL-specific mutation to the input.
        
        Args:
            inp: (sql_query, db_path) tuple
            
        Returns:
            The mutated input data (sql_query, db_path)
        """
        sql_query, db_path = inp
        
        # Validate input is a SELECT query
        if not sql_query.upper().strip().startswith("SELECT"):
            # Only mutate SELECT queries to ensure basic validity
            return (sql_query, db_path)

        # Choose a random mutation strategy with weighted probabilities
        strategies = [
            # Original strategies (modified for safety)
            (self._change_numeric_value, 0.15),
            (self._modify_operator, 0.15),
            (self._insert_function, 0.15),
            (self._toggle_all_some_any, 0.05),
            
            # New strategies (validated for syntax correctness)
            (self._insert_edge_case_number, 0.10),
            (self._insert_edge_case_string, 0.10),
            (self._inject_unicode_character, 0.05),
            (self._inject_complex_expression, 0.05),
            (self._inject_safe_subquery, 0.05),
            (self._inject_common_table_expression, 0.05),
            (self._toggle_case, 0.05),
            (self._add_whitespace, 0.02),
            (self._add_comment, 0.03),
            (self._randomize_limit_offset, 0.05)
        ]
        
        # Choose a strategy based on weights
        strategy_funcs, weights = zip(*strategies)
        strategy = random.choices(strategy_funcs, weights=weights, k=1)[0]
        
        # Save original query in case mutation fails
        original_query = sql_query
        
        try:
            # Apply the chosen strategy
            mutated_sql_query = strategy(sql_query)
            
            # Basic validation check
            if not self._is_likely_valid(mutated_sql_query):
                return (original_query, db_path)
            
            return (mutated_sql_query, db_path)
        except Exception:
            # If any error occurs during mutation, return the original query
            return (original_query, db_path)
    
    def _is_likely_valid(self, query: str) -> bool:
        """
        Perform a basic check to see if the query is likely to be valid SQL.
        This is not a full parser but should catch obvious errors.
        """
        # Very basic check for balanced parentheses
        if query.count('(') != query.count(')'):
            return False
        
        # Basic check for balanced quotes (simplistic, doesn't handle escapes properly)
        if query.count("'") % 2 != 0:
            return False
        
        # Check for missing essential keywords in SELECT queries
        if query.upper().startswith("SELECT") and "FROM" not in query.upper():
            return False
        
        # Ensure query has minimum required length
        if len(query.strip()) < 10:
            return False
        
        return True
    
    # Enhanced mutation strategies
    
    def _change_numeric_value(self, input_data: str) -> str:
        """Find numeric values and change them safely."""
        # Find numbers in the SQL
        numbers = re.findall(r'(?<!\w)(-?\d+(?:\.\d+)?)(?!\w)', input_data)
        if not numbers:
            return input_data
            
        # Pick a random number to change
        num_to_change = random.choice(numbers)
        
        # Choose a modification strategy (safer options)
        strategies = [
            lambda x: str(int(float(x)) + 1),    # Increment
            lambda x: str(int(float(x)) - 1),    # Decrement
            lambda x: str(-float(x)),            # Negate
            lambda x: random.choice(self.edge_case_numbers)  # Replace with edge case
        ]
        
        new_num = random.choice(strategies)(num_to_change)
        
        # Replace just one occurrence (not all)
        parts = input_data.split(num_to_change, 1)
        if len(parts) > 1:
            return parts[0] + new_num + parts[1]
        return input_data
    
    def _modify_operator(self, input_data: str) -> str:
        """Replace an operator with another operator safely."""
        # Dictionary of compatible operators
        compatible_operators = {
            "=": ["<>", "!=", "IS", "IS NOT"],
            "<>": ["=", "!=", "IS NOT", "IS"],
            "!=": ["=", "<>", "IS NOT", "IS"],
            ">": [">=", "<", "<="],
            "<": ["<=", ">", ">="],
            ">=": [">", "<=", "<"],
            "<=": ["<", ">=", ">"],
            "IS": ["IS NOT", "=", "<>"],
            "IS NOT": ["IS", "<>", "="],
            "IN": ["NOT IN"],
            "NOT IN": ["IN"],
            "LIKE": ["NOT LIKE"],
            "NOT LIKE": ["LIKE"],
            "BETWEEN": ["NOT BETWEEN"],
            "NOT BETWEEN": ["BETWEEN"],
            "AND": ["OR"],
            "OR": ["AND"]
        }
        
        for op in self.sql_operators:
            # Look for the operator with word boundaries or spaces
            pattern = r'\b' + re.escape(op) + r'\b|\s' + re.escape(op) + r'\s'
            if re.search(pattern, input_data.upper()):
                # Get compatible replacements
                replacements = compatible_operators.get(op, [])
                if not replacements:
                    continue
                    
                new_op = random.choice(replacements)
                
                # Case-preserving replacement
                if op in input_data:
                    return re.sub(pattern, lambda m: m.group(0).replace(op, new_op), input_data, count=1, flags=re.IGNORECASE)
                elif op.lower() in input_data:
                    return re.sub(pattern, lambda m: m.group(0).replace(op.lower(), new_op.lower()), input_data, count=1, flags=re.IGNORECASE)
                else:
                    # Must be uppercase in the original
                    return re.sub(pattern, lambda m: m.group(0).replace(op, new_op), input_data, count=1, flags=re.IGNORECASE)
        
        return input_data
    
    def _insert_function(self, input_data: str) -> str:
        """Insert a SQL function around a column or expression safely."""
        # Look for column references but avoid SQL keywords
        matches = re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)\b', input_data)
        columns = [match.group(0) for match in matches]
        
        if not columns:
            return input_data
            
        # Filter out SQL keywords
        columns = [col for col in columns if col.upper() not in [k.upper() for k in self.sql_keywords]]
        
        if not columns:
            return input_data
            
        column = random.choice(columns)
        
        # Functions that can safely wrap any column
        safe_functions = ["IFNULL", "COALESCE", "ABS", "TYPEOF", "LENGTH", "UPPER", "LOWER"] # remove "ROUND"
        func = random.choice(safe_functions)
        
        # Ensure there's appropriate second arguments for functions that need them
        if func == "IFNULL" or func == "COALESCE":
            replacement = f"{func}({column}, 0)"
        # elif func == "ROUND": # remove "ROUND"
        #     replacement = f"{func}({column}, 0)"
        else:
            replacement = f"{func}({column})"
        
        # Replace column with func(column)
        return input_data.replace(column, replacement, 1)
    
    def _toggle_all_some_any(self, input_data: str) -> str:
        """Toggle between ALL, SOME, and ANY in subqueries safely."""
        keywords = ["ALL", "SOME", "ANY"]
        
        # Pattern for finding these keywords in the correct context (in subqueries)
        pattern = r'((?:>|<|=|>=|<=|<>|!=)\s+(?:ALL|SOME|ANY)\s*\()'
        
        match = re.search(pattern, input_data, re.IGNORECASE)
        if match:
            for keyword in keywords:
                if keyword in match.group(0).upper():
                    new_keyword = random.choice([k for k in keywords if k != keyword])
                    replaced = match.group(0).replace(keyword, new_keyword)
                    if keyword.lower() in match.group(0).lower():
                        replaced = match.group(0).replace(keyword.lower(), new_keyword.lower())
                    
                    return input_data[:match.start()] + replaced + input_data[match.end():]
        
        return input_data
    
    # New mutation strategies (safer versions)
    
    def _insert_edge_case_number(self, input_data: str) -> str:
        """Replace a number with an edge case number safely."""
        # Find numbers in the SQL
        numbers = re.findall(r'(?<!\w)(-?\d+(?:\.\d+)?)(?!\w)', input_data)
        if not numbers:
            return input_data
            
        # Pick a random number to change
        num_to_change = random.choice(numbers)
        edge_num = random.choice(self.edge_case_numbers)
        
        # Replace just one occurrence
        parts = input_data.split(num_to_change, 1)
        if len(parts) > 1:
            return parts[0] + edge_num + parts[1]
        return input_data
    
    def _insert_edge_case_string(self, input_data: str) -> str:
        """Replace a string literal with an edge case string safely."""
        # Find string literals in the SQL
        string_literals = re.findall(r"'[^']*'", input_data)
        if not string_literals:
            return input_data
            
        # Pick a random string to change
        str_to_change = random.choice(string_literals)
        edge_str = random.choice(self.edge_case_strings)
        
        # Replace just one occurrence
        return input_data.replace(str_to_change, edge_str, 1)
    
    def _inject_unicode_character(self, input_data: str) -> str:
        """Inject a Unicode character into a string literal safely."""
        # Find string literals in the SQL
        string_literals = re.findall(r"'[^']*'", input_data)
        if not string_literals:
            return input_data
        
        # Pick a random string to change
        str_to_change = random.choice(string_literals)
        utf8_string = random.choice(self.utf8_edge_cases)
        
        # Replace the string
        return input_data.replace(str_to_change, utf8_string, 1)
    
    def _inject_complex_expression(self, input_data: str) -> str:
        """Inject a complex but valid expression."""
        safe_expressions = [
            "CASE WHEN 1=1 THEN 1 ELSE 0 END",
            "CASE WHEN NULL IS NULL THEN 1 ELSE 0 END",
            "COALESCE(NULL, NULL, 1, NULL)",
            "CAST('' AS TEXT)",
            "CAST(1 AS REAL)",
            "1 + CAST('2' AS INTEGER)",
            "SUBSTR('abc', 1, 10)",
            "LENGTH(x'00')",
            "ABS(-1)",
            # "ROUND(1.0/2.0)", # remove "ROUND"
            "json_extract('{\"a\":1}', '$.a')",
            "(SELECT 1)"
        ]
        
        complex_expr = random.choice(safe_expressions)
        
        # Find a good place to inject the expression
        if "SELECT" in input_data.upper():
            # After SELECT in the column list
            select_pos = input_data.upper().find("SELECT")
            from_pos = input_data.upper().find("FROM", select_pos)
            if from_pos != -1:
                # Insert as a column
                inject_pos = select_pos + 6
                
                return input_data[:inject_pos] + " " + complex_expr + " AS complex_col, " + input_data[inject_pos:]
        
        # Fallback - add in WHERE clause if exists
        if "WHERE" in input_data.upper():
            where_pos = input_data.upper().find("WHERE")
            # Find next keyword after WHERE
            next_keyword = None
            next_pos = len(input_data)
            for keyword in ["GROUP BY", "HAVING", "ORDER BY", "LIMIT"]:
                pos = input_data.upper().find(keyword, where_pos)
                if pos != -1 and pos < next_pos:
                    next_pos = pos
                    next_keyword = keyword
            
            if next_keyword:
                # Insert before next keyword
                return input_data[:next_pos] + " AND " + complex_expr + " = " + complex_expr + " " + input_data[next_pos:]
            else:
                # Append to end of query
                return input_data + " AND " + complex_expr + " = " + complex_expr
        
        return input_data
    
    def _inject_safe_subquery(self, input_data: str) -> str:
        """Inject a safe subquery."""
        safe_subqueries = [
            "(SELECT 1)",
            "(SELECT COUNT(*) FROM (SELECT 1) AS t)",
            "(SELECT CASE WHEN 1=1 THEN 1 ELSE 0 END)",
            "(SELECT 1 LIMIT 1)",
            "(SELECT TYPEOF(1))",
            "(SELECT json_valid('{\"a\":1}'))"
        ]
        
        subquery = random.choice(safe_subqueries)
        
        # Find a safe place for the subquery
        if "SELECT" in input_data.upper():
            select_pos = input_data.upper().find("SELECT")
            from_pos = input_data.upper().find("FROM", select_pos)
            if from_pos != -1:
                # Add as a column
                inject_pos = select_pos + 6
                return input_data[:inject_pos] + " " + subquery + " AS subq_col, " + input_data[inject_pos:]
        
        # Fallback to WHERE clause
        if "WHERE" in input_data.upper():
            where_pos = input_data.upper().find("WHERE")
            # Insert after WHERE
            inject_pos = where_pos + 5
            return input_data[:inject_pos] + " " + subquery + " = " + subquery + " AND " + input_data[inject_pos:]
        
        return input_data
    
    def _inject_common_table_expression(self, input_data: str) -> str:
        """Inject a common table expression (CTE) using WITH clause safely."""
        if input_data.upper().strip().startswith("WITH"):
            # Already has a WITH clause, don't modify
            return input_data
        
        safe_cte_templates = [
            "WITH t AS (SELECT 1 AS col) ",
            "WITH t1 AS (SELECT 0 AS n), t2 AS (SELECT 1 AS n) ",
            "WITH RECURSIVE t(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM t WHERE x < 3) "
        ]
        
        cte = random.choice(safe_cte_templates)
        
        # Place CTE at beginning of query
        if input_data.upper().strip().startswith("SELECT"):
            return cte + input_data
        
        return input_data
    
    def _toggle_case(self, input_data: str) -> str:
        """Toggle the case of SQL keywords safely."""
        for keyword in self.sql_keywords:
            if keyword in input_data.upper():
                # Find the keyword with word boundaries
                pattern = r'\b' + re.escape(keyword) + r'\b'
                match = re.search(pattern, input_data, re.IGNORECASE)
                if match:
                    case_functions = [
                        lambda w: w.upper(),
                        lambda w: w.lower(),
                        lambda w: w.capitalize()
                    ]
                    
                    new_word = random.choice(case_functions)(match.group(0))
                    
                    # Replace the word
                    return input_data[:match.start()] + new_word + input_data[match.end():]
        
        return input_data
    
    def _add_whitespace(self, input_data: str) -> str:
        """Add whitespace in strategic locations safely."""
        whitespace_patterns = [
            " " * random.randint(2, 5),  # Multiple spaces
            "\t",                         # Tab
            " \t ",                       # Mixed whitespace
            "\n    "                      # Newline with indent
        ]
        
        whitespace = random.choice(whitespace_patterns)
        
        # Strategic locations
        locations = []
        
        # After keywords
        for keyword in self.sql_keywords:
            if keyword in input_data.upper():
                keyword_end = input_data.upper().find(keyword) + len(keyword)
                if keyword_end < len(input_data) and input_data[keyword_end].isspace():
                    locations.append(keyword_end)
        
        # After commas
        for i, char in enumerate(input_data):
            if char == ',' and i + 1 < len(input_data) and input_data[i+1].isspace():
                locations.append(i + 1)
        
        if not locations:
            return input_data
            
        # Choose a location
        pos = random.choice(locations)
        
        # Add whitespace
        return input_data[:pos] + whitespace + input_data[pos:]
    
    def _add_comment(self, input_data: str) -> str:
        """Add SQL comments in strategic places safely."""
        comment_templates = [
            "/* */",
            "/* comment */",
            "-- inline comment",
            "-- ",
            "/* safe comment */",
            "/* valid sql */",
            "/**/",
        ]
        
        comment = random.choice(comment_templates)
        
        # Strategic locations
        locations = []
        
        # After keywords
        for keyword in self.sql_keywords:
            if keyword in input_data.upper():
                keyword_end = input_data.upper().find(keyword) + len(keyword)
                if keyword_end < len(input_data) and input_data[keyword_end].isspace():
                    locations.append(keyword_end)
        
        # After commas
        for i, char in enumerate(input_data):
            if char == ',' and i + 1 < len(input_data) and input_data[i+1].isspace():
                locations.append(i + 1)
        
        if not locations:
            return input_data
            
        # Choose a location
        pos = random.choice(locations)
        
        # Add comment
        return input_data[:pos] + " " + comment + " " + input_data[pos:]
    
    def _randomize_limit_offset(self, input_data: str) -> str:
        """Randomize or add LIMIT and OFFSET clauses safely."""
        limit_values = [
            "0",
            "1",
            "1000",
            str(2**31 - 1),  # MAX_INT
            "(SELECT 1)"      # Subquery (valid in SQLite)
        ]
        
        offset_values = [
            "0",
            "1",
            "1000",
            str(2**31 - 1),  # MAX_INT
            "(SELECT 0)"      # Subquery (valid in SQLite)
        ]
        
        # If query already has LIMIT
        if "LIMIT" in input_data.upper():
            # Replace existing LIMIT
            limit_pos = input_data.upper().find("LIMIT")
            offset_pos = input_data.upper().find("OFFSET", limit_pos)
            
            if offset_pos != -1:
                # Replace both LIMIT and OFFSET
                end_pos = len(input_data)
                for kw in self.sql_keywords:
                    pos = input_data.upper().find(kw, offset_pos + 6)
                    if pos != -1 and pos < end_pos:
                        end_pos = pos
                
                new_limit = random.choice(limit_values)
                new_offset = random.choice(offset_values)
                return input_data[:limit_pos] + f"LIMIT {new_limit} OFFSET {new_offset}" + input_data[end_pos:]
            else:
                # Find the end of LIMIT clause
                end_pos = len(input_data)
                for kw in self.sql_keywords:
                    if kw != "LIMIT":
                        pos = input_data.upper().find(kw, limit_pos + 5)
                        if pos != -1 and pos < end_pos:
                            end_pos = pos
                
                # Replace LIMIT and maybe add OFFSET
                new_limit = random.choice(limit_values)
                if random.choice([True, False]):
                    new_offset = random.choice(offset_values)
                    return input_data[:limit_pos] + f"LIMIT {new_limit} OFFSET {new_offset}" + input_data[end_pos:]
                else:
                    return input_data[:limit_pos] + f"LIMIT {new_limit}" + input_data[end_pos:]
        else:
            # Add LIMIT to the end
            new_limit = random.choice(limit_values)
            if random.choice([True, False]):
                new_offset = random.choice(offset_values)
                return input_data + f" LIMIT {new_limit} OFFSET {new_offset}"
            else:
                return input_data + f" LIMIT {new_limit}"
            