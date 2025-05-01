import os
import sqlite3
import random
import string
import shutil
from typing import List, Dict, Any

class DBGenerator:
    """
    Class to generate multiple SQLite databases with standard schema.
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
        
        # Standard schema definition
        self.schema = {
            "users": [
                "id INTEGER PRIMARY KEY",
                "name TEXT NOT NULL",
                "email TEXT UNIQUE",
                "age INTEGER",
                "joined_date TEXT",
                "score REAL"
            ],
            "products": [
                "id INTEGER PRIMARY KEY",
                "name TEXT NOT NULL",
                "price REAL",
                "category TEXT",
                "stock INTEGER DEFAULT 0"
            ],
            "orders": [
                "id INTEGER PRIMARY KEY",
                "user_id INTEGER",
                "product_id INTEGER",
                "quantity INTEGER",
                "order_date TEXT",
                "FOREIGN KEY(user_id) REFERENCES users(id)",
                "FOREIGN KEY(product_id) REFERENCES products(id)"
            ],
            "reviews": [
                "id INTEGER PRIMARY KEY",
                "user_id INTEGER",
                "product_id INTEGER",
                "rating INTEGER CHECK(rating >= 1 AND rating <= 5)",
                "comment TEXT",
                "FOREIGN KEY(user_id) REFERENCES users(id)",
                "FOREIGN KEY(product_id) REFERENCES products(id)"
            ]
        }
    
    def create_schema(self, conn: sqlite3.Connection) -> None:
        """
        Create the standard schema in a database.
        
        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()
        
        # Create each table
        for table_name, columns in self.schema.items():
            sql = f"CREATE TABLE {table_name} ({', '.join(columns)})"
            cursor.execute(sql)
        
        # Create some indexes
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX idx_products_category ON products(category)")
        cursor.execute("CREATE INDEX idx_orders_user ON orders(user_id)")
        cursor.execute("CREATE INDEX idx_orders_product ON orders(product_id)")
        
        conn.commit()
    
    def generate_random_data(self, conn: sqlite3.Connection, size: str = "small") -> None:
        """
        Generate random data for the database.
        
        Args:
            conn: SQLite database connection
            size: "empty", "small", "large", "edge_cases"
        """
        cursor = conn.cursor()
        
        if size == "empty":
            return  # Schema only, no data
        
        # Data size configurations
        sizes = {
            "small": {"users": 10, "products": 20, "orders": 50, "reviews": 30},
            "large": {"users": 1000, "products": 500, "orders": 5000, "reviews": 2000},
            "edge_cases": {"users": 50, "products": 100, "orders": 200, "reviews": 100}
        }
        
        config = sizes.get(size)
        
        # Generate users
        for i in range(config["users"]):
            name = ''.join(random.choices(string.ascii_letters, k=8))
            email = f"{name.lower()}@example.com"
            age = random.randint(0, 100) if size != "edge_cases" else random.choice([None, -2147483648, 0, 2147483647])
            joined_date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            score = random.uniform(0, 100) if size != "edge_cases" else random.choice([None, -999999.99, 0.0, 999999.99])
            
            try:
                cursor.execute("INSERT INTO users (name, email, age, joined_date, score) VALUES (?, ?, ?, ?, ?)",
                              (name, email, age, joined_date, score))
            except sqlite3.IntegrityError:
                # Skip entries that violate constraints
                continue
        
        # Generate products
        categories = ["Electronics", "Books", "Clothing", "Food", "Other"]
        for i in range(config["products"]):
            name = f"Product_{i+1}"
            price = random.uniform(1, 1000) if size != "edge_cases" else random.choice([None, -999999.99, 0.0, 999999.99])
            category = random.choice(categories) if size != "edge_cases" else random.choice(categories + [None, "", "🔥"])
            stock = random.randint(0, 100) if size != "edge_cases" else random.choice([None, -2147483648, 0, 2147483647])
            
            try:
                cursor.execute("INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)",
                              (name, price, category, stock))
            except sqlite3.IntegrityError:
                # Skip entries that violate constraints
                continue
        
        # Generate orders
        for i in range(config["orders"]):
            user_id = random.randint(1, config["users"])
            product_id = random.randint(1, config["products"])
            quantity = random.randint(1, 10) if size != "edge_cases" else random.choice([None, -2147483648, 0, 2147483647])
            order_date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            
            try:
                cursor.execute("INSERT INTO orders (user_id, product_id, quantity, order_date) VALUES (?, ?, ?, ?)",
                              (user_id, product_id, quantity, order_date))
            except sqlite3.IntegrityError:
                # Skip entries that violate constraints
                continue
        
        # Generate reviews
        for i in range(config["reviews"]):
            user_id = random.randint(1, config["users"])
            product_id = random.randint(1, config["products"])
            
            rating = random.randint(1, 5)
            comment = ''.join(random.choices(string.ascii_letters + ' ', k=50)) if size != "edge_cases" else random.choice([None, "", "X" * 10000, "Good! 👍🔥"])
            
            try:
                cursor.execute("INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?, ?, ?, ?)",
                              (user_id, product_id, rating, comment))
            except sqlite3.IntegrityError:
                # Skip entries that violate constraints
                continue
        
        conn.commit()
    
    def generate_databases(self) -> List[str]:
        """
        Generate all database variants and their backups.
        
        Returns:
            List of paths to generated databases (excluding backup copies)
        """
        db_configs = [
            ("empty.db", "empty"),
            ("small.db", "small"),
            ("large.db", "large"),
            ("edge_cases.db", "edge_cases")
        ]
        
        db_paths = []
        
        for db_name, size in db_configs:
            db_path = os.path.join(self.db_dir, db_name)
            
            # Remove existing file if present
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Create new database
            conn = sqlite3.connect(db_path)
            try:
                self.create_schema(conn)
                self.generate_random_data(conn, size)
                db_paths.append(db_path)
                
                # Create a backup copy
                backup_path = os.path.join(self.db_dir, f"{os.path.splitext(db_name)[0]}_copy.db")
                shutil.copy2(db_path, backup_path)
            finally:
                conn.close()
        
        return db_paths
    