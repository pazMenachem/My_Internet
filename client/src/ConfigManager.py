"""Configuration management module for the application."""

import json
import os
from typing import Dict, Any
from .Logger import setup_logger
from .utils import DEFAULT_CONFIG


class ConfigManager:
    """Manages application configuration loading and saving."""
    
    def __init__(self, config_file: str = "config.json") -> None:
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file.
        """
        self.logger = setup_logger(__name__)
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict containing configuration settings.
        """
        try:
            if os.path.exists(self.config_file):
                self.logger.info(f"Loading configuration from {self.config_file}")
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    return self._merge_configs(DEFAULT_CONFIG, user_config)

            self.logger.warning(f"Configuration file not found, using default configuration")
            
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding {self.config_file}, using default configuration")
        
        return DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge user configuration with default configuration.
        
        Args:
            default: Default configuration dictionary
            user: User configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config
