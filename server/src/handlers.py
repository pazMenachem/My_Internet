# handlers.py
import requests
import socket
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from My_Internet.server.src.db_manager import DatabaseManager
from response_codes import (
    SUCCESS, INVALID_REQUEST, DOMAIN_BLOCKED,
    DOMAIN_NOT_FOUND, AD_BLOCK_ENABLED,
    ADULT_CONTENT_BLOCKED, RESPONSE_MESSAGES
)


class RequestHandler(ABC):
    @abstractmethod
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

FAMILY_DNS_IP = "1.1.1.3"
EASYLIST_URL = "https://easylist.to/easylist/easylist.txt"


class AdBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.load_easylist()

    def load_easylist(self) -> None:
        try:
            response = requests.get(EASYLIST_URL)
            response.raise_for_status()
            easylist_data = response.text
            self.parse_and_store_easylist(easylist_data)
        except requests.exceptions.RequestException as e:
            print(f"Error loading EasyList: {e}")

    def parse_and_store_easylist(self, easylist_data: str) -> None:
        entries = []
        for line in easylist_data.split("\n"):
            line = line.strip()
            if line and not line.startswith("!"):
                entries.append((line,))
        self.db_manager.clear_easylist()
        self.db_manager.store_easylist_entries(entries)

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        domain = request_data.get('domain')
        if self.is_domain_blocked(domain):
            return {
                'code': AD_BLOCK_ENABLED,
                'message': RESPONSE_MESSAGES[AD_BLOCK_ENABLED]
            }
        else:
            return {
                'code': SUCCESS,
                'message': RESPONSE_MESSAGES[SUCCESS]
            }

    def is_domain_blocked(self, domain: str) -> bool:
        return self.db_manager.is_easylist_blocked(domain)


class DomainBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        domain = request_data.get('domain')
        action = request_data.get('action')

        if action == 'block':
            self.db_manager.add_blocked_domain(domain)
            return {
                'code': DOMAIN_BLOCKED,
                'message': RESPONSE_MESSAGES[DOMAIN_BLOCKED]
            }
        elif action == 'unblock':
            if self.db_manager.is_domain_blocked(domain):
                self.db_manager.remove_blocked_domain(domain)
                return {
                    'code': SUCCESS,
                    'message': RESPONSE_MESSAGES[SUCCESS]
                }
            else:
                return {
                    'code': DOMAIN_NOT_FOUND,
                    'message': RESPONSE_MESSAGES[DOMAIN_NOT_FOUND]
                }
        else:
            return {
                'code': INVALID_REQUEST,
                'message': RESPONSE_MESSAGES[INVALID_REQUEST]
            }


class AdultContentBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        domain = request_data.get('domain')
        if self.is_adult_content(domain):
            return {
                'code': ADULT_CONTENT_BLOCKED,
                'message': RESPONSE_MESSAGES[ADULT_CONTENT_BLOCKED]
            }
        else:
            return {
                'code': SUCCESS,
                'message': RESPONSE_MESSAGES[SUCCESS]
            }

    def is_adult_content(self, domain: str) -> bool:
        try:
            ip_address = socket.gethostbyname(domain)
            return ip_address == FAMILY_DNS_IP
        except socket.gaierror:
            return False


class RequestFactory:
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the RequestFactory with a database manager instance.
        
        Args:
            db_manager: DatabaseManager instance for handling database operations
        """
        self.db_manager = db_manager
        # Map request types to handler creator functions
        self._handlers = {
            'ad_block': lambda: AdBlockHandler(self.db_manager),
            'domain_block': lambda: DomainBlockHandler(self.db_manager),
            'adult_content_block': lambda: AdultContentBlockHandler()
        }
    
    def create_request_handler(self, request_type: str) -> Optional[RequestHandler]:
        """
        Creates and returns the appropriate request handler based on request type.
        
        Args:
            request_type: The type of request to handle
            
        Returns:
            RequestHandler instance or None if request type is not supported
        """
        handler_creator = self._handlers.get(request_type)
        return handler_creator() if handler_creator else None

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the request to appropriate handler and processes it.
        
        Args:
            request_data: The request data containing type and other parameters
            
        Returns:
            Dict containing response code and message
        """
        request_type = request_data.get('type')
        handler = self.create_request_handler(request_type)
        
        if handler:
            return handler.handle_request(request_data)
        else:
            return {
                'code': INVALID_REQUEST,
                'message': RESPONSE_MESSAGES[INVALID_REQUEST]
            }