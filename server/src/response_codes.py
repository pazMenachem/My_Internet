from typing import Dict, Any

# Client Command Codes (incoming requests)
class ClientCodes:
    AD_BLOCK = "50"            # Toggle ad blocking
    ADULT_BLOCK = "51"         # Toggle adult content blocking
    ADD_DOMAIN = "52"          # Add domain to block list
    REMOVE_DOMAIN = "53"       # Remove domain from block list
    DOMAIN_LIST_UPDATE = "54"  # Update domain list

# Server Response Codes
class ServerCodes:
    SUCCESS = 200
    INVALID_REQUEST = 400
    DOMAIN_BLOCKED = 201
    DOMAIN_NOT_FOUND = 404
    AD_BLOCK_ENABLED = 202
    ADULT_CONTENT_BLOCKED = 203

# Response Messages
RESPONSE_MESSAGES: Dict[int, str] = {
    ServerCodes.SUCCESS: "Request processed successfully.",
    ServerCodes.INVALID_REQUEST: "Invalid request. Please check the request format.",
    ServerCodes.DOMAIN_BLOCKED: "Domain has been successfully blocked.",
    ServerCodes.DOMAIN_NOT_FOUND: "Domain not found in the block list.",
    ServerCodes.AD_BLOCK_ENABLED: "Ad blocking has been enabled for the domain.",
    ServerCodes.ADULT_CONTENT_BLOCKED: "Adult content has been blocked for the domain."
}

def create_response(
    server_code: int,
    client_code: str = None,
    content: Any = None,
    message: str = None
) -> Dict[str, Any]:
    """
    Create a standardized response format.
    
    Args:
        server_code: Internal server response code
        client_code: Client's command code (if responding to specific command)
        content: Optional response payload
        message: Custom message (uses default if None)
        
    Returns:
        Formatted response dictionary
    """
    response = {
        "code": client_code if client_code else str(server_code),
        "message": message if message else RESPONSE_MESSAGES.get(server_code, ""),
        "status": server_code < 400  # True for success codes, False for error codes
    }
    
    if content is not None:
        response["content"] = content
        
    return response

def create_error_response(message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return create_response(
        ServerCodes.INVALID_REQUEST,
        message=message
    )