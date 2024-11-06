from typing import Dict

# Client Command Codes (exact match with client's codes)
class Codes:
    CODE_AD_BLOCK = "50"
    CODE_ADULT_BLOCK = "51"
    CODE_ADD_DOMAIN = "52"
    CODE_REMOVE_DOMAIN = "53"
    CODE_DOMAIN_LIST_UPDATE = "54"

# Response messages
RESPONSE_MESSAGES = {
    'success': "Request processed successfully.",
    'invalid_request': "Invalid request format.",
    'domain_blocked': "Domain has been successfully blocked.",
    'domain_not_found': "Domain not found in block list.",
    'domain_exists': "Domain already exists in block list."
}