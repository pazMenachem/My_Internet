from typing import Dict, Any
from .db_manager import DatabaseManager
from .utils import (
    Codes,
    STR_AD_BLOCK, STR_ADULT_BLOCK,
    STR_CODE, STR_CONTENT, STR_DOMAINS, STR_DOMAIN,
    STR_DOMAIN_BLOCKED_MSG, STR_DOMAIN_NOT_FOUND_MSG,
    STR_BLOCK, STR_UNBLOCK, STR_DOMAIN_UNBLOCKED_MSG, 
    invalid_json_response
)
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
            if STR_CONTENT in request_data:
                state = request_data[STR_CONTENT]
                self.db_manager.update_setting(STR_AD_BLOCK, state)
                self.logger.info(f"Ad blocking turned {state}")
                return {
                    STR_CODE: Codes.CODE_SUCCESS,
                    STR_CONTENT: f"Ad blocking turned {state}"
                }
                
            return invalid_json_response()
            
        except Exception as e:
            self.logger.error(f"Error in ad block handler: {e}")
            return {
                STR_CODE: Codes.CODE_ERROR,
                STR_CONTENT: str(e)
            }

class AdultContentBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adult content block requests."""
        try:
            if STR_CONTENT in request_data:
                state = request_data[STR_CONTENT]
                self.db_manager.update_setting(STR_ADULT_BLOCK, state)
                self.logger.info(f"Adult content blocking turned {state}")
                return {
                    STR_CODE: Codes.CODE_SUCCESS,
                    STR_CONTENT: f"Adult content blocking turned {state}"
                }
                
            return invalid_json_response()

        except Exception as e:
            self.logger.error(f"Error in adult content block handler: {e}")
            return {
                STR_CODE: Codes.CODE_ERROR,
                STR_CONTENT: str(e)
            }

class DomainBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain blocking requests."""
        try:
            if STR_CONTENT not in request_data:
                self.logger.warning("Invalid request format: missing content")
                return invalid_json_response()

            match request_data[STR_CODE]:
                case Codes.CODE_ADD_DOMAIN:
                    self.db_manager.add_blocked_domain(request_data[STR_CONTENT])
                    self.logger.info(f"Domain blocked: {request_data[STR_CONTENT]}")
                    
                    return {
                        STR_CODE: Codes.CODE_SUCCESS,
                        STR_CONTENT: STR_DOMAIN_BLOCKED_MSG,
                    }

                case Codes.CODE_REMOVE_DOMAIN:
                    if self.db_manager.remove_blocked_domain(request_data[STR_CONTENT]):
                        self.logger.info(f"Domain unblocked: {request_data[STR_CONTENT]}")

                        return {
                            STR_CODE: Codes.CODE_SUCCESS,
                            STR_CONTENT: STR_DOMAIN_UNBLOCKED_MSG
                        }

                    self.logger.warning(f"Domain not found for unblocking: {request_data[STR_CONTENT]}")
                    return {
                        STR_CODE: Codes.CODE_ERROR,
                        STR_CONTENT: STR_DOMAIN_NOT_FOUND_MSG
                    }
                    
            self.logger.warning(f"Invalid action requested: {request_data[STR_CODE]}")
            return invalid_json_response()
            
        except Exception as e:
            self.logger.error(f"Error in domain block handler: {e}")
            return {
                STR_CODE: Codes.CODE_ADD_DOMAIN,
                STR_CONTENT: str(e)
            }

class DomainListHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain list requests."""
        try:
            domains = self.db_manager.get_blocked_domains()
            self.logger.info(f"Domain list requested, returned {len(domains)} domains")
            return {
                STR_CODE: Codes.CODE_SUCCESS,
                STR_DOMAINS: domains
            }

        except Exception as e:
            self.logger.error(f"Error in domain list handler: {e}")
            return {
                STR_CODE: Codes.CODE_ERROR,
                STR_CONTENT: str(e)
            }

class RequestFactory:
    """Factory class for creating appropriate request handlers."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.handlers = {
            Codes.CODE_AD_BLOCK           : AdBlockHandler(db_manager),
            Codes.CODE_ADULT_BLOCK        : AdultContentBlockHandler(db_manager),
            Codes.CODE_ADD_DOMAIN         : DomainBlockHandler(db_manager),
            Codes.CODE_REMOVE_DOMAIN      : DomainBlockHandler(db_manager),
            Codes.CODE_DOMAIN_LIST_UPDATE : DomainListHandler(db_manager)
        }

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate handler."""
        try:
            code = request_data.get(STR_CODE)
            handler = self.handlers.get(code)
            
            if handler:
                self.logger.debug(f"Handling request with code: {code}")
                return handler.handle_request(request_data)

            self.logger.warning(f"Invalid request code: {code}")
            return invalid_json_response()

        except Exception as e:
            self.logger.error(f"Error in request factory: {e}")
            return {
                STR_CODE: Codes.CODE_ERROR,
                STR_CONTENT: str(e)
            }
