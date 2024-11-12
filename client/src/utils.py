"""Utility module containing constants and common functions for the application."""

# Network related constants
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: str = "65432"
DEFAULT_BUFFER_SIZE: str = "1024"

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
    CODE_SUCCESS            = "100"
    CODE_ERROR              = "101"

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
STR_DOMAINS           = "domains"
STR_SUCCESS           = "Success"

# Config Constants
STR_BLOCKED_DOMAINS     = "blocked_domains"
STR_NETWORK             = "network"
STR_SETTINGS            = "settings"
STR_LOGGING             = "logging"
STR_HOST                = "host"
STR_PORT                = "port"
STR_RECEIVE_BUFFER_SIZE = "receive_buffer_size"
STR_LEVEL               = "level"
STR_LOG_DIR             = "log_dir"

# Default settings
DEFAULT_CONFIG = {
    STR_NETWORK: {
        STR_HOST: DEFAULT_HOST,
        STR_PORT: DEFAULT_PORT,
        STR_RECEIVE_BUFFER_SIZE: DEFAULT_BUFFER_SIZE
    },
    
    STR_BLOCKED_DOMAINS: {},
    
    STR_SETTINGS: {
        STR_AD_BLOCK: "off",
        STR_ADULT_BLOCK: "off"
    },
    
    STR_LOGGING: {
        STR_LEVEL: "INFO",
        STR_LOG_DIR: LOG_DIR
    }
}
