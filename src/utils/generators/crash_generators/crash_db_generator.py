#!/usr/bin/env python3
"""
Database Generator

This module generates a minimal SQLite database for testing a specific SQL query.
"""

import os
import sqlite3
from typing import List

class DatabaseGenerator:
    """
    Class to generate a minimal SQLite database.
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
    
    def create_minimal_schema(self, conn: sqlite3.Connection) -> None:
        """
        Create a minimal schema with just the specified query.
        
        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()
        
        # Execute the specified query
        cursor.execute("CREATE TABLE t1(aaa, UNIQUE(aaA), UNIQUE(aAa), UNIQUE(aAA), CHECK(Aaa>0))")
        
        # The ALTER TABLE statement would fail when executed, so we don't include it here
        # It's included in the corpus for testing but not in the actual schema creation
        
        conn.commit()
    
    def generate_databases(self) -> List[str]:
        """
        Generate a minimal database.
        
        Returns:
            List of paths to generated databases
        """
        db_name = "minimal.db"
        db_path = os.path.join(self.db_dir, db_name)
        
        # Remove existing file if present
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Create new database
        conn = sqlite3.connect(db_path)
        try:
            self.create_minimal_schema(conn)
            return [db_path]
        finally:
            conn.close()
            