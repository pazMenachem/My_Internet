from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
from .db_manager import DatabaseManager
from .state_manager import StateManager
from .response_codes import (
    create_response,
    create_error_response,
    ServerCodes,
    ClientCodes
)

class RequestHandler(ABC):
    @abstractmethod
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class AdBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager, state_manager: StateManager):
        self.db_manager = db_manager
        self.state_manager = state_manager
        self.load_easylist()

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if 'action' in request_data:
                # Handle toggle request
                state = request_data['action']  # 'on' or 'off'
                self.state_manager.update_feature_state('ad_block', state)
                return create_response(
                    ServerCodes.SUCCESS,
                    ClientCodes.AD_BLOCK,
                    content={"state": state}
                )
            elif 'domain' in request_data:
                # Handle domain check
                domain = request_data['domain']
                if self.is_domain_blocked(domain):
                    return create_response(
                        ServerCodes.AD_BLOCK_ENABLED,
                        ClientCodes.AD_BLOCK,
                        content={"domain": domain}
                    )
            
            return create_response(ServerCodes.SUCCESS)
            
        except Exception as e:
            return create_error_response(str(e))

    def is_domain_blocked(self, domain: str) -> bool:
        feature_state = self.state_manager.get_feature_state('ad_block')
        if feature_state['state'] == 'off':
            return False
        return self.db_manager.is_easylist_blocked(domain)

class AdultContentBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager, state_manager: StateManager):
        self.db_manager = db_manager
        self.state_manager = state_manager

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = request_data.get('action')
            if not action:
                return create_error_response("Missing action parameter")

            if action in ['enable', 'disable']:
                # Convert enable/disable to on/off
                state = 'on' if action == 'enable' else 'off'
                self.state_manager.update_feature_state('adult_block', state)
                return create_response(
                    ServerCodes.SUCCESS,
                    ClientCodes.ADULT_BLOCK,
                    content={"state": state}
                )
                
            elif action == 'check':
                domain = request_data.get('domain')
                if not domain:
                    return create_error_response("Missing domain parameter")
                    
                feature_state = self.state_manager.get_feature_state('adult_block')
                if feature_state['state'] == 'on':
                    return create_response(
                        ServerCodes.ADULT_CONTENT_BLOCKED,
                        ClientCodes.ADULT_BLOCK,
                        content={"domain": domain}
                    )
                    
            return create_response(ServerCodes.SUCCESS)
            
        except Exception as e:
            return create_error_response(str(e))

class DomainBlockHandler(RequestHandler):
    def __init__(self, db_manager: DatabaseManager, state_manager: StateManager):
        self.db_manager = db_manager
        self.state_manager = state_manager

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = request_data.get('action')
            domain = request_data.get('domain')

            if not action or not domain:
                return create_error_response("Missing action or domain parameter")

            if action == 'block':
                self.state_manager.add_domain(domain, reason='manual')
                return create_response(
                    ServerCodes.DOMAIN_BLOCKED,
                    ClientCodes.ADD_DOMAIN,
                    content={"domain": domain}
                )
                
            elif action == 'unblock':
                if self.state_manager.remove_domain(domain):
                    return create_response(
                        ServerCodes.SUCCESS,
                        ClientCodes.REMOVE_DOMAIN,
                        content={"domain": domain}
                    )
                else:
                    return create_response(
                        ServerCodes.DOMAIN_NOT_FOUND,
                        ClientCodes.REMOVE_DOMAIN,
                        content={"domain": domain}
                    )
                    
            return create_error_response("Invalid action")
            
        except Exception as e:
            return create_error_response(str(e))

class RequestFactory:
    def __init__(self, db_manager: DatabaseManager, state_manager: StateManager):
        self.db_manager = db_manager
        self.state_manager = state_manager
        self._handlers = {
            ClientCodes.AD_BLOCK: lambda: AdBlockHandler(self.db_manager, self.state_manager),
            ClientCodes.ADULT_BLOCK: lambda: AdultContentBlockHandler(self.db_manager, self.state_manager),
            ClientCodes.ADD_DOMAIN: lambda: DomainBlockHandler(self.db_manager, self.state_manager),
            ClientCodes.REMOVE_DOMAIN: lambda: DomainBlockHandler(self.db_manager, self.state_manager)
        }

    def create_request_handler(self, request_type: str) -> Optional[RequestHandler]:
        handler_creator = self._handlers.get(request_type)
        return handler_creator() if handler_creator else None

    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            request_type = request_data.get('code')
            handler = self.create_request_handler(request_type)
            
            if handler:
                response = handler.handle_request(request_data)
                # After handling request, check if we need to broadcast updates
                if request_type in [ClientCodes.ADD_DOMAIN, ClientCodes.REMOVE_DOMAIN]:
                    self._broadcast_domain_update()
                return response
                
            return create_error_response("Invalid request type")
            
        except Exception as e:
            return create_error_response(str(e))

    def _broadcast_domain_update(self) -> None:
        """Prepare domain list update for broadcasting."""
        domains = list(self.state_manager.get_all_domains().keys())
        # The server will use this to broadcast to all clients
        return create_response(
            ServerCodes.SUCCESS,
            ClientCodes.DOMAIN_LIST_UPDATE,
            content=domains
        )