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
        queries.extend(self._generate_materialized_queries())
        queries.extend(self._generate_nested_queries())
        
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
        """Generate JOIN queries, including complex and unusual join patterns."""
        queries = []
        
        # Make sure we have at least 2 tables
        if len(self.table_names) < 2:
            return queries
        
        # --- Standard JOIN queries  ---
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
        
        # --- More complex JOIN queries ---
        # Weird chained JOIN pattern
        if len(self.table_names) >= 3:
            table1, table2, table3 = self._get_random_tables(3)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            pk3 = self._get_primary_key_column(table3)
            col1 = self._get_random_column(table1)
            
            # Chained JOIN with mixed types and no explicit ON clause for the last join
            queries.append(f"""
                SELECT 1 as count 
                FROM {table1} 
                INNER JOIN {table2} ON {table1}.{pk1} = {table2}.{pk2}
                RIGHT OUTER JOIN {table3} ON {table2}.{pk2} = {table3}.{pk3}
                ORDER BY {table1}.{col1};
            """)
            
            # Another weird join pattern with multiple conditions
            queries.append(f"""
                SELECT {table1}.{pk1}, {table2}.{pk2}, {table3}.{pk3}
                FROM {table1}
                LEFT JOIN {table2} ON {table1}.{pk1} = {table2}.{pk2}
                INNER JOIN {table3} ON {table1}.{col1} = {table3}.{pk3}
                WHERE {table2}.{pk2} IS NULL OR {table3}.{pk3} > 10;
            """)
        
        # Complex JOIN with a view if available
        if self.view_names and len(self.table_names) >= 2:
            view = self._get_random_view()
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            view_col = self._get_random_column(view)
            
            # Join with a view
            queries.append(f"""
                SELECT {table1}.{pk1}, v.{view_col}, {table2}.{pk2}
                FROM {table1}
                INNER JOIN {view} v ON {table1}.{pk1} = v.{view_col}
                LEFT OUTER JOIN {table2} ON v.{view_col} = {table2}.{pk2}
                ORDER BY {table1}.{pk1};
            """)
        
        # NATURAL JOIN
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            queries.append(f"SELECT * FROM {table1} NATURAL JOIN {table2};")
            queries.append(f"SELECT * FROM {table1} NATURAL LEFT JOIN {table2};")
        
        # JOIN with USING clause
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            pk = self._get_primary_key_column(table1)  # Assuming same PK name
            queries.append(f"SELECT * FROM {table1} JOIN {table2} USING ({pk});")
        
        # Complex multi-level JOIN structure
        if len(self.table_names) >= 4:
            tables = self._get_random_tables(4)
            pks = [self._get_primary_key_column(t) for t in tables]
            
            queries.append(f"""
                SELECT t1.{pks[0]}, t2.{pks[1]}, t3.{pks[2]}, t4.{pks[3]}
                FROM {tables[0]} t1
                LEFT JOIN (
                    {tables[1]} t2 
                    INNER JOIN {tables[2]} t3 ON t2.{pks[1]} = t3.{pks[2]}
                ) ON t1.{pks[0]} = t2.{pks[1]}
                RIGHT OUTER JOIN {tables[3]} t4 ON t3.{pks[2]} = t4.{pks[3]};
            """)
        
        # JOIN with a derived table/subquery
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        col = self._get_random_column(table)
        
        queries.append(f"""
            SELECT t.{pk}, d.avg_value
            FROM {table} t
            JOIN (
                SELECT {col}, AVG({pk}) as avg_value
                FROM {table}
                GROUP BY {col}
                HAVING COUNT(*) > 1
            ) d ON t.{col} = d.{col}
            WHERE t.{pk} > d.avg_value;
        """)
        
        # JOIN with CASE expression in the ON clause
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            col1 = self._get_random_column(table1)
            col2 = self._get_random_column(table2)
            
            queries.append(f"""
                SELECT t1.{pk1}, t2.{pk2}
                FROM {table1} t1
                LEFT JOIN {table2} t2 ON 
                    CASE 
                        WHEN t1.{col1} IS NULL THEN t1.{pk1} = t2.{pk2}
                        ELSE t1.{col1} = t2.{col2}
                    END
                WHERE t1.{pk1} < 100;
            """)
        
        # Multiple chained JOINs with mixed styles and complex conditions
        if len(self.table_names) >= 3:
            table1, table2, table3 = self._get_random_tables(3)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            pk3 = self._get_primary_key_column(table3)
            col1 = self._get_random_column(table1)
            col2 = self._get_random_column(table2)
            col3 = self._get_random_column(table3)
            
            # Extremely complex nested JOIN structure
            queries.append(f"""
                SELECT 
                    t1.{pk1}, 
                    t2.{pk2}, 
                    t3.{pk3},
                    CASE WHEN t2.{col2} IS NULL THEN 'Missing' ELSE 'Present' END as status
                FROM {table1} t1
                LEFT JOIN {table2} t2 
                    ON t1.{pk1} = t2.{pk2} AND t1.{col1} IS NOT NULL
                RIGHT JOIN (
                    SELECT * FROM {table3}
                    WHERE {pk3} IN (
                        SELECT {pk3} FROM {table3} WHERE {col3} > 0
                    )
                ) t3 
                    ON t2.{col2} = t3.{col3} OR (t2.{pk2} = t3.{pk3} AND t2.{col2} IS NULL)
                WHERE (t1.{pk1} % 2 = 0 OR t3.{pk3} % 2 = 1)
                ORDER BY 
                    CASE 
                        WHEN t1.{pk1} IS NULL THEN t3.{pk3}
                        ELSE t1.{pk1}
                    END;
            """)
            
            # JOIN chain with lateral join-like pattern
            queries.append(f"""
                SELECT t1.{pk1}, t2.{pk2}, t3.{pk3}, grp.cnt
                FROM {table1} t1
                JOIN {table2} t2 
                    ON t1.{pk1} = t2.{pk2}
                LEFT JOIN {table3} t3 
                    ON t2.{pk2} = t3.{pk3}
                JOIN (
                    SELECT {col1}, COUNT(*) as cnt
                    FROM {table1} 
                    GROUP BY {col1}
                ) grp 
                    ON t1.{col1} = grp.{col1}
                WHERE t3.{col3} < (
                    SELECT AVG({col3}) FROM {table3}
                    WHERE {pk3} IN (
                        SELECT {pk2} FROM {table2}
                        WHERE {col2} = t1.{col1}
                    )
                );
            """)
        
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
        # queries.append("SELECT random();")
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
    
    def _generate_materialized_queries(self) -> List[str]:
        """
        Generate queries with explicit MATERIALIZED and NOT MATERIALIZED hints,
        along with other advanced SQL features.
        """
        queries = []
        
        # Example with explicit MATERIALIZED
        queries.append("""
            WITH t(a) AS MATERIALIZED (SELECT json('{"x": 10}'))
            SELECT json_extract(a, '$.x') FROM t;
        """)
        
        # Multiple CTEs with different materialization strategies
        queries.append("""
            WITH 
            t1(a) AS MATERIALIZED (SELECT 1),
            t2(b) AS NOT MATERIALIZED (SELECT 2),
            t3(c) AS (SELECT 3)
            SELECT t1.a, t2.b, t3.c FROM t1, t2, t3;
        """)
        
        # --- Materialization with dynamic data ---
        
        # Get some tables and columns for building dynamic queries
        if self.table_names:
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            cols = self._get_random_columns(table, min_count=2, max_count=3)
            
            # CTE with materialization and table data
            queries.append(f"""
                WITH data AS MATERIALIZED (
                    SELECT {pk}, {', '.join(cols)}
                    FROM {table}
                    WHERE {pk} < 100
                )
                SELECT * FROM data
                WHERE {cols[0]} IS NOT NULL;
            """)
            
            # Multiple CTEs with mixed materialization
            col1 = cols[0]
            col2 = cols[1] if len(cols) > 1 else cols[0]
            
            queries.append(f"""
                WITH 
                raw_data AS MATERIALIZED (
                    SELECT {pk}, {col1}, {col2}
                    FROM {table}
                    WHERE {pk} > 0
                ),
                aggregated AS NOT MATERIALIZED (
                    SELECT {col1}, COUNT(*) as count, SUM({pk}) as total
                    FROM raw_data
                    GROUP BY {col1}
                ),
                filtered AS (
                    SELECT * FROM aggregated
                    WHERE count > 1
                )
                SELECT 
                    r.{pk},
                    r.{col1},
                    a.count,
                    f.total
                FROM raw_data r
                LEFT JOIN aggregated a ON r.{col1} = a.{col1}
                LEFT JOIN filtered f ON a.{col1} = f.{col1};
            """)
        
        # --- Complex materialized queries with functions and expressions ---
        
        # JSON functions with NOT MATERIALIZED
        queries.append("""
            WITH 
            json_data(doc) AS NOT MATERIALIZED (
                SELECT json('{"id": 123, "values": [1, 2, 3], "nested": {"key": "value"}}')
            ),
            extracted(id, first_val, key_val) AS MATERIALIZED (
                SELECT 
                    json_extract(doc, '$.id'),
                    json_extract(doc, '$.values[0]'),
                    json_extract(doc, '$.nested.key')
                FROM json_data
            )
            SELECT * FROM extracted;
        """)
        
        # Math functions with materialization
        queries.append("""
            WITH 
            numbers(n) AS MATERIALIZED (
                SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5
            ),
            calculations AS NOT MATERIALIZED (
                SELECT 
                    n,
                    n*n as squared,
                    pow(n, 3) as cubed,
                    sqrt(n) as square_root
                FROM numbers
            )
            SELECT * FROM calculations
            ORDER BY n;
        """)
        
        # Date functions
        queries.append("""
            WITH 
            dates(d) AS MATERIALIZED (
                SELECT date('now') UNION ALL
                SELECT date('now', '+1 day') UNION ALL
                SELECT date('now', '+2 days') UNION ALL
                SELECT date('now', '+1 month') UNION ALL
                SELECT date('now', '+1 year')
            ),
            formatted AS NOT MATERIALIZED (
                SELECT 
                    d,
                    strftime('%Y', d) as year,
                    strftime('%m', d) as month,
                    strftime('%d', d) as day
                FROM dates
            )
            SELECT * FROM formatted;
        """)
        
        # Recursive CTE with materialization
        queries.append("""
            WITH RECURSIVE 
            fibonacci(a, b) AS NOT MATERIALIZED (
                SELECT 0, 1
                UNION ALL
                SELECT b, a+b FROM fibonacci
                WHERE b < 100
            )
            SELECT a as fibonacci_number FROM fibonacci;
        """)
        
        # --- Combination of materialization with other advanced features ---
        
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            col1 = self._get_random_column(table1)
            col2 = self._get_random_column(table2)
            
            # Materialization + Window functions + Join
            queries.append(f"""
                WITH 
                t1_data AS MATERIALIZED (
                    SELECT 
                        {pk1}, 
                        {col1},
                        ROW_NUMBER() OVER(ORDER BY {pk1}) as row_num,
                        RANK() OVER(ORDER BY {col1}) as rank_val
                    FROM {table1}
                    WHERE {col1} IS NOT NULL
                ),
                t2_data AS NOT MATERIALIZED (
                    SELECT 
                        {pk2}, 
                        {col2},
                        COUNT(*) OVER(PARTITION BY {col2}) as count_in_group
                    FROM {table2}
                    WHERE {col2} IS NOT NULL
                )
                SELECT 
                    t1.{pk1},
                    t1.{col1},
                    t1.row_num,
                    t2.{col2},
                    t2.count_in_group
                FROM t1_data t1
                LEFT JOIN t2_data t2 ON t1.{pk1} = t2.{pk2}
                WHERE t1.rank_val <= 10
                ORDER BY t1.row_num;
            """)
            
            # Materialization + Subqueries + CASE
            queries.append(f"""
                WITH 
                base_data AS MATERIALIZED (
                    SELECT * FROM {table1}
                    WHERE {pk1} IN (
                        SELECT {pk2} FROM {table2}
                        WHERE {col2} IS NOT NULL
                    )
                ),
                categories AS NOT MATERIALIZED (
                    SELECT 
                        {pk1},
                        CASE 
                            WHEN {col1} < 10 THEN 'Low'
                            WHEN {col1} < 50 THEN 'Medium'
                            ELSE 'High'
                        END as category
                    FROM base_data
                )
                SELECT 
                    category,
                    COUNT(*) as count,
                    MIN({col1}) as min_value,
                    MAX({col1}) as max_value,
                    AVG({col1}) as avg_value
                FROM categories
                GROUP BY category
                ORDER BY count DESC;
            """)
        
        # Advanced nested materialization pattern
        if self.table_names:
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            col = self._get_random_column(table)
            
            queries.append(f"""
                WITH RECURSIVE
                counter(n) AS NOT MATERIALIZED (
                    SELECT 1
                    UNION ALL
                    SELECT n+1 FROM counter
                    WHERE n < 5
                ),
                data(group_id, value) AS MATERIALIZED (
                    SELECT 
                        (({pk} - 1) % 5) + 1,
                        {col}
                    FROM {table}
                    WHERE {col} IS NOT NULL
                ),
                grouped_data AS NOT MATERIALIZED (
                    SELECT 
                        c.n as group_id,
                        (
                            SELECT json_group_array(value)
                            FROM data
                            WHERE group_id = c.n
                        ) as values_json
                    FROM counter c
                )
                SELECT 
                    group_id,
                    json_array_length(values_json) as count,
                    values_json
                FROM grouped_data
                WHERE json_array_length(values_json) > 0;
            """)
        
        # --- Super complex materialized query ---
        
        if len(self.table_names) >= 3:
            table1, table2, table3 = self._get_random_tables(3)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            pk3 = self._get_primary_key_column(table3)
            col1 = self._get_random_column(table1)
            col2 = self._get_random_column(table2)
            col3 = self._get_random_column(table3)
            
            queries.append(f"""
                WITH 
                t1_base AS MATERIALIZED (
                    SELECT 
                        {pk1}, 
                        {col1},
                        NTILE(4) OVER(ORDER BY {col1}) as quartile
                    FROM {table1}
                    WHERE {col1} IS NOT NULL
                ),
                t2_base AS NOT MATERIALIZED (
                    SELECT 
                        {pk2}, 
                        {col2},
                        CASE 
                            WHEN {col2} < 10 THEN 'A'
                            WHEN {col2} < 50 THEN 'B'
                            ELSE 'C'
                        END as category
                    FROM {table2}
                    WHERE {col2} IS NOT NULL
                ),
                t3_base AS MATERIALIZED (
                    SELECT * FROM {table3}
                    WHERE {col3} > (SELECT AVG({col3}) FROM {table3})
                ),
                quartile_stats AS NOT MATERIALIZED (
                    SELECT 
                        quartile,
                        COUNT(*) as count,
                        AVG({col1}) as avg_val
                    FROM t1_base
                    GROUP BY quartile
                ),
                category_stats AS MATERIALIZED (
                    SELECT 
                        category,
                        COUNT(*) as count,
                        SUM({col2}) as total
                    FROM t2_base
                    GROUP BY category
                ),
                joined_data AS NOT MATERIALIZED (
                    SELECT 
                        t1.{pk1},
                        t1.quartile,
                        q.avg_val as quartile_avg,
                        t2.{pk2},
                        t2.category,
                        c.total as category_total,
                        t3.{pk3}
                    FROM t1_base t1
                    JOIN quartile_stats q ON t1.quartile = q.quartile
                    LEFT JOIN t2_base t2 ON t1.{pk1} = t2.{pk2}
                    LEFT JOIN category_stats c ON t2.category = c.category
                    LEFT JOIN t3_base t3 ON t2.{pk2} = t3.{pk3}
                    WHERE (t1.{col1} > q.avg_val OR t2.category = 'A')
                    AND (t3.{pk3} IS NULL OR t3.{col3} > 0)
                )
                SELECT 
                    quartile,
                    category,
                    COUNT(*) as count,
                    SUM(quartile_avg) as sum_quartile_avg,
                    AVG(category_total) as avg_category_total,
                    JSON_GROUP_ARRAY({pk1}) as ids_json
                FROM joined_data
                GROUP BY quartile, category
                HAVING count > 1
                ORDER BY quartile, category;
            """)
        
        return queries
    
    def _generate_nested_queries(self) -> List[str]:
        """
        Generate complex nested queries with multiple levels (depth) of nesting.
        Incorporates various SQL features like subqueries, CTEs, joins, aggregates
        and window functions at different nesting depths.
        """
        queries = []
        
        # --- Simple Nested Subqueries (Level 2) ---
        for _ in range(2):
            table = self._get_random_table()
            pk = self._get_primary_key_column(table)
            
            # Get two distinct columns
            columns = self._get_random_columns(table, min_count=2, max_count=2)
            col1 = columns[0]
            col2 = columns[1]
            
            # Nested WHERE subquery
            queries.append(f"""
            SELECT {pk}, {col1} 
            FROM {table}
            WHERE {col2} IN (
                SELECT {col2} 
                FROM {table} 
                WHERE {col1} IS NOT NULL AND {pk} < 100
            );
            """)
            
            # FROM clause subquery with filtering
            queries.append(f"""
            SELECT outer_query.{pk}, outer_query.row_num
            FROM (
                SELECT {pk}, {col1}, 
                    ROW_NUMBER() OVER(ORDER BY {col1}) as row_num
                FROM {table}
                WHERE {col2} IS NOT NULL
            ) outer_query
            WHERE outer_query.row_num < 10;
            """)
        
        # --- Double Nested Subqueries (Level 3) ---
        for _ in range(2):
            if len(self.table_names) >= 2:
                table1, table2 = self._get_random_tables(2)
                pk1 = self._get_primary_key_column(table1)
                pk2 = self._get_primary_key_column(table2)
                col1 = self._get_random_column(table1)
                col2 = self._get_random_column(table2)
                
                # Level 3 nesting with multiple features
                queries.append(f"""
                SELECT t1.{pk1}, t1.{col1},
                    (SELECT COUNT(*) 
                    FROM {table2} t2 
                    WHERE t2.{pk2} IN (
                        SELECT t3.{pk2} 
                        FROM {table2} t3 
                        WHERE t3.{col2} > t1.{col1} AND t3.{pk2} < 50
                    )
                    ) as related_count
                FROM {table1} t1
                WHERE t1.{col1} IS NOT NULL;
                """)
                
                # Level 3 nesting with different features
                queries.append(f"""
                SELECT * FROM (
                    SELECT t1.{pk1}, t1.{col1}, 
                        (SELECT AVG(t3.{col2}) 
                            FROM {table2} t3 
                            WHERE t3.{pk2} < t1.{pk1}) as avg_value
                    FROM {table1} t1
                    JOIN (
                        SELECT * FROM {table2}
                        WHERE {col2} IS NOT NULL
                    ) t2 ON t1.{pk1} = t2.{pk2}
                ) complex_data
                WHERE avg_value IS NOT NULL;
                """)
        
        # --- Complex WITH Clause and Nested Subqueries (Level 3+) ---
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            col1 = self._get_random_column(table1)
            numeric_cols = [col for col in self.schema_info[table1]["column_names"] 
                            if self._is_numeric_column(table1, col)]
            
            if numeric_cols:
                num_col = random.choice(numeric_cols)
                
                # WITH clauses + nesting
                queries.append(f"""
                WITH 
                base_data AS (
                    SELECT {pk1}, {col1}, {num_col}
                    FROM {table1}
                    WHERE {num_col} IS NOT NULL
                ),
                aggregated AS (
                    SELECT {col1}, 
                        AVG({num_col}) as avg_val,
                        COUNT(*) as count
                    FROM base_data
                    GROUP BY {col1}
                    HAVING COUNT(*) > 1
                )
                SELECT a.{col1}, a.avg_val, a.count,
                    (SELECT COUNT(*) 
                    FROM {table2} t 
                    WHERE t.{pk2} IN (
                        SELECT b.{pk1} 
                        FROM base_data b 
                        WHERE b.{col1} = a.{col1}
                    )
                    ) as related_items
                FROM aggregated a
                WHERE a.avg_val > (
                    SELECT AVG(avg_val) FROM aggregated
                )
                ORDER BY a.avg_val DESC;
                """)
        
        # --- Super Complex Nested Queries (Level 4+) ---
        if len(self.table_names) >= 3:
            table1, table2, table3 = self._get_random_tables(3)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            pk3 = self._get_primary_key_column(table3)
            
            # Get columns for each table
            col1 = self._get_random_column(table1)
            col2 = self._get_random_column(table2)
            col3 = self._get_random_column(table3)
            
            # Deeply nested with multiple features
            queries.append(f"""
            WITH RECURSIVE 
            counter(n) AS (
                SELECT 1
                UNION ALL
                SELECT n+1 FROM counter WHERE n < 5
            ),
            filtered_t1 AS (
                SELECT {pk1}, {col1},
                    RANK() OVER(ORDER BY {col1}) as rank_val
                FROM {table1}
                WHERE {col1} IS NOT NULL
            )
            SELECT c.n, f.{pk1}, f.{col1}, 
                (SELECT COUNT(*) 
                    FROM {table2} t2 
                    WHERE t2.{pk2} IN (
                        SELECT t3.{pk3} 
                        FROM {table3} t3 
                        LEFT JOIN (
                            SELECT {pk2}, {col2} 
                            FROM {table2}
                            WHERE {col2} > f.{col1}
                        ) subq ON t3.{pk3} = subq.{pk2}
                        WHERE t3.{col3} IS NOT NULL
                        GROUP BY t3.{pk3}
                        HAVING COUNT(*) > c.n
                    )
                ) as nested_count
            FROM counter c
            CROSS JOIN filtered_t1 f
            WHERE f.rank_val <= 3
            ORDER BY c.n, f.rank_val;
            """)
            
            # Complex nested window functions and aggregates
            queries.append(f"""
            WITH 
            t1_stats AS (
                SELECT {col1}, 
                    COUNT(*) as count,
                    AVG({pk1}) as avg_pk
                FROM {table1}
                GROUP BY {col1}
            ),
            t2_derived AS (
                SELECT {pk2}, {col2},
                    CASE 
                        WHEN {col2} IS NULL THEN 'Unknown'
                        WHEN {col2} < 50 THEN 'Low'
                        ELSE 'High'
                    END as category
                FROM {table2}
            )
            SELECT main.*, 
                (SELECT AVG(count) FROM t1_stats) as overall_avg,
                (
                    SELECT COUNT(*) FROM (
                        SELECT t3.{pk3}, 
                                LAG(t3.{col3}) OVER(ORDER BY t3.{pk3}) as prev_val,
                                LEAD(t3.{col3}) OVER(ORDER BY t3.{pk3}) as next_val
                        FROM {table3} t3
                        WHERE t3.{pk3} IN (
                            SELECT td.{pk2} FROM t2_derived td
                            WHERE td.category = main.category
                            UNION
                            SELECT ts.avg_pk FROM t1_stats ts
                            WHERE ts.{col1} = main.{col1}
                        )
                    ) complex_window
                    WHERE complex_window.prev_val IS NOT NULL
                    OR complex_window.next_val IS NOT NULL
                ) as window_matches
            FROM (
                SELECT ts.{col1}, td.category,
                    ts.count, ts.avg_pk,
                    DENSE_RANK() OVER(PARTITION BY td.category ORDER BY ts.count DESC) as rank_in_category
                FROM t1_stats ts
                CROSS JOIN (
                    SELECT DISTINCT category FROM t2_derived
                ) td
            ) main
            WHERE main.rank_in_category <= 2
            ORDER BY main.category, main.rank_in_category;
            """)
        
        # --- CTE with Deep Nesting and Multiple Features ---
        if len(self.table_names) >= 2:
            table1, table2 = self._get_random_tables(2)
            pk1 = self._get_primary_key_column(table1)
            pk2 = self._get_primary_key_column(table2)
            
            # Get distinct columns for table1
            t1_columns = self._get_random_columns(table1, min_count=2, max_count=2)
            col1a = t1_columns[0]
            col1b = t1_columns[1]
            
            col2 = self._get_random_column(table2)
            
            # CTE with subquery and window function combinations
            queries.append(f"""
            WITH 
            base_data AS (
                SELECT {pk1}, {col1a}, {col1b},
                    ROW_NUMBER() OVER(PARTITION BY {col1a} ORDER BY {pk1}) as row_num,
                    NTILE(4) OVER(ORDER BY {col1b}) as quartile
                FROM {table1}
                WHERE {col1a} IS NOT NULL AND {col1b} IS NOT NULL
            ),
            quartile_stats AS (
                SELECT quartile, 
                    COUNT(*) as count,
                    AVG({col1b}) as avg_value
                FROM base_data
                GROUP BY quartile
            )
            SELECT 
                bd.{pk1},
                bd.{col1a},
                bd.{col1b},
                bd.quartile,
                qs.avg_value as quartile_avg,
                (bd.{col1b} - qs.avg_value) as diff_from_avg,
                (
                    SELECT COUNT(*) 
                    FROM {table2} t2
                    WHERE t2.{pk2} IN (
                        SELECT t2_inner.{pk2}
                        FROM {table2} t2_inner
                        WHERE t2_inner.{col2} BETWEEN bd.{col1b} - 10 AND bd.{col1b} + 10
                    )
                    AND t2.{col2} IS NOT NULL
                ) as related_count,
                CASE 
                    WHEN bd.row_num = 1 THEN 'First'
                    WHEN bd.row_num <= 3 THEN 'Top 3'
                    ELSE 'Other'
                END as position_group
            FROM base_data bd
            JOIN quartile_stats qs ON bd.quartile = qs.quartile
            WHERE bd.row_num <= (
                SELECT MAX(row_num)/2 FROM base_data WHERE quartile = bd.quartile
            )
            ORDER BY bd.quartile, bd.row_num;
            """)
        
        # --- Combine Multiple Techniques in One Query ---
        table = self._get_random_table()
        pk = self._get_primary_key_column(table)
        
        # Get two distinct columns
        columns = self._get_random_columns(table, min_count=2, max_count=2)
        col1 = columns[0]
        col2 = columns[1]
        
        # Nested UNION, window functions, aggregates, and filtering
        queries.append(f"""
        WITH 
        partitioned_data AS (
            SELECT {pk}, {col1}, {col2},
                NTILE(3) OVER(ORDER BY {col1}) as segment
            FROM {table}
            WHERE {col1} IS NOT NULL
        ),
        segment_stats AS (
            SELECT segment, 
                COUNT(*) as count,
                MIN({col1}) as min_val,
                MAX({col1}) as max_val
            FROM partitioned_data
            GROUP BY segment
        )
        SELECT 
            'Segment ' || pd.segment as group_name,
            pd.{pk},
            pd.{col1},
            pd.{col2},
            ss.min_val,
            ss.max_val,
            (
                SELECT COUNT(*)
                FROM (
                    SELECT {pk} FROM {table} WHERE {col1} < pd.{col1}
                    UNION ALL
                    SELECT {pk} FROM {table} WHERE {col2} > pd.{col2}
                )
            ) as combined_count
        FROM partitioned_data pd
        JOIN segment_stats ss ON pd.segment = ss.segment
        WHERE pd.{col1} > (
            SELECT AVG({col1})
            FROM partitioned_data
            WHERE segment = pd.segment
        )
        ORDER BY pd.segment, pd.{col1} DESC;
        """)
        
        return queries
    