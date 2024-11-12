"""Utility module containing constants and common functions for the application."""

import os
from pathlib import Path

# Network related constants
DEFAULT_ADDRESS: str = "127.0.0.1"
CLIENT_PORT: int = 65432
KERNEL_PORT: int = 65433
BUFFER_SIZE: int = 1024

# Base directories
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_FILE: str = 'my_internet.db'

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
STR_CODE = "code"
STR_CONTENT = "content"
STR_OPERATION = "operation"
STR_SETTINGS = "settings"
# STR_TYPE = "type"
# STR_ACTION = "action"
# STR_MESSAGE_ID = "message_id"
# STR_ACK = "ack"

# Domain Related
STR_DOMAIN = "domain"
STR_DOMAINS = "domains"
STR_BLOCK = "block"
STR_UNBLOCK = "unblock"
# STR_IS_AD = "is_ad"
# STR_CATEGORIES = "categories"
# STR_REASON = "reason"

# Features and Settings
STR_AD_BLOCK = "ad_block"
STR_ADULT_BLOCK = "adult_block"
STR_TOGGLE_ON = "on"
STR_TOGGLE_OFF = "off"

# Status and Response Keys
STR_ERROR = "Error"
STR_SUCCESS = "success"
# STR_INVALID_REQUEST = "invalid_request"
# STR_DOMAIN_BLOCKED = "domain_blocked"
# STR_DOMAIN_NOT_FOUND = "domain_not_found"
# STR_INVALID_JSON = "invalid_json"

# Block Reasons
# STR_CUSTOM_BLOCKLIST = "custom_blocklist"
# STR_ADS = "ads"
# STR_ADULT_CONTENT = "adult_content"
# STR_ALLOWED = "allowed"
# STR_DOMAIN_LIST = "domain_list"

# Response Messages
STR_DOMAIN_BLOCKED_MSG = "Domain has been successfully blocked."
STR_DOMAIN_UNBLOCKED_MSG = "Domain has been successfully unblocked."
STR_DOMAIN_NOT_FOUND_MSG = "Domain not found in block list."
STR_INVALID_JSON_MSG = "Invalid JSON format."
# STR_REQUEST_PROCESSED = "Request processed successfully."
# STR_INVALID_REQUEST_FORMAT = "Invalid request format."
# STR_DOMAIN_EXISTS_MSG = "Domain already exists in block list."
# STR_ACK_TIMEOUT_MSG = "Acknowledgment timeout occurred."

# Config Constants
# STR_BLOCKED_DOMAINS = "blocked_domains"
# STR_NETWORK = "network"
# STR_SETTINGS = "settings"
# STR_LOGGING = "logging"

# Timeouts
# ACK_TIMEOUT = 5.0  # seconds

def invalid_json_response():
    return {
        STR_CODE: Codes.CODE_ERROR,
        STR_CONTENT: STR_INVALID_JSON_MSG
    }
