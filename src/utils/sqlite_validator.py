import sqlite3
from typing import Optional, Tuple


class SQLiteValidator:
    """
    Class to validate SQLite queries.
    """
    
    def __init__(self):
        """Initialize the SQLite validator."""
        # Create an in-memory database for syntax checking
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        
        # Create a dummy schema for validation
        self._create_validation_schema()
    
    def _create_validation_schema(self) -> None:
        """Create a dummy schema for query validation."""
        # Create the same schema as our test databases
        schema_sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            joined_date TEXT,
            score REAL
        );
        
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL,
            category TEXT,
            stock INTEGER DEFAULT 0
        );
        
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        """
        
        self.cursor.executescript(schema_sql)
        self.conn.commit()
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query for syntax correctness.
        
        Args:
            query: The SQL query to validate
            
        Returns:
            A tuple of (is_valid, error_message)
        """
        try:
            # Handle multiple statements
            if ";" in query:
                # For scripts with multiple statements, validate each one
                statements = query.split(";")
                for stmt in statements:
                    stmt = stmt.strip()
                    if stmt:  # Skip empty statements
                        self._validate_single_statement(stmt)
            else:
                self._validate_single_statement(query)
            
            return True, None
            
        except sqlite3.Error as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _validate_single_statement(self, statement: str) -> None:
        """
        Validate a single SQL statement.
        
        Args:
            statement: The SQL statement to validate
        """
        statement = statement.strip()
        if not statement:
            return
        
        # Handle different types of statements
        statement_upper = statement.upper()
        
        if statement_upper.startswith("SELECT"):
            # For SELECT statements, use EXPLAIN QUERY PLAN
            self.cursor.execute(f"EXPLAIN QUERY PLAN {statement}")
        elif statement_upper.startswith(("INSERT", "UPDATE", "DELETE")):
            # For DML statements, wrap in a transaction and rollback
            self.conn.execute("BEGIN TRANSACTION")
            try:
                self.cursor.execute(statement)
            finally:
                self.conn.execute("ROLLBACK")
        elif statement_upper.startswith(("CREATE INDEX", "DROP INDEX")):
            # For index operations, just check syntax without execution
            # SQLite will validate the syntax without creating the index
            self.cursor.execute(f"EXPLAIN {statement}")
        elif statement_upper.startswith(("BEGIN", "COMMIT", "ROLLBACK")):
            # Transaction commands are always valid in this context
            pass
        else:
            # For other statements, use EXPLAIN
            self.cursor.execute(f"EXPLAIN {statement}")
    
    def close(self):
        """Close the database connection."""
        # Check if the connection is open before closing
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.conn = None
        self.cursor = None
        self.schema = None
