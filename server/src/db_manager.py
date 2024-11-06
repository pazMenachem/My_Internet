import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._connection_lock = threading.Lock()
        self.create_tables()

    def create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Existing tables with enhancements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE,
                    timestamp TEXT,
                    reason TEXT,
                    active BOOLEAN DEFAULT TRUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS easylist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry TEXT UNIQUE,
                    category TEXT,
                    timestamp TEXT
                )
            """)
            
            # New tables for state management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_states (
                    feature TEXT PRIMARY KEY,
                    state TEXT,
                    last_updated TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS client_sessions (
                    client_id TEXT PRIMARY KEY,
                    last_sync TEXT,
                    connected BOOLEAN,
                    last_updated TEXT
                )
            """)
            
            # Initialize feature states if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO feature_states (feature, state, last_updated)
                VALUES 
                    ('ad_block', 'off', ?),
                    ('adult_block', 'off', ?)
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()

    def get_feature_state(self, feature: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a feature."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT state, last_updated
                    FROM feature_states
                    WHERE feature = ?
                """, (feature,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "state": result[0],
                        "last_updated": result[1]
                    }
                return None

    def update_feature_state(self, feature: str, state: str) -> None:
        """Update the state of a feature."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE feature_states
                    SET state = ?, last_updated = ?
                    WHERE feature = ?
                """, (state, datetime.now().isoformat(), feature))
                conn.commit()

    def add_blocked_domain(self, domain: str, reason: str = "manual") -> None:
        """Add a domain to blocked list with metadata."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO blocked_domains (domain, timestamp, reason, active)
                        VALUES (?, ?, ?, TRUE)
                    """, (domain, datetime.now().isoformat(), reason))
                    conn.commit()
                except sqlite3.IntegrityError:
                    cursor.execute("""
                        UPDATE blocked_domains
                        SET active = TRUE, timestamp = ?, reason = ?
                        WHERE domain = ?
                    """, (datetime.now().isoformat(), reason, domain))
                    conn.commit()

    def remove_blocked_domain(self, domain: str) -> bool:
        """Soft delete a domain from blocked list."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE blocked_domains
                    SET active = FALSE, timestamp = ?
                    WHERE domain = ?
                """, (datetime.now().isoformat(), domain))
                conn.commit()
                return cursor.rowcount > 0

    def get_blocked_domains(self) -> List[Dict[str, Any]]:
        """Get all active blocked domains with their metadata."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT domain, timestamp, reason
                    FROM blocked_domains
                    WHERE active = TRUE
                """)
                return [
                    {
                        "domain": row[0],
                        "timestamp": row[1],
                        "reason": row[2]
                    }
                    for row in cursor.fetchall()
                ]

    def store_easylist_entries(self, entries: List[tuple[str, str]]) -> None:
        """Store easylist entries with categories."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()
                cursor.executemany("""
                    INSERT OR REPLACE INTO easylist (entry, category, timestamp)
                    VALUES (?, ?, ?)
                """, [(entry, category, timestamp) for entry, category in entries])
                conn.commit()

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if a domain is manually blocked."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM blocked_domains
                    WHERE domain = ? AND active = TRUE
                """, (domain,))
                return cursor.fetchone() is not None

    def is_easylist_blocked(self, domain: str) -> bool:
        """Check if a domain matches any easylist pattern."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM easylist
                    WHERE ? GLOB '*' || entry || '*'
                """, (domain,))
                return cursor.fetchone() is not None

    def register_client(self, client_id: str) -> None:
        """Register or update a client session."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                timestamp = datetime.now().isoformat()
                cursor.execute("""
                    INSERT OR REPLACE INTO client_sessions
                    (client_id, last_sync, connected, last_updated)
                    VALUES (?, ?, TRUE, ?)
                """, (client_id, timestamp, timestamp))
                conn.commit()

    def unregister_client(self, client_id: str) -> None:
        """Mark a client as disconnected."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE client_sessions
                    SET connected = FALSE, last_updated = ?
                    WHERE client_id = ?
                """, (datetime.now().isoformat(), client_id))
                conn.commit()

    def clear_easylist(self) -> None:
        """Clear all easylist entries."""
        with self._connection_lock:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM easylist")
                conn.commit()

    def close(self) -> None:
        """Clean up resources."""
        pass  