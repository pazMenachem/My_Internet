# response_codes.py

from typing import Dict

# Response codes
SUCCESS: int = 200
INVALID_REQUEST: int = 400
DOMAIN_BLOCKED: int = 201
DOMAIN_NOT_FOUND: int = 404
AD_BLOCK_ENABLED: int = 202
ADULT_CONTENT_BLOCKED: int = 203

# Response messages
RESPONSE_MESSAGES: Dict[int, str] = {
    SUCCESS: "Request processed successfully.",
    INVALID_REQUEST: "Invalid request. Please check the request format.",
    DOMAIN_BLOCKED: "Domain has been successfully blocked.",
    DOMAIN_NOT_FOUND: "Domain not found in the block list.",
    AD_BLOCK_ENABLED: "Ad blocking has been enabled for the domain.",
    ADULT_CONTENT_BLOCKED: "Adult content has been blocked for the domain."
}