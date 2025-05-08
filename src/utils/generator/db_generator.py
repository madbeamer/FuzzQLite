import os
import sqlite3
import random
import string
import shutil
import json
import re
import subprocess
from typing import List, Dict

class DBGenerator:
    """
    Class to generate SQLite databases with IDENTICAL schema but different data.
    Ensures both small.db and edge_cases.db have the exact same tables and structure.
    """
    
    def __init__(self, db_dir: str = "databases"):
        """
        Initialize the database generator.
        
        Args:
            db_dir: Directory to store generated databases
        """
        self.db_dir = db_dir
        
        # Create the database directory if it doesn't exist
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Available SQLite data types
        self.data_types = [
            "INTEGER", "INT", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT", 
            "UNSIGNED BIG INT", "INT2", "INT8", "TEXT", "CHARACTER", "VARCHAR", 
            "VARYING CHARACTER", "NCHAR", "NATIVE CHARACTER", "NVARCHAR", "CLOB", 
            "REAL", "DOUBLE", "DOUBLE PRECISION", "FLOAT", "NUMERIC", "DECIMAL", 
            "BOOLEAN", "DATE", "DATETIME", "BLOB", "NONE"
        ]
    
    def generate_databases(self) -> List[str]:
        """
        Generate databases with IDENTICAL SCHEMA but different data.
        
        Returns:
            List of paths to generated databases
        """
        db_configs = [
            ("small.db", "small"),
            ("edge_cases.db", "edge_cases")
        ]
        
        db_paths = []
        
        # STEP 1: First generate a common schema definition
        schema_definition = self._generate_random_schema()
        
        # STEP 2: Create each database using the SAME schema but different data
        for db_name, size in db_configs:
            db_path = os.path.join(self.db_dir, db_name)
            
            # Create database with the common schema
            self._create_database_with_schema(db_path, schema_definition, size)
            db_paths.append(db_path)
            
            # Create a backup copy
            backup_path = os.path.join(self.db_dir, f"{os.path.splitext(db_name)[0]}_copy.db")
            shutil.copy2(db_path, backup_path)
        
        # STEP 3: Generate schema JSON based on the first database
        schema_json_path = os.path.join(self.db_dir, "schema_info.json")
        schema_info = self._extract_schema_from_db(db_paths[0])
        
        with open(schema_json_path, 'w') as f:
            json.dump(schema_info, f, indent=2)
        
        return db_paths
    
    def _generate_random_schema(self) -> List[Dict]:
        """
        Generate a random schema definition to be used for all databases.
        
        Returns:
            List of table definitions
        """
        tables = []
        
        # Generate 10 tables
        for table_idx in range(10):
            table_name = f"t{table_idx}"
            
            # Random number of columns (between 3 and 10)
            num_columns = random.randint(3, 10)
            
            # Generate column definitions
            columns = []
            for col_idx in range(num_columns):
                col_name = f"c{col_idx}"
                data_type = random.choice(self.data_types)
                
                # First column is primary key
                is_primary_key = (col_idx == 0)
                
                columns.append({
                    "name": col_name,
                    "type": data_type,
                    "primary_key": is_primary_key
                })
            
            # Determine which columns will have indices (30% chance for non-PK columns)
            indices = []
            for col_idx in range(1, num_columns):
                if random.random() < 0.3:
                    col_name = f"c{col_idx}"
                    index_name = f"idx_{table_name}_{col_idx}"
                    indices.append({
                        "name": index_name,
                        "column": col_name
                    })
            
            # Decide if we should create a view (20% chance per table)
            view = None
            if random.random() < 0.2:
                view_name = f"v{table_idx}"
                # Select up to 3 random columns for the view
                view_column_count = min(3, num_columns)
                view_column_indices = random.sample(range(num_columns), view_column_count)
                view_columns = [columns[idx]["name"] for idx in view_column_indices]
                
                view = {
                    "name": view_name,
                    "columns": view_columns
                }
            
            # Add table definition to list
            tables.append({
                "name": table_name,
                "columns": columns,
                "indices": indices,
                "view": view
            })
        
        return tables
    
    def _create_database_with_schema(self, db_path: str, schema: List[Dict], size: str) -> None:
        """
        Create a database with the predefined schema and fill it with data.
        
        Args:
            db_path: Path to create the database
            schema: Schema definition (list of table definitions)
            size: Size of data to generate
        """
        # Remove existing file if present
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Create new database
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            
            # Create tables, indices, and views
            for table_def in schema:
                table_name = table_def["name"]
                
                # Create table
                column_defs = []
                for col in table_def["columns"]:
                    col_def = f"{col['name']} {col['type']}"
                    if col["primary_key"]:
                        col_def += " PRIMARY KEY"
                    column_defs.append(col_def)
                
                create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
                cursor.execute(create_table_sql)
                
                # Create indices
                for idx in table_def["indices"]:
                    index_name = idx["name"]
                    column_name = idx["column"]
                    cursor.execute(f"CREATE INDEX {index_name} ON {table_name}({column_name})")
                
                # Create view if present
                if table_def["view"]:
                    view_name = table_def["view"]["name"]
                    view_columns = table_def["view"]["columns"]
                    columns_str = ", ".join(view_columns)
                    cursor.execute(f"CREATE VIEW {view_name} AS SELECT {columns_str} FROM {table_name}")
            
            conn.commit()
            
            # Generate data
            self._generate_data(conn, size)
        
        finally:
            conn.close()
    
    def _generate_data(self, conn: sqlite3.Connection, size: str) -> None:
        """
        Generate random data for the database.
        
        Args:
            conn: SQLite database connection
            size: Size of the data to generate (small, edge_cases)
        """
        cursor = conn.cursor()
        rows_per_table = 50 if size == "small" else 20
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table_name in tables:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            column_types = {}
            
            for col in cursor.fetchall():
                col_name = col[1]  # Column name
                col_type = col[2]  # Column type
                columns.append(col_name)
                column_types[col_name] = col_type
            
            # Insert random data
            for _ in range(rows_per_table):
                values = []
                
                for col_name in columns:
                    col_type = column_types.get(col_name, "TEXT")
                    
                    if size == "edge_cases" and random.random() < 0.2:
                        value = self._generate_edge_case_value(col_type)
                    else:
                        value = self._generate_random_value(col_type)
                    
                    values.append(value)
                
                # Insert data
                try:
                    placeholders = ', '.join(['?' for _ in columns])
                    cursor.execute(
                        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})",
                        values
                    )
                except sqlite3.Error:
                    # Skip on error (constraint violations, etc.)
                    pass
        
        conn.commit()
    
    def _extract_schema_from_db(self, db_path: str) -> Dict:
        """
        Extract the schema directly from the database.
        
        Args:
            db_path: Path to the SQLite database file
            
        Returns:
            Dictionary with complete schema information
        """
        schema_info = {}
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Process each table
        for table_name in tables:
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            column_names = []
            column_types = {}
            
            for col in cursor.fetchall():
                col_name = col[1]  # Column name
                col_type = col[2]  # Column type
                column_names.append(col_name)
                column_types[col_name] = col_type
            
            # Get index information
            cursor.execute(f"PRAGMA index_list({table_name})")
            index_names = []
            
            for idx in cursor.fetchall():
                index_name = idx[1]  # Index name
                index_names.append(index_name)
            
            # Store schema info
            schema_info[table_name] = {
                "table_name": [table_name],
                "column_names": column_names,
                "column_types": column_types,
                "index_names": index_names
            }
        
        # Process views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        
        for view_name in views:
            # Get view definition
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name=?", (view_name,))
            view_sql = cursor.fetchone()[0]
            
            # Extract base table
            match = re.search(r'FROM\s+(\w+)', view_sql)
            base_table = match.group(1) if match else "unknown"
            
            # Get view columns
            cursor.execute(f"PRAGMA table_info({view_name})")
            view_columns = []
            view_column_types = {}
            
            for col in cursor.fetchall():
                col_name = col[1]
                col_type = col[2]
                view_columns.append(col_name)
                view_column_types[col_name] = col_type
            
            # Store view info
            schema_info[view_name] = {
                "table_name": [view_name],
                "column_names": view_columns,
                "column_types": view_column_types,
                "index_names": [],
                "is_view": True,
                "base_table": base_table
            }
        
        conn.close()
        return schema_info
    
    def _verify_schemas_identical(self, db_path1: str, db_path2: str) -> None:
        """
        Verify that two databases have identical schemas.
        
        Args:
            db_path1: Path to the first database
            db_path2: Path to the second database
        """
        # Extract schemas for both databases
        schema1 = self._extract_schema_from_db(db_path1)
        schema2 = self._extract_schema_from_db(db_path2)
        
        # Compare tables
        tables1 = set(schema1.keys())
        tables2 = set(schema2.keys())
        
        if tables1 != tables2:
            print("ERROR: Databases have different tables!")
            print(f"Only in {db_path1}: {tables1 - tables2}")
            print(f"Only in {db_path2}: {tables2 - tables1}")
            return
        
        for table_name in tables1:
            if "is_view" in schema1[table_name] and schema1[table_name]["is_view"]:
                # Skip views for now
                continue
                
            # Compare columns
            cols1 = schema1[table_name]["column_names"]
            cols2 = schema2[table_name]["column_names"]
            
            if cols1 != cols2:
                print(f"ERROR: Table {table_name} has different columns!")
                print(f"{db_path1}: {cols1}")
                print(f"{db_path2}: {cols2}")
            
            # Compare column types
            types1 = schema1[table_name]["column_types"]
            types2 = schema2[table_name]["column_types"]
            
            for col in cols1:
                if col in types2 and types1[col] != types2[col]:
                    print(f"ERROR: Column {table_name}.{col} has different types!")
                    print(f"{db_path1}: {types1[col]}")
                    print(f"{db_path2}: {types2[col]}")
            
            # Compare indices
            idx1 = set(schema1[table_name]["index_names"])
            idx2 = set(schema2[table_name]["index_names"])
            
            if idx1 != idx2:
                print(f"ERROR: Table {table_name} has different indices!")
                print(f"{db_path1}: {sorted(idx1)}")
                print(f"{db_path2}: {sorted(idx2)}")
                print(f"Only in {db_path1}: {idx1 - idx2}")
                print(f"Only in {db_path2}: {idx2 - idx1}")

    def _verify_schema_match(self, db_path: str, json_path: str) -> None:
        """
        Verify that the JSON schema matches the database schema.
        
        Args:
            db_path: Path to the SQLite database
            json_path: Path to the JSON schema file
        """
        # Load JSON schema
        with open(json_path, 'r') as f:
            schema_json = json.load(f)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check each table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        db_tables = [row[0] for row in cursor.fetchall()]
        
        for table_name in db_tables:
            # Make sure table is in JSON
            if table_name not in schema_json:
                print(f"ERROR: Table {table_name} is in database but missing from JSON!")
                continue
            
            # Get exact columns from database
            cursor.execute(f"PRAGMA table_info({table_name})")
            db_columns = [row[1] for row in cursor.fetchall()]
            
            json_columns = schema_json[table_name]["column_names"]
            
            # Compare column lists directly
            if db_columns != json_columns:
                print(f"MISMATCH: Columns for table {table_name} don't match!")
                print(f"DB columns: {db_columns}")
                print(f"JSON columns: {json_columns}")
                
                # Find differences
                db_column_set = set(db_columns)
                json_column_set = set(json_columns)
                
                missing = db_column_set - json_column_set
                extra = json_column_set - db_column_set
                
                if missing:
                    print(f"Missing in JSON: {missing}")
                if extra:
                    print(f"Extra in JSON: {extra}")
            
            # Get exact indices from database
            cursor.execute(f"PRAGMA index_list({table_name})")
            db_indices = [row[1] for row in cursor.fetchall()]
            
            json_indices = schema_json[table_name]["index_names"]
            
            # Compare index lists
            if set(db_indices) != set(json_indices):
                print(f"MISMATCH: Indices for table {table_name} don't match!")
                print(f"DB indices: {sorted(db_indices)}")
                print(f"JSON indices: {sorted(json_indices)}")
                
                # Find differences
                db_index_set = set(db_indices)
                json_index_set = set(json_indices)
                
                missing = db_index_set - json_index_set
                extra = json_index_set - db_index_set
                
                if missing:
                    print(f"Missing in JSON: {missing}")
                if extra:
                    print(f"Extra in JSON: {extra}")
        
        # Check views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        db_views = [row[0] for row in cursor.fetchall()]
        
        for view_name in db_views:
            # Make sure view is in JSON
            if view_name not in schema_json:
                print(f"ERROR: View {view_name} is in database but missing from JSON!")
                continue
            
            # Get exact columns from database
            cursor.execute(f"PRAGMA table_info({view_name})")
            db_columns = [row[1] for row in cursor.fetchall()]
            
            json_columns = schema_json[view_name]["column_names"]
            
            # Compare column lists directly
            if db_columns != json_columns:
                print(f"MISMATCH: Columns for view {view_name} don't match!")
                print(f"DB columns: {db_columns}")
                print(f"JSON columns: {json_columns}")
                
                # Find differences
                db_column_set = set(db_columns)
                json_column_set = set(json_columns)
                
                missing = db_column_set - json_column_set
                extra = json_column_set - db_column_set
                
                if missing:
                    print(f"Missing in JSON: {missing}")
                if extra:
                    print(f"Extra in JSON: {extra}")
        
        # Close connection
        conn.close()
    
    def _generate_random_value(self, data_type: str):
        """Generate a random value appropriate for the given data type."""
        
        # Integer types
        if any(int_type in data_type.upper() for int_type in ["INTEGER", "INT", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT"]):
            if "TINY" in data_type.upper():
                return random.randint(-128, 127)
            elif "SMALL" in data_type.upper():
                return random.randint(-32768, 32767)
            elif "MEDIUM" in data_type.upper():
                return random.randint(-8388608, 8388607)
            else:
                return random.randint(-2147483648, 2147483647)
        
        # Text types
        elif any(text_type in data_type.upper() for text_type in ["TEXT", "CHARACTER", "VARCHAR", "CLOB", "CHAR"]):
            safe_chars = string.ascii_letters + string.digits + ' ,.!?-_'
            length = random.randint(5, 20)
            return ''.join(random.choices(safe_chars, k=length))
        
        # Float types
        elif any(float_type in data_type.upper() for float_type in ["REAL", "DOUBLE", "FLOAT", "NUMERIC", "DECIMAL"]):
            return round(random.uniform(-100, 100), 2)
        
        # Boolean
        elif "BOOLEAN" in data_type.upper():
            return random.choice([0, 1])
        
        # Date
        elif "DATE" in data_type.upper() and "TIME" not in data_type.upper():
            year = random.randint(2000, 2023)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            return f"{year}-{month:02d}-{day:02d}"
        
        # DateTime
        elif "DATETIME" in data_type.upper():
            year = random.randint(2000, 2023)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
        
        # Blob
        elif "BLOB" in data_type.upper():
            return bytes([random.randint(0, 127) for _ in range(random.randint(1, 10))])
        
        # None/NULL
        elif "NONE" in data_type.upper():
            return None
        
        # Default
        else:
            return f"Default-{random.randint(1, 100)}"
    
    def _generate_edge_case_value(self, data_type: str):
        """Generate an edge case value for the given data type."""
        
        # 25% chance of NULL for any type
        if random.random() < 0.25:
            return None
            
        # Integer types
        if any(int_type in data_type.upper() for int_type in ["INTEGER", "INT", "TINYINT", "SMALLINT", "MEDIUMINT", "BIGINT"]):
            return random.choice([0, -1, 1, -32768, 32767, -2147483648, 2147483647])
        
        # Text types
        elif any(text_type in data_type.upper() for text_type in ["TEXT", "CHARACTER", "VARCHAR", "CLOB", "CHAR"]):
            return random.choice(["", "NULL", "NA", "0", "-1", "A" * 20, "Test with spaces", "Comma, period. dash-underscore_"])
        
        # Float types
        elif any(float_type in data_type.upper() for float_type in ["REAL", "DOUBLE", "FLOAT", "NUMERIC", "DECIMAL"]):
            return random.choice([0.0, -0.0, 1.0, -1.0, 3.14159, 2.71828, 0.00001, 99999.99])
        
        # Boolean
        elif "BOOLEAN" in data_type.upper():
            return random.choice([0, 1])
        
        # Date
        elif "DATE" in data_type.upper() and "TIME" not in data_type.upper():
            return random.choice(["1970-01-01", "2000-01-01", "2023-12-31", "2023-02-28"])
        
        # DateTime
        elif "DATETIME" in data_type.upper():
            return random.choice(["1970-01-01 00:00:00", "2000-01-01 00:00:00", "2023-12-31 23:59:59", "2023-01-01 12:30:45"])
        
        # Blob
        elif "BLOB" in data_type.upper():
            choice = random.randint(1, 3)
            if choice == 1:
                return bytes()
            elif choice == 2:
                return bytes([0] * 5)
            else:
                return bytes([65] * 5)
        
        # None/NULL
        elif "NONE" in data_type.upper():
            return None
        
        # Default
        else:
            return None
