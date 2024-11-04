# db_manager.py

import sqlite3
from typing import List, Tuple


class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.create_tables()

    def create_tables(self) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS easylist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry TEXT UNIQUE
                )
            """)
            conn.commit()

    def add_blocked_domain(self, domain: str) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO blocked_domains (domain)
                    VALUES (?)
                """, (domain,))
                conn.commit()
            except sqlite3.IntegrityError:
                print(f"Domain {domain} already exists in the database.")

    def remove_blocked_domain(self, domain: str) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM blocked_domains
                WHERE domain = ?
            """, (domain,))
            conn.commit()

    def is_domain_blocked(self, domain: str) -> bool:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT domain FROM blocked_domains
                WHERE domain = ?
            """, (domain,))
            result = cursor.fetchone()
            return result is not None

    def store_easylist_entries(self, entries: List[Tuple[str]]) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR IGNORE INTO easylist (entry)
                VALUES (?)
            """, entries)
            conn.commit()

    def is_easylist_blocked(self, domain: str) -> bool:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM easylist
                WHERE ? GLOB '*' || entry || '*'
            """, (domain,))
            result = cursor.fetchone()
            return result is not None

    def clear_easylist(self) -> None:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM easylist")
            conn.commit()

    def close(self) -> None:
        pass