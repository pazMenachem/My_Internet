from typing import Dict, Any
from .db_manager import DatabaseManager
from .utils import (
    Codes,
    STR_AD_BLOCK, STR_ADULT_BLOCK, STR_CODE, STR_CONTENT,
    STR_DOMAINS, STR_OPERATION, STR_SETTINGS,
    invalid_json_response
)
from .logger import setup_logger
from .dns_manager import DNSManager

class RequestHandler:
    """Base class for request handlers."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager  = db_manager
        self.dns_manager = DNSManager()
        self.logger      = setup_logger(self.__class__.__name__)

class AdBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ad block requests."""
        try:
            if STR_CONTENT in request_data:
                state = request_data[STR_CONTENT]
                self.db_manager.update_setting(STR_AD_BLOCK, state)
                
                # Update DNS settings based on current state
                adult_state = self.db_manager.get_setting(STR_ADULT_BLOCK)
                self.dns_manager.update_dns_settings(state, adult_state)
                
                self.logger.info(f"Ad blocking turned {state}")
                return {
                    STR_CODE:      Codes.CODE_SUCCESS,
                    STR_CONTENT:   f"{state}",
                    STR_OPERATION: Codes.CODE_AD_BLOCK
                }
                
            return invalid_json_response()
            
        except Exception as e:
            self.logger.error(f"Error in ad block handler: {e}")
            return {
                STR_CODE:      Codes.CODE_ERROR,
                STR_CONTENT:   str(e),
                STR_OPERATION: Codes.CODE_AD_BLOCK
            }

class AdultContentBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle adult content block requests."""
        try:
            if STR_CONTENT in request_data:
                state = request_data[STR_CONTENT]
                self.db_manager.update_setting(STR_ADULT_BLOCK, state)
                
                # Update DNS settings based on current state
                ad_state = self.db_manager.get_setting(STR_AD_BLOCK)
                self.dns_manager.update_dns_settings(ad_state, state)
                
                self.logger.info(f"Adult content blocking turned {state}")
                return {
                    STR_CODE:      Codes.CODE_SUCCESS,
                    STR_CONTENT:   f"{state}",
                    STR_OPERATION: Codes.CODE_ADULT_BLOCK
                }
                
            return invalid_json_response()

        except Exception as e:
            self.logger.error(f"Error in adult content block handler: {e}")
            return {
                STR_CODE:      Codes.CODE_ERROR,
                STR_CONTENT:   str(e),
                STR_OPERATION: Codes.CODE_ADULT_BLOCK
            }

class DomainBlockHandler(RequestHandler):
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle domain blocking requests."""
        try:
            if STR_CONTENT not in request_data:
                self.logger.warning("Invalid request format: missing content")
                return invalid_json_response()

            operation_code = request_data[STR_CODE]
            domain = request_data[STR_CONTENT]
            
            if not domain.startswith("www."):
                domain = f"www.{domain}"

            match operation_code:
                case Codes.CODE_ADD_DOMAIN:
                    if self.db_manager.is_domain_blocked(domain):
                        self.logger.warning(f"Domain already blocked: {domain}")
                        return {
                            STR_CODE:      Codes.CODE_ERROR,
                            STR_CONTENT:   f"Domain {domain} is already blocked",
                            STR_OPERATION: Codes.CODE_ADD_DOMAIN
                        }
                    
                    self.db_manager.add_blocked_domain(domain)
                    self.logger.info(f"Domain blocked: {domain}")
                    return {
                        STR_CODE:      Codes.CODE_SUCCESS,
                        STR_CONTENT:   domain,
                        STR_OPERATION: Codes.CODE_ADD_DOMAIN
                    }

                case Codes.CODE_REMOVE_DOMAIN:
                    if self.db_manager.remove_blocked_domain(domain):
                        self.logger.info(f"Domain unblocked: {domain}")
                        return {
                            STR_CODE:      Codes.CODE_SUCCESS,
                            STR_CONTENT:   domain,
                            STR_OPERATION: Codes.CODE_REMOVE_DOMAIN
                        }

                    self.logger.warning(f"Domain not found for unblocking: {domain}")
                    return {
                        STR_CODE:      Codes.CODE_ERROR,
                        STR_CONTENT:   domain,
                        STR_OPERATION: Codes.CODE_REMOVE_DOMAIN
                    }
                    
            self.logger.warning(f"Invalid action requested: {request_data[STR_CODE]}")
            return invalid_json_response()

        except Exception as e:
            self.logger.error(f"Error in domain block handler: {e}")
            return {
                STR_CODE:      Codes.CODE_ERROR,
                STR_CONTENT:   str(e),
                STR_OPERATION: operation_code
            }

class SettingsHandler(RequestHandler):
    """Handle settings and domain list requests."""
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle settings requests."""
        try:
            # Get domains and settings
            domains = self.db_manager.get_blocked_domains()
            settings = {
                STR_AD_BLOCK:    self.db_manager.get_setting(STR_AD_BLOCK),
                STR_ADULT_BLOCK: self.db_manager.get_setting(STR_ADULT_BLOCK)
            }

            self.dns_manager.update_dns_settings(settings[STR_AD_BLOCK], settings[STR_ADULT_BLOCK])
            
            self.logger.info(f"Settings requested, returned {len(domains)} domains")
            return {
                STR_CODE:      Codes.CODE_SUCCESS,
                STR_DOMAINS:   domains,
                STR_SETTINGS:  settings,
                STR_OPERATION: Codes.CODE_INIT_SETTINGS
            }

        except Exception as e:
            self.logger.error(f"Error in settings handler: {e}")
            return {
                STR_CODE:      Codes.CODE_ERROR,
                STR_CONTENT:   str(e),
                STR_OPERATION: Codes.CODE_INIT_SETTINGS
            }

class RequestFactory:
    """Factory class for creating appropriate request handlers."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.handlers = {
            Codes.CODE_AD_BLOCK:      AdBlockHandler(db_manager),
            Codes.CODE_ADULT_BLOCK:   AdultContentBlockHandler(db_manager),
            Codes.CODE_ADD_DOMAIN:    DomainBlockHandler(db_manager),
            Codes.CODE_REMOVE_DOMAIN: DomainBlockHandler(db_manager),
            Codes.CODE_INIT_SETTINGS: SettingsHandler(db_manager)
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