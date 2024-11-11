import os
from pathlib import Path
from typing import Dict

# Base directories
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Network Configuration
HOST: str = '127.0.0.1'
CLIENT_PORT: int = 65432
KERNEL_PORT: int = 65433
DB_FILE: str = 'my_internet.db'

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y%m%d_%H%M%S"

# Client Command Codes
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