"""Utility module containing constants and common functions for the application."""

import os
from pathlib import Path

# Network related constants
DEFAULT_ADDRESS: str = "127.0.0.1"
CLIENT_PORT: int     = 65432
KERNEL_PORT: int     = 65433
BUFFER_SIZE: int     = 1024

# Base directories
BASE_DIR: Path = Path(__file__).parent.parent
LOG_DIR: str   = os.path.join(BASE_DIR, "logs")
DB_FILE: str   = 'my_internet.db'

# Message codes
class Codes:
    """Constants for message codes used in communication."""
    CODE_AD_BLOCK           = "50"
    CODE_ADULT_BLOCK        = "51"
    CODE_ADD_DOMAIN         = "52"
    CODE_REMOVE_DOMAIN      = "53"
    CODE_DOMAIN_LIST_UPDATE = "54"
    CODE_SUCCESS            = "100"
    CODE_ERROR              = "101"
    CODE_ACK                = "99"
    CODE_INIT_SETTINGS      = "55"
# Logging constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y%m%d_%H%M%S"

# Message Types and Codes
STR_CODE      = "code"
STR_CONTENT   = "content"
STR_OPERATION = "operation"
STR_SETTINGS  = "settings"

# Domain Related
STR_DOMAIN  = "domain"
STR_DOMAINS = "domains"
STR_BLOCK   = "block"
STR_UNBLOCK = "unblock"

# Features and Settings
STR_AD_BLOCK    = "ad_block"
STR_ADULT_BLOCK = "adult_block"
STR_TOGGLE_ON   = "on"
STR_TOGGLE_OFF  = "off"

# Status and Response Keys
STR_ERROR   = "Error"
STR_SUCCESS = "success"

# Response Messages
STR_DOMAIN_BLOCKED_MSG   = "Domain has been successfully blocked."
STR_DOMAIN_UNBLOCKED_MSG = "Domain has been successfully unblocked."
STR_DOMAIN_NOT_FOUND_MSG = "Domain not found in block list."
STR_INVALID_JSON_MSG     = "Invalid JSON format."

# DNS Script Names
STR_CLOUDFLARE_DNS_SCRIPT     = "cloudflare_dns.sh"
STR_ADGUARD_DNS_SCRIPT        = "adguard_dns.sh"
STR_ADGUARD_FAMILY_DNS_SCRIPT = "adguard_family_dns.sh"
STR_RESET_DNS_SCRIPT          = "reset_dns.sh"

def invalid_json_response():
    return {
        STR_CODE: Codes.CODE_ERROR,
        STR_CONTENT: STR_INVALID_JSON_MSG
    }
