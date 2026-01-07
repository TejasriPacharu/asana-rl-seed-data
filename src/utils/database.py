"""
Database utilities for SQLite operations.
Handles connection, table creation, and bulk inserts.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Any, Dict
from dataclasses import asdict, fields

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Open database connection."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
        logger.info(f"Connected to database: {self.db_path}")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def execute_script(self, script_path: str):
        """Execute SQL script file.
        
        Args:
            script_path: Path to SQL script file
        """
        with open(script_path, 'r') as f:
            script = f.read()
        self.cursor.executescript(script)
        self.conn.commit()
        logger.info(f"Executed script: {script_path}")
    
    def insert_one(self, table: str, entity: Any) -> None:
        """Insert a single entity into table.
        
        Args:
            table: Table name
            entity: Dataclass entity to insert
        """
        data = asdict(entity)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
    
    def insert_many(self, table: str, entities: List[Any]) -> None:
        """Bulk insert entities into table.
        
        Args:
            table: Table name
            entities: List of dataclass entities to insert
        """
        if not entities:
            return
        
        # Get columns from first entity
        data = asdict(entities[0])
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        # Convert all entities to tuples
        values = [tuple(asdict(e).values()) for e in entities]
        
        self.cursor.executemany(sql, values)
        self.conn.commit()
        logger.info(f"Inserted {len(entities)} rows into {table}")
    
    def insert_dict(self, table: str, data: Dict[str, Any]) -> None:
        """Insert a dictionary into table.
        
        Args:
            table: Table name
            data: Dictionary of column:value pairs
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(sql, values)
    
    def insert_dicts(self, table: str, data_list: List[Dict[str, Any]]) -> None:
        """Bulk insert dictionaries into table.
        
        Args:
            table: Table name
            data_list: List of dictionaries to insert
        """
        if not data_list:
            return
        
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in data_list[0]])
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        values = [tuple(d.values()) for d in data_list]
        
        self.cursor.executemany(sql, values)
        self.conn.commit()
        logger.info(f"Inserted {len(data_list)} rows into {table}")
    
    def query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and return results.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            List of result rows
        """
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()
    
    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row:
        """Execute query and return single result.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            Single result row or None
        """
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()
    
    def count(self, table: str) -> int:
        """Count rows in table.
        
        Args:
            table: Table name
            
        Returns:
            Row count
        """
        result = self.query_one(f"SELECT COUNT(*) as cnt FROM {table}")
        return result['cnt'] if result else 0
    
    def commit(self):
        """Commit current transaction."""
        self.conn.commit()
    
    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables.
        
        Returns:
            Dictionary of table_name: row_count
        """
        tables = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        counts = {}
        for table in tables:
            counts[table['name']] = self.count(table['name'])
        return counts
    
    def print_summary(self):
        """Print summary of all table counts."""
        counts = self.get_table_counts()
        logger.info("=" * 50)
        logger.info("DATABASE SUMMARY")
        logger.info("=" * 50)
        total = 0
        for table, count in sorted(counts.items()):
            logger.info(f"  {table}: {count:,} rows")
            total += count
        logger.info("-" * 50)
        logger.info(f"  TOTAL: {total:,} rows")
        logger.info("=" * 50)