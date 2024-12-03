import sqlite3
from typing import List
from .logger import setup_logger

class DatabaseManager:
    def __init__(self, db_file: str):
        """Initialize database manager."""
        self.db_file = db_file
        self.logger = setup_logger(__name__)
        self._create_tables()
        self.logger.info(f"Database initialized at {db_file}")

    def _create_tables(self) -> None:
        """Create necessary database tables."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_domains (
                    domain TEXT PRIMARY KEY
                )
            """)
            
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) 
                VALUES 
                    ('ad_block', 'off'),
                    ('adult_block', 'off')
            """)
            
            conn.commit()
            self.logger.info("Database tables created/verified")

    def get_setting(self, setting: str) -> str:
        """Get setting value."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT value 
                              FROM settings 
                              WHERE key = ?""", (setting,))
            result = cursor.fetchone()
            value = result[0] if result else 'off'
            self.logger.debug(f"Retrieved setting {setting}: {value}")
            return value

    def update_setting(self, setting: str, value: str) -> None:
        """Update setting value."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE settings 
                SET value = ?
                WHERE key = ?
            """, (value, setting))
            conn.commit()
            self.logger.info(f"Updated setting {setting} to {value}")

    def add_blocked_domain(self, domain: str) -> None:
        """Add a domain to blocked list."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""INSERT INTO blocked_domains (domain) 
                                  VALUES (?)""", (domain,))
                conn.commit()
                self.logger.info(f"Domain {domain} added to block list")
            except sqlite3.IntegrityError:
                self.logger.warning(f"Domain {domain} already exists in the database")

    def remove_blocked_domain(self, domain: str) -> bool:
        """Remove a domain from blocked list."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""DELETE FROM blocked_domains 
                              WHERE domain = ?""", (domain,))
            conn.commit()
            if cursor.rowcount:
                self.logger.info(f"Domain {domain} removed from block list")
            else:
                self.logger.warning(f"Domain {domain} not found in block list")
            return bool(cursor.rowcount)

    def get_blocked_domains(self) -> List[str]:
        """Get list of all blocked domains."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT domain 
                              FROM blocked_domains""")
            domains = [row[0] for row in cursor.fetchall()]
            self.logger.debug(f"Retrieved {len(domains)} blocked domains")
            return domains

    def is_domain_blocked(self, domain: str) -> bool:

        """Check if domain is in blocked list."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT 1 
                              FROM blocked_domains 
                              WHERE domain = ?""", (domain,))
            is_blocked = cursor.fetchone() is not None
            self.logger.debug(f"Domain {domain} blocked status: {is_blocked}")
            return is_blocked