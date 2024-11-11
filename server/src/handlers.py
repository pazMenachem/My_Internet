from typing import Dict, Any
from .db_manager import DatabaseManager
from .utils import Codes, RESPONSE_MESSAGES
from .logger import setup_logger

class RequestHandler:
    """Base class for request handlers."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)

class AdBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ad block requests."""
        try:
            if 'action' in request_data:
                # Handle toggle request
                state = request_data['action']  # 'on' or 'off'
                self.db_manager.update_setting('ad_block', state)
                self.logger.info(f"Ad blocking turned {state}")
                return {
                    'code': Codes.CODE_AD_BLOCK,
                    'message': f"Ad blocking turned {state}"
                }
                
            return {
                'code': Codes.CODE_AD_BLOCK,
                'message': RESPONSE_MESSAGES['success']
            }
            
        except Exception as e:
            self.logger.error(f"Error in ad block handler: {e}")
            return {
                'code': Codes.CODE_AD_BLOCK,
                'message': str(e)
            }

class AdultContentBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adult content block requests."""
        try:
            if 'action' in request_data:
                # Handle toggle request
                state = request_data['action']  # 'on' or 'off'
                self.db_manager.update_setting('adult_block', state)
                self.logger.info(f"Adult content blocking turned {state}")
                return {
                    'code': Codes.CODE_ADULT_BLOCK,
                    'message': f"Adult content blocking turned {state}"
                }
                
            return {
                'code': Codes.CODE_ADULT_BLOCK,
                'message': RESPONSE_MESSAGES['success']
            }
            
        except Exception as e:
            self.logger.error(f"Error in adult content block handler: {e}")
            return {
                'code': Codes.CODE_ADULT_BLOCK,
                'message': str(e)
            }

class DomainBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain blocking requests."""
        try:
            if 'action' not in request_data or 'domain' not in request_data:
                self.logger.warning("Invalid request format: missing action or domain")
                return {
                    'code': Codes.CODE_ADD_DOMAIN,
                    'message': RESPONSE_MESSAGES['invalid_request']
                }

            domain = request_data['domain']
            action = request_data['action']

            if action == 'block':
                self.db_manager.add_blocked_domain(domain)
                self.logger.info(f"Domain blocked: {domain}")
                return {
                    'code': Codes.CODE_ADD_DOMAIN,
                    'message': RESPONSE_MESSAGES['domain_blocked']
                }
            elif action == 'unblock':
                if self.db_manager.remove_blocked_domain(domain):
                    self.logger.info(f"Domain unblocked: {domain}")
                    return {
                        'code': Codes.CODE_REMOVE_DOMAIN,
                        'message': RESPONSE_MESSAGES['success']
                    }
                else:
                    self.logger.warning(f"Domain not found for unblocking: {domain}")
                    return {
                        'code': Codes.CODE_REMOVE_DOMAIN,
                        'message': RESPONSE_MESSAGES['domain_not_found']
                    }
            else:
                self.logger.warning(f"Invalid action requested: {action}")
                return {
                    'code': Codes.CODE_ADD_DOMAIN,
                    'message': RESPONSE_MESSAGES['invalid_request']
                }

        except Exception as e:
            self.logger.error(f"Error in domain block handler: {e}")
            return {
                'code': Codes.CODE_ADD_DOMAIN,
                'message': str(e)
            }

class DomainListHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain list requests."""
        try:
            domains = self.db_manager.get_blocked_domains()
            self.logger.info(f"Domain list requested, returned {len(domains)} domains")
            return {
                'code': Codes.CODE_DOMAIN_LIST_UPDATE,
                'domains': domains,
                'message': RESPONSE_MESSAGES['success']
            }
        except Exception as e:
            self.logger.error(f"Error in domain list handler: {e}")
            return {
                'code': Codes.CODE_DOMAIN_LIST_UPDATE,
                'message': str(e)
            }

class RequestFactory:
    """Factory class for creating appropriate request handlers."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.handlers = {
            Codes.CODE_AD_BLOCK: AdBlockHandler(db_manager),
            Codes.CODE_ADULT_BLOCK: AdultContentBlockHandler(db_manager),
            Codes.CODE_ADD_DOMAIN: DomainBlockHandler(db_manager),
            Codes.CODE_REMOVE_DOMAIN: DomainBlockHandler(db_manager),
            Codes.CODE_DOMAIN_LIST_UPDATE: DomainListHandler(db_manager)
        }

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate handler."""
        try:
            code = request_data.get('code')
            handler = self.handlers.get(code)
            
            if handler:
                self.logger.debug(f"Handling request with code: {code}")
                return handler.handle_request(request_data)
            else:
                self.logger.warning(f"Invalid request code: {code}")
                return {
                    'message': RESPONSE_MESSAGES['invalid_request']
                }
        except Exception as e:
            self.logger.error(f"Error in request factory: {e}")
            return {
                'message': str(e)
            }