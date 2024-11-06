from typing import Dict, Any, Optional
from datetime import datetime
import threading
from .db_manager import DatabaseManager

class StateManager:
    """Manages application state including feature toggles and domain states."""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
        self._state_lock = threading.Lock()
        self._states = {
            "settings": {
                "ad_block": {
                    "state": "off",
                    "last_updated": datetime.now().isoformat()
                },
                "adult_block": {
                    "state": "off",
                    "last_updated": datetime.now().isoformat()
                }
            },
            "domains": {},  # Will be populated from database
            "clients": {}   # Will track connected clients
        }
        self._load_initial_state()

    def _load_initial_state(self) -> None:
        """Load initial state from database."""
        # Load blocked domains
        domains = self._db_manager.get_blocked_domains()
        for domain in domains:
            self._states["domains"][domain] = {
                "blocked": True,
                "timestamp": datetime.now().isoformat(),
                "reason": "manual"
            }

    def update_feature_state(self, feature: str, state: str) -> Dict[str, Any]:
        """
        Update the state of a feature (ad_block or adult_block).
        
        Args:
            feature: Feature to update ('ad_block' or 'adult_block')
            state: New state ('on' or 'off')
            
        Returns:
            Dict containing the updated state information
        """
        with self._state_lock:
            if feature not in self._states["settings"]:
                raise ValueError(f"Invalid feature: {feature}")
                
            if state not in ["on", "off"]:
                raise ValueError(f"Invalid state: {state}")
                
            self._states["settings"][feature] = {
                "state": state,
                "last_updated": datetime.now().isoformat()
            }
            
            return self._states["settings"][feature]

    def get_feature_state(self, feature: str) -> Dict[str, Any]:
        """Get the current state of a feature."""
        with self._state_lock:
            if feature not in self._states["settings"]:
                raise ValueError(f"Invalid feature: {feature}")
            
            return self._states["settings"][feature]

    def add_domain(self, domain: str, reason: str = "manual") -> Dict[str, Any]:
        """
        Add a domain to blocked list.
        
        Args:
            domain: Domain to block
            reason: Reason for blocking ('manual', 'easylist', 'adult')
            
        Returns:
            Dict containing the domain state information
        """
        with self._state_lock:
            domain_state = {
                "blocked": True,
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            }
            self._states["domains"][domain] = domain_state
            self._db_manager.add_blocked_domain(domain)
            
            return domain_state

    def remove_domain(self, domain: str) -> bool:
        """
        Remove a domain from blocked list.
        
        Returns:
            bool indicating if domain was removed
        """
        with self._state_lock:
            if domain in self._states["domains"]:
                del self._states["domains"][domain]
                self._db_manager.remove_blocked_domain(domain)
                return True
            return False

    def get_domain_state(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a domain."""
        with self._state_lock:
            return self._states["domains"].get(domain)

    def get_all_domains(self) -> Dict[str, Dict[str, Any]]:
        """Get all domain states."""
        with self._state_lock:
            return self._states["domains"].copy()

    def register_client(self, client_id: str) -> None:
        """Register a new client connection."""
        with self._state_lock:
            self._states["clients"][client_id] = {
                "last_sync": datetime.now().isoformat(),
                "connected": True
            }

    def unregister_client(self, client_id: str) -> None:
        """Unregister a client connection."""
        with self._state_lock:
            if client_id in self._states["clients"]:
                self._states["clients"][client_id]["connected"] = False

    def get_full_state(self) -> Dict[str, Any]:
        """Get the complete current state."""
        with self._state_lock:
            return self._states.copy()