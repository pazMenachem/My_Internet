"""Utility module containing constants and common functions for the application."""

# Network related constants
DEFAULT_HOST        = "host"
DEFAULT_PORT        = "port"
DEFAULT_BUFFER_SIZE = "receive_buffer_size"

# GUI constants
WINDOW_TITLE    = "Site Blocker"
WINDOW_SIZE     = "800x600"
PADDING_SMALL   = "5"
PADDING_MEDIUM  = "10"

# Message codes
class Codes:
    """Constants for message codes used in communication."""
    CODE_AD_BLOCK           = "50"
    CODE_ADULT_BLOCK        = "51"
    CODE_ADD_DOMAIN         = "52"
    CODE_REMOVE_DOMAIN      = "53"
    CODE_DOMAIN_LIST_UPDATE = "54"

# Default settings
DEFAULT_CONFIG = {
    "network": {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "receive_buffer_size": DEFAULT_BUFFER_SIZE
    },
    "blocked_domains": {},
    "settings": {
        "ad_block": "off",
        "adult_block": "off"
    },
    "logging": {
        "level": "INFO",
        "log_dir": "client_logs"
    }
}

# Logging constants
LOG_DIR          = "client_logs"
LOG_FORMAT       = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT  = "%Y%m%d_%H%M%S"

# Error messages
ERR_SOCKET_NOT_SETUP          = "Socket not set up. Call connect method first."
ERR_NO_CONNECTION             = "Attempted to send message without connection"
ERR_DUPLICATE_DOMAIN          = "Domain already exists in the list"
ERR_NO_DOMAIN_SELECTED        = "Please select a domain to remove"
ERR_DOMAIN_LIST_UPDATE_FAILED = "Failed to update domain list"

# String Constants
STR_AD_BLOCK          = "ad_block"
STR_ADULT_BLOCK       = "adult_block"
STR_CODE              = "code"
STR_CONTENT           = "content"
STR_ERROR             = "Error"

# Config Constants
STR_BLOCKED_DOMAINS  = "blocked_domains"
STR_NETWORK          = "network"
STR_SETTINGS         = "settings"
STR_LOGGING          = "logging"
