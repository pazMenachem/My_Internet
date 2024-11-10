import sqlite3
import json
from typing import List, Dict, Any, Optional
import requests
from .filter_rules import FilterRule, PatternType

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.create_tables()

    def create_tables(self) -> None:
        """Create the necessary tables if they don't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Drop existing indices first to avoid conflicts
            cursor.execute("DROP INDEX IF EXISTS idx_pattern_type")
            cursor.execute("DROP INDEX IF EXISTS idx_processed_pattern")
            
            # Drop existing tables to ensure clean schema
            cursor.execute("DROP TABLE IF EXISTS easylist")
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS easylist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_pattern TEXT UNIQUE,
                    pattern_type TEXT NOT NULL,
                    processed_pattern TEXT NOT NULL,
                    options TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    setting TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Initialize settings
            cursor.execute("""
                INSERT OR IGNORE INTO settings (setting, value)
                VALUES 
                    ('ad_block', 'off'),
                    ('adult_block', 'off')
            """)
            
            # Create indices after tables are created
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pattern_type 
                ON easylist(pattern_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_pattern 
                ON easylist(processed_pattern)
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

    def store_filter_rule(self, rule: FilterRule) -> None:
        """Store a single filter rule in easylist table."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO easylist 
                (raw_pattern, pattern_type, processed_pattern, options)
                VALUES (?, ?, ?, ?)
            """, (
                rule.raw_pattern,
                rule.pattern_type.value,
                rule.processed_pattern,
                json.dumps(rule.options)
            ))
            conn.commit()

    def store_easylist_entries(self, entries: List[str]) -> None:
        """Store easylist entries with proper pattern parsing."""
        rules = []
        for entry in entries:
            try:
                rule = FilterRule(entry)
                rules.append((
                    rule.raw_pattern,
                    rule.pattern_type.value,
                    rule.processed_pattern,
                    json.dumps(rule.options)
                ))
            except Exception as e:
                print(f"Error parsing rule '{entry}': {e}")
                continue

        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO easylist 
                (raw_pattern, pattern_type, processed_pattern, options)
                VALUES (?, ?, ?, ?)
            """, rules)
            conn.commit()

    def is_easylist_blocked(self, domain: str) -> bool:
        """Check if domain matches any easylist pattern."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # First check exceptions
            cursor.execute("""
                SELECT raw_pattern, pattern_type, processed_pattern, options 
                FROM easylist 
                WHERE pattern_type = ?
            """, (PatternType.EXCEPTION.value,))
            
            for row in cursor.fetchall():
                rule = FilterRule(row[0])
                if rule.matches(domain, domain):  # Using domain as both URL and domain
                    print(f"Domain {domain} matched exception rule: {row[0]}")
                    return False
            
            # Then check blocking rules
            cursor.execute("""
                SELECT raw_pattern, pattern_type, processed_pattern, options 
                FROM easylist 
                WHERE pattern_type != ?
            """, (PatternType.EXCEPTION.value,))
            
            for row in cursor.fetchall():
                rule = FilterRule(row[0])
                if rule.matches(domain, domain):
                    print(f"Domain {domain} matched blocking rule: {row[0]}")
                    return True
            
            print(f"Domain {domain} did not match any patterns")
            return False

    def clear_easylist(self) -> None:
        """Clear all easylist entries."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM easylist")
            conn.commit()