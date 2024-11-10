from abc import ABC, abstractmethod
from typing import Dict, Any
from .db_manager import DatabaseManager
from .response_codes import Codes, RESPONSE_MESSAGES
from .easylist_manager import EasyListManager

class RequestHandler(ABC):
    @abstractmethod
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class AdBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager):
        """Initialize AdBlockHandler with database manager and EasyList manager."""
        self.db_manager = db_manager
        self.easylist_manager = EasyListManager(db_manager)
        # Start the automatic update scheduler
        self.easylist_manager.start_update_scheduler()
        # Perform initial load
        self.easylist_manager.force_update()

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ad block requests."""
        try:
            if 'action' in request_data:
                # Handle toggle request
                state = request_data['action']  # 'on' or 'off'
                self.db_manager.update_setting('ad_block', state)
                
                # If turning on, ensure EasyList is loaded
                if state == 'on':
                    self.easylist_manager.force_update()
                
                return {
                    'code': Codes.CODE_AD_BLOCK,
                    'message': RESPONSE_MESSAGES['success']
                }
            
            elif 'domain' in request_data:
                # Check if domain should be blocked
                if self.is_domain_blocked(request_data['domain']):
                    return {
                        'code': Codes.CODE_AD_BLOCK,
                        'message': "Domain contains ads"
                    }
                    
            return {
                'code': Codes.CODE_AD_BLOCK,
                'message': RESPONSE_MESSAGES['success']
            }
            
        except Exception as e:
            return {
                'code': Codes.CODE_AD_BLOCK,
                'message': str(e)
            }

    def is_domain_blocked(self, domain: str) -> bool:
        """Check if domain should be blocked based on easylist."""
        if self.db_manager.get_setting('ad_block') == 'off':
            return False
        return self.db_manager.is_easylist_blocked(domain)

    def __del__(self) -> None:
        """Cleanup when handler is destroyed."""
        if hasattr(self, 'easylist_manager'):
            self.easylist_manager.stop_update_scheduler()

class AdultContentBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adult content block requests."""
        try:
            if 'action' in request_data:
                # Handle toggle request
                state = request_data['action']  # 'on' or 'off'
                self.db_manager.update_setting('adult_block', state)
                return {
                    'code': Codes.CODE_ADULT_BLOCK,
                    'message': RESPONSE_MESSAGES['success']
                }
            
            elif 'domain' in request_data:
                # Check if adult blocking is enabled
                if self.db_manager.get_setting('adult_block') == 'on':
                    return {
                        'code': Codes.CODE_ADULT_BLOCK,
                        'message': "Adult content blocked"
                    }
            
            return {
                'code': Codes.CODE_ADULT_BLOCK,
                'message': RESPONSE_MESSAGES['success']
            }
            
        except Exception as e:
            return {
                'code': Codes.CODE_ADULT_BLOCK,
                'message': str(e)
            }

class DomainBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain block/unblock requests."""
        try:
            action = request_data.get('action')
            domain = request_data.get('domain')

            if not domain:
                return {
                    'code': request_data.get('code'),
                    'message': RESPONSE_MESSAGES['invalid_request']
                }

            if action == 'block':
                self.db_manager.add_blocked_domain(domain)
                return {
                    'code': Codes.CODE_ADD_DOMAIN,
                    'message': RESPONSE_MESSAGES['domain_blocked']
                }
                
            elif action == 'unblock':
                if self.db_manager.remove_blocked_domain(domain):
                    return {
                        'code': Codes.CODE_REMOVE_DOMAIN,
                        'message': RESPONSE_MESSAGES['success']
                    }
                else:
                    return {
                        'code': Codes.CODE_REMOVE_DOMAIN,
                        'message': RESPONSE_MESSAGES['domain_not_found']
                    }
            
            return {
                'code': request_data.get('code'),
                'message': RESPONSE_MESSAGES['invalid_request']
            }
            
        except Exception as e:
            return {
                'code': request_data.get('code'),
                'message': str(e)
            }

class DomainListHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain list requests."""
        try:
            domains = self.db_manager.get_blocked_domains()
            return {
                'code': Codes.CODE_DOMAIN_LIST_UPDATE,
                'domains': domains,
                'message': RESPONSE_MESSAGES['success']
            }
        except Exception as e:
            return {
                'code': Codes.CODE_DOMAIN_LIST_UPDATE,
                'message': str(e)
            }

class RequestFactory:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._handlers = {
            Codes.CODE_AD_BLOCK: lambda: AdBlockHandler(self.db_manager),
            Codes.CODE_ADULT_BLOCK: lambda: AdultContentBlockHandler(self.db_manager),
            Codes.CODE_ADD_DOMAIN: lambda: DomainBlockHandler(self.db_manager),
            Codes.CODE_REMOVE_DOMAIN: lambda: DomainBlockHandler(self.db_manager),
            Codes.CODE_DOMAIN_LIST_UPDATE: lambda: DomainListHandler(self.db_manager)
        }

    def create_request_handler(self, request_type: str) -> RequestHandler:
        """Create appropriate handler based on request type."""
        handler_creator = self._handlers.get(request_type)
        if handler_creator:
            return handler_creator()
        raise ValueError(f"Invalid request type: {request_type}")

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request using appropriate handler."""
        try:
            request_type = request_data.get('code')
            handler = self.create_request_handler(request_type)
            return handler.handle_request(request_data)
        except Exception as e:
            return {
                'code': request_data.get('code', ''),
                'message': str(e)
            }