import threading
import requests
import json
from datetime import datetime, timedelta
from typing import Optional
from .db_manager import DatabaseManager
from .config import EASYLIST_URL
from .filter_rules import FilterRule

class EasyListManager:
    def __init__(self, db_manager: DatabaseManager, update_interval: int = 24) -> None:
        """
        Initialize EasyList manager.
        
        Args:
            db_manager: Database manager instance
            update_interval: Update interval in hours (default: 24)
        """
        self.db_manager = db_manager
        self.update_interval = update_interval
        self.update_timer: Optional[threading.Timer] = None
        self.running = True

    def start_update_scheduler(self) -> None:
        """Start the update scheduler."""
        self.schedule_next_update()

    def stop_update_scheduler(self) -> None:
        """Stop the update scheduler."""
        self.running = False
        if self.update_timer:
            self.update_timer.cancel()

    def schedule_next_update(self) -> None:
        """Schedule the next update."""
        if not self.running:
            return

        # Schedule next update
        self.update_timer = threading.Timer(
            self.update_interval * 3600,  # Convert hours to seconds
            self._perform_update
        )
        self.update_timer.daemon = True
        self.update_timer.start()

    def _perform_update(self) -> None:
        """Perform the EasyList update."""
        try:
            print("Starting EasyList update...")
            
            # Download new EasyList
            response = requests.get(EASYLIST_URL)
            response.raise_for_status()
            
            # Parse rules
            rules = []
            for line in response.text.split('\n'):
                line = line.strip()
                if line and not line.startswith('!') and not line.startswith('['):
                    try:
                        rule = FilterRule(line)
                        rules.append((
                            rule.raw_pattern,
                            rule.pattern_type.value,
                            rule.processed_pattern,
                            json.dumps(rule.options)
                        ))
                    except Exception as e:
                        print(f"Error parsing rule '{line}': {e}")
                        continue

            # Update database
            self.db_manager.clear_easylist()
            self.db_manager.store_easylist_entries(rules)
            
            print(f"EasyList updated with {len(rules)} rules")
            
        except Exception as e:
            print(f"Error updating EasyList: {e}")
        finally:
            self.schedule_next_update()

    def force_update(self) -> None:
        """Force an immediate update."""
        self._perform_update()