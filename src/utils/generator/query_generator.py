import json
import os
import random
import re
from typing import List, Dict, Any, Tuple, Set

class QueryGenerator:
    """
    Enhanced class to generate SQL queries covering most SQL features.
    """
    
    def __init__(self, schema_path: str = "databases/schema_info.json"):
        """
        Initialize the query generator.
        
        Args:
            schema_path: Path to the schema JSON file
        """
        self.schema_info = self._load_schema(schema_path)
        self.table_names = [name for name, info in self.schema_info.items() 
                           if not info.get("is_view", False)]
        self.view_names = [name for name, info in self.schema_info.items() 
                          if info.get("is_view", False)]
        
        if not self.table_names:
            raise ValueError("No tables found in schema information.")
    
    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """
        Load schema information from JSON file.
        
        Args:
            schema_path: Path to the schema JSON file
            
        Returns:
            Dictionary with schema information
        """
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file {schema_path} not found.")
            
        with open(schema_path, 'r') as f:
            schema_info = json.load(f)
        
        return schema_info
    
    def _get_random_table(self) -> str:
        """Get a random table name from the schema."""
        return random.choice(self.table_names)
    
    def _get_random_view(self) -> str:
        """Get a random view name from the schema."""
        if not self.view_names:
            return None
        return random.choice(self.view_names)
    
    def _get_random_tables(self, count: int = 2) -> List[str]:
        """Get multiple random table names from the schema."""
        if count >= len(self.table_names):
            return self.table_names.copy()
        return random.sample(self.table_names, count)
    
    def _get_random_column(self, table_name: str) -> str:
        """Get a random column name from the specified table."""
        if table_name not in self.schema_info:
            raise ValueError(f"Table {table_name} not found in schema.")
            
        return random.choice(self.schema_info[table_name]["column_names"])
    
    def _get_random_columns(self, table_name: str, min_count: int = 1, max_count: int = None) -> List[str]:
        """Get random column names from the specified table."""
        if table_name not in self.schema_info:
            raise ValueError(f"Table {table_name} not found in schema.")
            
        columns = self.schema_info[table_name]["column_names"]
        
        if max_count is None or max_count > len(columns):
            max_count = len(columns)
            
        count = random.randint(min_count, max_count)
        return random.sample(columns, count)
    
    def _get_primary_key_column(self, table_name: str) -> str:
        """Get the primary key column of the specified table."""
        if table_name not in self.schema_info:
            raise ValueError(f"Table {table_name} not found in schema.")
            
        # Assuming c0 is always the primary key
        return "c0"
    
    def _get_random_index(self, table_name: str) -> str:
        """Get a random index name from the specified table."""
        if table_name not in self.schema_info:
            raise ValueError(f"Table {table_name} not found in schema.")
            
        indices = self.schema_info[table_name]["index_names"]
        if not indices:
            return None
            
        return random.choice(indices)
    
    def _get_column_type(self, table_name: str, column_name: str) -> str:
        """Get the data type of a column."""
        if table_name not in self.schema_info:
            raise ValueError(f"Table {table_name} not found in schema.")
            
        if column_name not in self.schema_info[table_name]["column_types"]:
            raise ValueError(f"Column {column_name} not found in table {table_name}.")
            
        return self.schema_info[table_name]["column_types"][column_name]
    
    def _is_numeric_column(self, table_name: str, column_name: str) -> bool:
        """Check if the column is numeric."""
        col_type = self._get_column_type(table_name, column_name)
        numeric_types = ["INTEGER", "INT", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT", 
                         "UNSIGNED BIG INT", "INT2", "INT8", "REAL", "DOUBLE", 
                         "DOUBLE PRECISION", "FLOAT", "NUMERIC", "DECIMAL"]
        
        return any(num_type in col_type.upper() for num_type in numeric_types)
    
    def _is_text_column(self, table_name: str, column_name: str) -> bool:
        """Check if the column is text."""
        col_type = self._get_column_type(table_name, column_name)
        text_types = ["TEXT", "CHARACTER", "VARCHAR", "VARYING CHARACTER", 
                     "NCHAR", "NATIVE CHARACTER", "NVARCHAR", "CLOB"]
        
        return any(text_type in col_type.upper() for text_type in text_types)
    
    def _is_date_column(self, table_name: str, column_name: str) -> bool:
        """Check if the column is a date or datetime."""
        col_type = self._get_column_type(table_name, column_name)
        return "DATE" in col_type.upper()
    
    def _get_literal_for_column(self, table_name: str, column_name: str) -> str:
        """Get a literal value appropriate for the column's data type."""
        col_type = self._get_column_type(table_name, column_name)
        
        # Integer types
        if any(int_type in col_type.upper() for int_type in ["INTEGER", "INT", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT"]):
            return str(random.randint(1, 100))
        
        # Float types
        elif any(float_type in col_type.upper() for float_type in ["REAL", "DOUBLE", "FLOAT", "NUMERIC", "DECIMAL"]):
            return str(round(random.uniform(1.0, 100.0), 2))
        
        # Text types
        elif any(text_type in col_type.upper() for text_type in ["TEXT", "CHARACTER", "VARCHAR", "VARYING CHARACTER", "NCHAR", "CLOB"]):
            return f"'Example{random.randint(1, 100)}'"
        
        # Boolean
        elif "BOOLEAN" in col_type.upper():
            return random.choice(["0", "1"])
        
        # Date
        elif "DATE" in col_type.upper() and "TIME" not in col_type.upper():
            return f"'2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}'"
        
        # DateTime
        elif "DATETIME" in col_type.upper():
            return f"'2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d} {random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}'"
        
        # Default
        else:
            return "'example'"
    
    def generate_queries(self) -> List[str]:
        """
        Generate SQL queries covering most SQL features.
        
        Returns:
            List of valid SQL queries
        """
        queries = ["SELECT 1;"] # Add dummy query to ensure that the energy assertion in the schedule class will not fail (division by zero because of empty seed)
        
        # Add queries for each category
        queries.extend(self._generate_select_queries())
        queries.extend(self._generate_join_queries())
        queries.extend(self._generate_aggregate_queries())
        queries.extend(self._generate_subquery_queries())
        queries.extend(self._generate_insert_queries())
        queries.extend(self._generate_update_queries())
        queries.extend(self._generate_delete_queries())
        queries.extend(self._generate_order_limit_queries())
        queries.extend(self._generate_case_queries())
        queries.extend(self._generate_union_queries())
        queries.extend(self._generate_view_queries())
        queries.extend(self._generate_index_queries())
        queries.extend(self._generate_transaction_queries())
        queries.extend(self._generate_cte_queries())
        queries.extend(self._generate_function_queries())
        queries.extend(self._generate_window_function_queries())
        queries.extend(self._generate_schema_queries())
        
        return queries
    
    def _generate_select_queries(self) -> List[str]:
        """Generate basic SELECT queries."""
        queries = []
        
        # Basic SELECT queries
        for _ in range(3):
            table = self._get_random_table()
            # SELECT *
            queries.append(f"SELECT * FROM {table};")
            
            # SELECT specific columns
            columns = self._get_random_columns(table, min_count=2, max_count=4)
            columns_str = ", ".join(columns)
            queries.append(f"SELECT {columns_str} FROM {table};")
            
            # SELECT with WHERE
            column = self._get_random_column(table)
            if self._is_numeric_column(table, column):
                queries.append(f"SELECT * FROM {table} WHERE {column} > {random.randint(1, 50)};")
            elif self._is_text_column(table, column):
                queries.append(f"SELECT * FROM {table} WHERE {column} LIKE 'A%';")
            else:
                queries.append(f"SELECT * FROM {table} WHERE {column} IS NOT NULL;")
            
            # SELECT with WHERE conditions
            column1 = self._get_random_column(table)
            column2 = self._get_random_column(table)
            if column1 != column2:
                queries.append(f"SELECT * FROM {table} WHERE {column1} IS NOT NULL AND {column2} IS NOT NULL;")
                queries.append(f"SELECT * FROM {table} WHERE {column1} IS NULL OR {column2} IS NULL;")
            
            # SELECT DISTINCT
            column = self._get_random_column(table)
            queries.append(f"SELECT DISTINCT {column} FROM {table};")
        
        return queries
    
    def _generate_join_queries(self) -> List[str]:
        """Generate JOIN queries."""
        queries = []
        
        # Make sure we have at least 2 tables
        if len(self.table_names) < 2:
            return queries
        
        for _ in range(3):
            # Get two random tables
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            
            # Basic INNER JOIN
            queries.append(f"SELECT {table1}.{pk1}, {table2}.{pk2} FROM {table1} JOIN {table2} ON {table1}.{pk1} = {table2}.{pk2};")
            
            # LEFT JOIN
            queries.append(f"SELECT {table1}.{pk1}, {table2}.{pk2} FROM {table1} LEFT JOIN {table2} ON {table1}.{pk1} = {table2}.{pk2};")
            
            # Complex JOIN with table aliases
            col1 = self._get_random_column(table1)
            col2 = self._get_random_column(table2)
            queries.append(f"SELECT a.{pk1}, a.{col1}, b.{pk2}, b.{col2} FROM {table1} a JOIN {table2} b ON a.{pk1} = b.{pk2};")
        
        # If we have 3 or more tables
        if len(self.table_names) >= 3:
            # Get three random tables
            table1, table2, table3 = self._get_random_tables(3)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            pk3 = self._get_primary_key_column(table3)
            
            # Complex multi-table JOIN
            queries.append(f"""
                SELECT a.{pk1}, b.{pk2}, c.{pk3} 
                FROM {table1} a 
                JOIN {table2} b ON a.{pk1} = b.{pk2} 
                JOIN {table3} c ON b.{pk2} = c.{pk3};
            """)
            
            # Multi-table JOIN with different join types
            queries.append(f"""
                SELECT a.{pk1}, b.{pk2}, c.{pk3} 
                FROM {table1} a 
                LEFT JOIN {table2} b ON a.{pk1} = b.{pk2} 
                INNER JOIN {table3} c ON b.{pk2} = c.{pk3};
            """)
        
        # Self JOIN
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        queries.append(f"SELECT a.{pk}, b.{pk} FROM {table} a, {table} b WHERE a.{pk} < b.{pk} AND a.{col} = b.{col};")
        
        # Cross JOIN
        table1, table2 = self._get_random_tables(2)
        queries.append(f"SELECT * FROM {table1} CROSS JOIN {table2};")
        
        return queries
    
    def _generate_aggregate_queries(self) -> List[str]:
        """Generate aggregate and GROUP BY queries."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            
            # Find a numeric column for aggregations
            numeric_columns = [col for col in self.schema_info[table]["column_names"] 
                              if self._is_numeric_column(table, col)]
            
            if numeric_columns:
                numeric_col = random.choice(numeric_columns)
                
                # Simple aggregation
                queries.append(f"SELECT COUNT(*) FROM {table};")
                queries.append(f"SELECT COUNT({numeric_col}) FROM {table};")
                queries.append(f"SELECT SUM({numeric_col}) FROM {table};")
                queries.append(f"SELECT AVG({numeric_col}) FROM {table};")
                queries.append(f"SELECT MIN({numeric_col}), MAX({numeric_col}) FROM {table};")
                
                # GROUP BY
                group_col = self._get_random_column(table)
                if group_col != numeric_col:
                    queries.append(f"SELECT {group_col}, COUNT(*) FROM {table} GROUP BY {group_col};")
                    queries.append(f"SELECT {group_col}, SUM({numeric_col}) FROM {table} GROUP BY {group_col};")
                    queries.append(f"SELECT {group_col}, AVG({numeric_col}) FROM {table} GROUP BY {group_col};")
                    
                    # With HAVING
                    queries.append(f"SELECT {group_col}, COUNT(*) FROM {table} GROUP BY {group_col} HAVING COUNT(*) > 1;")
                    queries.append(f"SELECT {group_col}, SUM({numeric_col}) FROM {table} GROUP BY {group_col} HAVING SUM({numeric_col}) > 10;")
        
        return queries
    
    def _generate_subquery_queries(self) -> List[str]:
        """Generate queries with subqueries."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            # Simple subquery in WHERE
            queries.append(f"SELECT * FROM {table} WHERE {pk} IN (SELECT {pk} FROM {table} WHERE {col} IS NOT NULL);")
            
            # Subquery with comparison
            if self._is_numeric_column(table, col):
                queries.append(f"SELECT * FROM {table} WHERE {col} > (SELECT AVG({col}) FROM {table});")
            
            # Subquery in SELECT
            queries.append(f"SELECT {pk}, (SELECT COUNT(*) FROM {table} t2 WHERE t2.{pk} <= {table}.{pk}) AS count_less_equal FROM {table};")
            
            # EXISTS subquery
            queries.append(f"SELECT * FROM {table} t1 WHERE EXISTS (SELECT 1 FROM {table} t2 WHERE t2.{pk} = t1.{pk});")
            
            # NOT EXISTS subquery
            queries.append(f"SELECT * FROM {table} t1 WHERE NOT EXISTS (SELECT 1 FROM {table} t2 WHERE t2.{pk} > t1.{pk});")
            
            # Subquery in FROM
            queries.append(f"SELECT sub.{pk}, sub.{col} FROM (SELECT {pk}, {col} FROM {table} WHERE {col} IS NOT NULL) sub;")
            
            # Correlated subquery
            if len(self.table_names) >= 2:
                table2 = random.choice([t for t in self.table_names if t != table])
                pk2 = self._get_primary_key_column(table2)
                queries.append(f"SELECT t1.{pk}, (SELECT COUNT(*) FROM {table2} t2 WHERE t2.{pk2} = t1.{pk}) FROM {table} t1;")
        
        # ALL, ANY, SOME subqueries
        table = self._get_random_table()
        col = self._get_random_column(table)
        if self._is_numeric_column(table, col):
            queries.append(f"SELECT * FROM {table} WHERE {col} > ALL (SELECT {col} FROM {table} WHERE {pk} < 5);")
            queries.append(f"SELECT * FROM {table} WHERE {col} > ANY (SELECT {col} FROM {table} WHERE {pk} < 5);")
            queries.append(f"SELECT * FROM {table} WHERE {col} > SOME (SELECT {col} FROM {table} WHERE {pk} < 5);")
        
        return queries
    
    def _generate_insert_queries(self) -> List[str]:
        """Generate INSERT queries."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            columns = self._get_random_columns(table, min_count=2, max_count=4)
            columns_str = ", ".join(columns)
            
            # Generate appropriate values
            values = []
            for col in columns:
                values.append(self._get_literal_for_column(table, col))
            values_str = ", ".join(values)
            
            # Basic INSERT
            queries.append(f"INSERT INTO {table} ({columns_str}) VALUES ({values_str});")
            
            # Multiple row INSERT
            values2 = []
            for col in columns:
                values2.append(self._get_literal_for_column(table, col))
            values2_str = ", ".join(values2)
            
            queries.append(f"INSERT INTO {table} ({columns_str}) VALUES ({values_str}), ({values2_str});")
            
            # INSERT OR REPLACE
            queries.append(f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({values_str});")
            
            # INSERT OR IGNORE
            queries.append(f"INSERT OR IGNORE INTO {table} ({columns_str}) VALUES ({values_str});")
            
            # INSERT with SELECT
            queries.append(f"INSERT INTO {table} ({columns_str}) SELECT {columns_str} FROM {table} LIMIT 1;")
        
        # INSERT with RETURNING
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        queries.append(f"INSERT INTO {table} ({pk}, {col}) VALUES (999, {self._get_literal_for_column(table, col)}) RETURNING {pk}, {col};")
        
        # INSERT with ON CONFLICT
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        if self._is_numeric_column(table, col):
            queries.append(f"INSERT INTO {table} ({pk}, {col}) VALUES (1, 100) ON CONFLICT({pk}) DO UPDATE SET {col} = {col} + 1;")
            queries.append(f"INSERT INTO {table} ({pk}, {col}) VALUES (1, 100) ON CONFLICT({pk}) DO NOTHING;")
        
        return queries
    
    def _generate_update_queries(self) -> List[str]:
        """Generate UPDATE queries."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            # Basic UPDATE
            queries.append(f"UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} WHERE {pk} = 1;")
            
            # Update with expressions
            if self._is_numeric_column(table, col):
                queries.append(f"UPDATE {table} SET {col} = {col} + 10 WHERE {pk} > 0;")
                queries.append(f"UPDATE {table} SET {col} = {col} * 2 WHERE {pk} > 0;")
            
            # Update with NULL
            queries.append(f"UPDATE {table} SET {col} = NULL WHERE {pk} = 2;")
            
            # Update with CASE
            if self._is_numeric_column(table, col):
                queries.append(f"""
                UPDATE {table} SET {col} = CASE 
                    WHEN {pk} < 10 THEN {col} + 5 
                    WHEN {pk} < 20 THEN {col} + 10 
                    ELSE {col} 
                END;
                """)
            
            # Update with subquery
            queries.append(f"UPDATE {table} SET {col} = (SELECT {col} FROM {table} WHERE {pk} = 1) WHERE {pk} = 2;")
        
        # UPDATE with RETURNING
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        queries.append(f"UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} WHERE {pk} = 1 RETURNING {pk}, {col};")
        
        # UPDATE multiple columns
        table = self._get_random_table()
        columns = self._get_random_columns(table, min_count=2, max_count=3)
        set_clauses = []
        for col in columns:
            set_clauses.append(f"{col} = {self._get_literal_for_column(table, col)}")
        set_str = ", ".join(set_clauses)
        
        queries.append(f"UPDATE {table} SET {set_str} WHERE {pk} = 1;")
        
        # UPDATE with OR
        queries.append(f"UPDATE OR IGNORE {table} SET {col} = {self._get_literal_for_column(table, col)};")
        
        # UPDATE with ORDER BY and LIMIT
        queries.append(f"UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} ORDER BY {pk} DESC LIMIT 5;")
        
        return queries
    
    def _generate_delete_queries(self) -> List[str]:
        """Generate DELETE queries."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            # Basic DELETE
            queries.append(f"DELETE FROM {table} WHERE {pk} = 1;")
            
            # DELETE with complex condition
            queries.append(f"DELETE FROM {table} WHERE {pk} > 10 AND {col} IS NOT NULL;")
            
            # DELETE all rows
            queries.append(f"DELETE FROM {table};")
            
            # DELETE with subquery
            queries.append(f"DELETE FROM {table} WHERE {pk} IN (SELECT {pk} FROM {table} WHERE {col} IS NULL);")
        
        # DELETE with ORDER BY and LIMIT
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        queries.append(f"DELETE FROM {table} ORDER BY {pk} DESC LIMIT 5;")
        
        return queries
    
    def _generate_order_limit_queries(self) -> List[str]:
        """Generate queries with ORDER BY and LIMIT."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            # ORDER BY ASC
            queries.append(f"SELECT * FROM {table} ORDER BY {col} ASC;")
            
            # ORDER BY DESC
            queries.append(f"SELECT * FROM {table} ORDER BY {col} DESC;")
            
            # ORDER BY multiple columns
            col2 = self._get_random_column(table)
            if col != col2:
                queries.append(f"SELECT * FROM {table} ORDER BY {col} ASC, {col2} DESC;")
            
            # LIMIT
            queries.append(f"SELECT * FROM {table} LIMIT 10;")
            
            # LIMIT with OFFSET
            queries.append(f"SELECT * FROM {table} LIMIT 5 OFFSET 5;")
            
            # ORDER BY with LIMIT
            queries.append(f"SELECT * FROM {table} ORDER BY {col} DESC LIMIT 10;")
            
            # ORDER BY with NULLS FIRST/LAST
            queries.append(f"SELECT * FROM {table} ORDER BY {col} NULLS FIRST;")
            queries.append(f"SELECT * FROM {table} ORDER BY {col} NULLS LAST;")
            
            # ORDER BY with COLLATE
            if self._is_text_column(table, col):
                queries.append(f"SELECT * FROM {table} ORDER BY {col} COLLATE NOCASE;")
        
        return queries
    
    def _generate_case_queries(self) -> List[str]:
        """Generate queries with CASE expressions."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            # Simple CASE
            if self._is_numeric_column(table, col):
                queries.append(f"""
                SELECT {pk}, CASE 
                    WHEN {col} < 10 THEN 'Low' 
                    WHEN {col} < 50 THEN 'Medium' 
                    ELSE 'High' 
                END as category 
                FROM {table};
                """)
            
            # Searched CASE
            queries.append(f"""
            SELECT {pk}, CASE {col}
                WHEN NULL THEN 'Unknown'
                ELSE 'Known'
            END as status
            FROM {table};
            """)
            
            # CASE in ORDER BY
            queries.append(f"""
            SELECT * FROM {table}
            ORDER BY CASE
                WHEN {col} IS NULL THEN 1
                ELSE 0
            END, {pk};
            """)
        
        # CASE in UPDATE
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        if self._is_numeric_column(table, col):
            queries.append(f"""
            UPDATE {table} SET {col} = CASE
                WHEN {pk} < 10 THEN {col} + 5
                WHEN {pk} < 20 THEN {col} + 10
                ELSE {col}
            END;
            """)
        
        return queries
    
    def _generate_union_queries(self) -> List[str]:
        """Generate UNION, EXCEPT, INTERSECT queries."""
        queries = []
        
        # Make sure we have at least 2 tables
        if len(self.table_names) < 2:
            return queries
        
        for _ in range(2):
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            
            # UNION
            queries.append(f"SELECT {pk1} FROM {table1} UNION SELECT {pk2} FROM {table2};")
            
            # UNION ALL
            queries.append(f"SELECT {pk1} FROM {table1} UNION ALL SELECT {pk2} FROM {table2};")
            
            # EXCEPT
            queries.append(f"SELECT {pk1} FROM {table1} EXCEPT SELECT {pk2} FROM {table2};")
            
            # INTERSECT
            queries.append(f"SELECT {pk1} FROM {table1} INTERSECT SELECT {pk2} FROM {table2};")
        
        # Complex UNION with subqueries
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            
            queries.append(f"""
            SELECT {pk1}, 'Table1' as source FROM {table1} WHERE {pk1} < 10
            UNION
            SELECT {pk2}, 'Table2' as source FROM {table2} WHERE {pk2} < 10
            ORDER BY 1;
            """)
        
        return queries
    
    def _generate_view_queries(self) -> List[str]:
        """Generate queries for views."""
        queries = []
        
        for _ in range(2):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            columns = self._get_random_columns(table, min_count=2, max_count=3)
            columns_str = ", ".join(columns)
            
            # CREATE VIEW
            view_name = f"v_{table}_{random.randint(1, 1000)}"
            queries.append(f"CREATE VIEW {view_name} AS SELECT {columns_str} FROM {table};")
            
            # CREATE TEMPORARY VIEW
            temp_view_name = f"temp_v_{table}_{random.randint(1, 1000)}"
            queries.append(f"CREATE TEMPORARY VIEW {temp_view_name} AS SELECT {columns_str} FROM {table};")
            
            # DROP VIEW
            queries.append(f"DROP VIEW IF EXISTS {view_name};")
            
            # Create view with complex query
            complex_view_name = f"complex_v_{table}_{random.randint(1, 1000)}"
            queries.append(f"""
            CREATE VIEW {complex_view_name} AS
            SELECT {pk}, COUNT(*) as count, SUM({columns[0]}) as total
            FROM {table}
            GROUP BY {pk};
            """)
        
        # Use existing views in queries
        for view_name in self.view_names:
            col = self._get_random_column(view_name)
            queries.append(f"SELECT * FROM {view_name};")
            queries.append(f"SELECT {col} FROM {view_name} WHERE {col} IS NOT NULL;")
            
            # Join view with table
            if self.table_names:
                table = self._get_random_table()
                pk = self._get_primary_key_column(table)
                queries.append(f"SELECT v.{col}, t.{pk} FROM {view_name} v JOIN {table} t ON v.{col} = t.{pk};")
        
        return queries
    
    def _generate_index_queries(self) -> List[str]:
        """Generate queries for indexes."""
        queries = []
        
        for _ in range(2):
            table = self._get_random_table()
            column = self._get_random_column(table)
            
            # CREATE INDEX
            index_name = f"idx_{table}_{column}_{random.randint(1, 1000)}"
            queries.append(f"CREATE INDEX {index_name} ON {table}({column});")
            
            # CREATE UNIQUE INDEX
            unique_index_name = f"uix_{table}_{column}_{random.randint(1, 1000)}"
            queries.append(f"CREATE UNIQUE INDEX {unique_index_name} ON {table}({column});")
            
            # CREATE INDEX IF NOT EXISTS
            queries.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});")
            
            # DROP INDEX
            queries.append(f"DROP INDEX IF EXISTS {index_name};")
            
            # CREATE INDEX with multiple columns
            col2 = self._get_random_column(table)
            if column != col2:
                multi_index_name = f"idx_{table}_{column}_{col2}_{random.randint(1, 1000)}"
                queries.append(f"CREATE INDEX {multi_index_name} ON {table}({column}, {col2});")
            
            # CREATE INDEX with WHERE clause
            where_index_name = f"idx_{table}_{column}_where_{random.randint(1, 1000)}"
            queries.append(f"CREATE INDEX {where_index_name} ON {table}({column}) WHERE {column} IS NOT NULL;")
            
            # CREATE INDEX with COLLATE
            if self._is_text_column(table, column):
                collate_index_name = f"idx_{table}_{column}_collate_{random.randint(1, 1000)}"
                queries.append(f"CREATE INDEX {collate_index_name} ON {table}({column} COLLATE NOCASE);")
        
        # REINDEX
        table = self._get_random_table()
        queries.append(f"REINDEX {table};")
        
        # REINDEX a specific index
        index = self._get_random_index(table)
        if index:
            queries.append(f"REINDEX {index};")
        
        return queries
    
    def _generate_transaction_queries(self) -> List[str]:
        """Generate transaction queries."""
        queries = []
        
        # Basic transaction
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        queries.append(f"""
        BEGIN TRANSACTION;
        UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} WHERE {pk} = 1;
        COMMIT;
        """)
        
        # Transaction with ROLLBACK
        queries.append(f"""
        BEGIN;
        UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} WHERE {pk} = 2;
        ROLLBACK;
        """)
        
        # Transaction with SAVEPOINT
        queries.append(f"""
        BEGIN;
        UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} WHERE {pk} = 3;
        SAVEPOINT sp1;
        UPDATE {table} SET {col} = {self._get_literal_for_column(table, col)} WHERE {pk} = 4;
        ROLLBACK TO SAVEPOINT sp1;
        COMMIT;
        """)
        
        # Various transaction types
        queries.append("BEGIN IMMEDIATE TRANSACTION; COMMIT;")
        queries.append("BEGIN EXCLUSIVE TRANSACTION; COMMIT;")
        queries.append("BEGIN DEFERRED TRANSACTION; COMMIT;")
        
        # Transaction with multiple operations
        queries.append(f"""
        BEGIN TRANSACTION;
        DELETE FROM {table} WHERE {pk} = 5;
        INSERT INTO {table} ({pk}, {col}) VALUES (5, {self._get_literal_for_column(table, col)});
        COMMIT;
        """)
        
        # SAVEPOINT operations
        queries.append("SAVEPOINT sp_name; RELEASE SAVEPOINT sp_name;")
        queries.append("SAVEPOINT sp_name; ROLLBACK TO SAVEPOINT sp_name;")
        
        return queries
    
    def _generate_cte_queries(self) -> List[str]:
        """Generate queries with Common Table Expressions (WITH clause)."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            # Simple WITH clause
            queries.append(f"""
            WITH temp_data AS (
                SELECT {pk}, {col} FROM {table} WHERE {col} IS NOT NULL
            )
            SELECT * FROM temp_data;
            """)
            
            # Multiple CTEs
            col2 = self._get_random_column(table)
            if col != col2:
                queries.append(f"""
                WITH 
                data1 AS (
                    SELECT {pk}, {col} FROM {table} WHERE {col} IS NOT NULL
                ),
                data2 AS (
                    SELECT {pk}, {col2} FROM {table} WHERE {col2} IS NOT NULL
                )
                SELECT d1.{pk}, d1.{col}, d2.{col2}
                FROM data1 d1
                JOIN data2 d2 ON d1.{pk} = d2.{pk};
                """)
            
            # WITH clause with aggregation
            if self._is_numeric_column(table, col):
                queries.append(f"""
                WITH agg_data AS (
                    SELECT {col}, COUNT(*) as count, AVG({col}) as avg_val
                    FROM {table}
                    GROUP BY {col}
                )
                SELECT * FROM agg_data WHERE count > 1;
                """)
        
        # WITH RECURSIVE
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        queries.append(f"""
        WITH RECURSIVE numbers(n) AS (
            SELECT 1
            UNION ALL
            SELECT n+1 FROM numbers WHERE n < 10
        )
        SELECT n FROM numbers;
        """)
        
        # Complex WITH clause
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        queries.append(f"""
        WITH ranked_data AS (
            SELECT {pk}, {col},
                   ROW_NUMBER() OVER (ORDER BY {col}) as row_num
            FROM {table}
            WHERE {col} IS NOT NULL
        )
        SELECT * FROM ranked_data WHERE row_num <= 5;
        """)
        
        return queries
    
    def _generate_function_queries(self) -> List[str]:
        """Generate queries with SQL functions."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            
            # String functions
            text_columns = [col for col in self.schema_info[table]["column_names"] 
                           if self._is_text_column(table, col)]
            
            if text_columns:
                col = random.choice(text_columns)
                queries.append(f"SELECT UPPER({col}) FROM {table};")
                queries.append(f"SELECT LOWER({col}) FROM {table};")
                queries.append(f"SELECT LENGTH({col}) FROM {table};")
                queries.append(f"SELECT SUBSTR({col}, 1, 3) FROM {table};")
                queries.append(f"SELECT INSTR({col}, 'a') FROM {table};")
                queries.append(f"SELECT REPLACE({col}, 'a', 'A') FROM {table};")
                queries.append(f"SELECT TRIM({col}) FROM {table};")
                queries.append(f"SELECT LTRIM(RTRIM({col})) FROM {table};")
                queries.append(f"SELECT {col} || ' suffix' FROM {table};")
            
            # Numeric functions
            num_columns = [col for col in self.schema_info[table]["column_names"] 
                          if self._is_numeric_column(table, col)]
            
            if num_columns:
                col = random.choice(num_columns)
                queries.append(f"SELECT ABS({col}) FROM {table};")
                queries.append(f"SELECT ROUND({col}, 2) FROM {table};")
                queries.append(f"SELECT CEIL({col}) FROM {table};")
                queries.append(f"SELECT FLOOR({col}) FROM {table};")
                
                # Math expressions
                queries.append(f"SELECT {col} + 10 FROM {table};")
                queries.append(f"SELECT {col} * 2 FROM {table};")
                queries.append(f"SELECT {col} / NULLIF(2, 0) FROM {table};")  # Prevent division by zero
            
            # Date functions
            date_columns = [col for col in self.schema_info[table]["column_names"] 
                           if self._is_date_column(table, col)]
            
            if date_columns:
                col = random.choice(date_columns)
                queries.append(f"SELECT date({col}, '+1 day') FROM {table};")
                queries.append(f"SELECT strftime('%Y-%m-%d', {col}) FROM {table};")
                queries.append(f"SELECT datetime({col}, 'start of month') FROM {table};")
            
            # NULL handling
            col = self._get_random_column(table)
            queries.append(f"SELECT COALESCE({col}, 'N/A') FROM {table};")
            queries.append(f"SELECT NULLIF({col}, 'unknown') FROM {table};")
            queries.append(f"SELECT IFNULL({col}, 0) FROM {table};")
        
        # SQLite-specific functions
        queries.append("SELECT random();")
        queries.append("SELECT quote('string''with quotes');")
        queries.append("SELECT typeof(42), typeof('text'), typeof(3.14), typeof(NULL);")
        
        # Type casting
        table = self._get_random_table()
        col = self._get_random_column(table)
        queries.append(f"SELECT CAST({col} AS TEXT) FROM {table};")
        queries.append(f"SELECT CAST({col} AS INTEGER) FROM {table};")
        queries.append(f"SELECT CAST({col} AS REAL) FROM {table};")
        
        return queries
    
    def _generate_window_function_queries(self) -> List[str]:
        """Generate queries with window functions."""
        queries = []
        
        for _ in range(3):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            
            # Find a numeric column for window functions
            numeric_columns = [col for col in self.schema_info[table]["column_names"] 
                              if self._is_numeric_column(table, col)]
            
            if numeric_columns:
                col = random.choice(numeric_columns)
                
                # Basic window function
                queries.append(f"SELECT {pk}, {col}, AVG({col}) OVER () as avg_total FROM {table};")
                
                # Window function with PARTITION BY
                partition_col = self._get_random_column(table)
                if partition_col != col:
                    queries.append(f"SELECT {pk}, {partition_col}, {col}, AVG({col}) OVER (PARTITION BY {partition_col}) as avg_by_group FROM {table};")
                
                # Window function with ORDER BY
                queries.append(f"SELECT {pk}, {col}, SUM({col}) OVER (ORDER BY {pk}) as running_sum FROM {table};")
                
                # Window function with both PARTITION BY and ORDER BY
                if partition_col != col:
                    queries.append(f"SELECT {pk}, {partition_col}, {col}, SUM({col}) OVER (PARTITION BY {partition_col} ORDER BY {pk}) as running_sum_by_group FROM {table};")
                
                # Row numbering functions
                queries.append(f"SELECT {pk}, {col}, ROW_NUMBER() OVER (ORDER BY {col}) as row_num FROM {table};")
                queries.append(f"SELECT {pk}, {col}, RANK() OVER (ORDER BY {col}) as rank_val FROM {table};")
                queries.append(f"SELECT {pk}, {col}, DENSE_RANK() OVER (ORDER BY {col}) as dense_rank_val FROM {table};")
                
                # NTILE
                queries.append(f"SELECT {pk}, {col}, NTILE(4) OVER (ORDER BY {col}) as quartile FROM {table};")
                
                # Lead and lag
                queries.append(f"SELECT {pk}, {col}, LAG({col}, 1) OVER (ORDER BY {pk}) as prev_val FROM {table};")
                queries.append(f"SELECT {pk}, {col}, LEAD({col}, 1) OVER (ORDER BY {pk}) as next_val FROM {table};")
                
                # First_value and last_value
                queries.append(f"SELECT {pk}, {col}, FIRST_VALUE({col}) OVER (ORDER BY {pk}) as first_val FROM {table};")
                queries.append(f"SELECT {pk}, {col}, LAST_VALUE({col}) OVER (ORDER BY {pk} RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as last_val FROM {table};")
        
        return queries
    
    def _generate_schema_queries(self) -> List[str]:
        """Generate schema alteration queries."""
        queries = []
        
        # CREATE TABLE
        new_table_name = f"new_table_{random.randint(1, 1000)}"
        queries.append(f"""
        CREATE TABLE {new_table_name} (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL
        );
        """)
        
        # CREATE TABLE IF NOT EXISTS
        queries.append(f"""
        CREATE TABLE IF NOT EXISTS {new_table_name} (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value REAL
        );
        """)
        
        # CREATE TEMPORARY TABLE
        temp_table_name = f"temp_table_{random.randint(1, 1000)}"
        queries.append(f"""
        CREATE TEMPORARY TABLE {temp_table_name} (
            id INTEGER PRIMARY KEY,
            data TEXT
        );
        """)
        
        # DROP TABLE
        queries.append(f"DROP TABLE IF EXISTS {new_table_name};")
        
        # ALTER TABLE statements
        table = self._get_random_table()
        
        # ALTER TABLE ADD COLUMN
        queries.append(f"ALTER TABLE {table} ADD COLUMN new_col TEXT;")
        
        # ALTER TABLE RENAME TO
        queries.append(f"ALTER TABLE {table} RENAME TO {table}_renamed;")
        
        # ALTER TABLE RENAME COLUMN
        col = self._get_random_column(table)
        queries.append(f"ALTER TABLE {table} RENAME COLUMN {col} TO {col}_renamed;")
        
        # CREATE TABLE with constraints
        constraints_table = f"constraints_table_{random.randint(1, 1000)}"
        queries.append(f"""
        CREATE TABLE {constraints_table} (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER CHECK(age >= 18),
            category TEXT DEFAULT 'General'
        );
        """)
        
        # CREATE TABLE with foreign key
        if self.table_names:
            fk_table = self._get_random_table()
            fk_col = self._get_primary_key_column(fk_table)
            fk_ref_table = f"fk_table_{random.randint(1, 1000)}"
            queries.append(f"""
            CREATE TABLE {fk_ref_table} (
                id INTEGER PRIMARY KEY,
                {fk_table}_id INTEGER,
                name TEXT,
                FOREIGN KEY ({fk_table}_id) REFERENCES {fk_table}({fk_col})
            );
            """)
        
        # PRAGMA statements
        queries.append("PRAGMA table_info(sqlite_master);")
        
        if self.table_names:
            table = self._get_random_table()
            queries.append(f"PRAGMA table_info({table});")
            queries.append(f"PRAGMA index_list({table});")
            queries.append(f"PRAGMA foreign_key_list({table});")
        
        # Additional PRAGMA statements
        queries.append("PRAGMA journal_mode = WAL;")
        queries.append("PRAGMA synchronous = NORMAL;")
        queries.append("PRAGMA cache_size = 10000;")
        
        # CREATE TABLE without ROWID
        queries.append(f"""
        CREATE TABLE no_rowid_table_{random.randint(1, 1000)} (
            id INTEGER PRIMARY KEY,
            name TEXT
        ) WITHOUT ROWID;
        """)
        
        # CREATE trigger
        trigger_table = self._get_random_table()
        trigger_name = f"trg_{trigger_table}_{random.randint(1, 1000)}"
        queries.append(f"""
        CREATE TRIGGER {trigger_name}
        AFTER INSERT ON {trigger_table}
        BEGIN
            UPDATE {trigger_table} SET c1 = NEW.c0 WHERE c0 = NEW.c0;
        END;
        """)
        
        # DROP trigger
        queries.append(f"DROP TRIGGER IF EXISTS {trigger_name};")
        
        return queries
    