import sqlite3
from typing import List, Dict, Any, Optional
import requests

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.create_tables()

    def create_tables(self) -> None:
        """Create the necessary tables if they don't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Blocked domains table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE
                )
            """)
            
            # Easylist entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS easylist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry TEXT UNIQUE
                )
            """)
            
            # Settings table for toggles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    setting TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Initialize settings if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO settings (setting, value)
                VALUES 
                    ('ad_block', 'off'),
                    ('adult_block', 'off')
            """)
            
            conn.commit()

    def get_setting(self, setting: str) -> str:
        """Get setting value."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE setting = ?", (setting,))
            result = cursor.fetchone()
            return result[0] if result else 'off'

    def update_setting(self, setting: str, value: str) -> None:
        """Update setting value."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE settings 
                SET value = ?
                WHERE setting = ?
            """, (value, setting))
            conn.commit()

    def add_blocked_domain(self, domain: str) -> None:
        """Add a domain to blocked list."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO blocked_domains (domain) VALUES (?)", (domain,))
                conn.commit()
            except sqlite3.IntegrityError:
                print(f"Domain {domain} already exists in the database.")

    def remove_blocked_domain(self, domain: str) -> bool:
        """Remove a domain from blocked list."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM blocked_domains WHERE domain = ?", (domain,))
            conn.commit()
            return cursor.rowcount > 0

    def get_blocked_domains(self) -> List[str]:
        """Get list of all blocked domains."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT domain FROM blocked_domains")
            return [row[0] for row in cursor.fetchall()]

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if domain is in blocked list."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM blocked_domains WHERE domain = ?", (domain,))
            return cursor.fetchone() is not None

    def store_easylist_entries(self, entries: List[tuple]) -> None:
        """Store easylist entries."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT OR IGNORE INTO easylist (entry) VALUES (?)", 
                entries
            )
            conn.commit()

    def is_easylist_blocked(self, domain: str) -> bool:
        """Check if domain matches any easylist pattern."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM easylist WHERE ? GLOB '*' || entry || '*'", 
                (domain,)
            )
            return cursor.fetchone() is not None

    def clear_easylist(self) -> None:
        """Clear all easylist entries."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM easylist")
            conn.commit()