import pytest
from unittest import mock
import json
from typing import Callable

from src.View import Viewer
from src.utils import (
    Codes, STR_CODE, STR_CONTENT,
    STR_SETTINGS, STR_AD_BLOCK, STR_ADULT_BLOCK,
    STR_BLOCKED_DOMAINS, DEFAULT_CONFIG,
    ERR_DUPLICATE_DOMAIN
)

@pytest.fixture
def mock_config_manager() -> mock.Mock:
    """Fixture to provide a mock configuration manager."""
    config_manager = mock.Mock()
    config_manager.get_config.return_value = DEFAULT_CONFIG.copy()
    return config_manager

@pytest.fixture
def mock_callback() -> Callable[[str], None]:
    """Fixture to provide a mock callback function."""
    return mock.Mock()

@pytest.fixture
def viewer(mock_config_manager: mock.Mock, mock_callback: mock.Mock) -> Viewer:
    """Fixture to create a Viewer instance with mocked components."""
    with mock.patch('tkinter.Tk') as mock_tk, \
         mock.patch('tkinter.ttk.Style'):
        # Create a mock Tk instance
        root = mock_tk.return_value
        
        # Set up the mock root properly
        mock_tk._default_root = root
        root._default_root = root
        
        # Create StringVar mock that returns string values
        with mock.patch('tkinter.StringVar') as mock_string_var:
            string_var_instance = mock.Mock()
            string_var_instance.get.return_value = "off"
            mock_string_var.return_value = string_var_instance
            
            # Create Entry and Listbox mocks
            with mock.patch('tkinter.Entry') as mock_entry, \
                 mock.patch('tkinter.Listbox') as mock_listbox:
                
                # Setup Entry mock
                entry_instance = mock.Mock()
                entry_instance.get.return_value = ""
                mock_entry.return_value = entry_instance
                
                # Setup Listbox mock
                listbox_instance = mock.Mock()
                listbox_instance.curselection.return_value = ()
                listbox_instance.get.return_value = ""
                mock_listbox.return_value = listbox_instance
                
                viewer = Viewer(
                    config_manager=mock_config_manager,
                    message_callback=mock_callback
                )
                
                # Store mock instances for easy access in tests
                viewer.domain_entry = entry_instance
                viewer.domains_listbox = listbox_instance
                
                # Mock the _show_error method
                viewer._show_error = mock.Mock()
                
                return viewer

def test_get_block_settings(viewer: Viewer) -> None:
    """Test getting block settings."""
    # Configure the mock StringVar to return specific values
    viewer.ad_var.get.return_value = "off"
    viewer.adult_var.get.return_value = "off"
    
    settings = viewer.get_block_settings()
    assert STR_AD_BLOCK in settings
    assert STR_ADULT_BLOCK in settings
    assert isinstance(settings[STR_AD_BLOCK], str)
    assert isinstance(settings[STR_ADULT_BLOCK], str)

def test_handle_ad_block(viewer: Viewer) -> None:
    """Test handling ad block setting changes."""
    # Configure the mock StringVar to return "on"
    viewer.ad_var.get.return_value = "on"
    viewer._handle_ad_block()
    
    expected_json = json.dumps({
        STR_CODE: Codes.CODE_AD_BLOCK,
        STR_CONTENT: "on"
    })
    
    viewer._message_callback.assert_called_once_with(expected_json)
    viewer.config_manager.save_config.assert_called_once_with(viewer.config)
    assert viewer.config[STR_SETTINGS][STR_AD_BLOCK] == "on"

def test_handle_adult_block(viewer: Viewer) -> None:
    """Test handling adult block setting changes."""
    # Configure the mock StringVar to return "on"
    viewer.adult_var.get.return_value = "on"
    viewer._handle_adult_block()
    
    expected_json = json.dumps({
        STR_CODE: Codes.CODE_ADULT_BLOCK,
        STR_CONTENT: "on"
    })
    
    viewer._message_callback.assert_called_once_with(expected_json)
    viewer.config_manager.save_config.assert_called_once_with(viewer.config)
    assert viewer.config[STR_SETTINGS][STR_ADULT_BLOCK] == "on"

def test_add_domain(viewer: Viewer) -> None:
    """Test adding a domain."""
    domain = "test.com"
    viewer.domain_entry.get.return_value = domain
    viewer._add_domain()
    
    expected_json = json.dumps({
        STR_CODE: Codes.CODE_ADD_DOMAIN,
        STR_CONTENT: domain
    })
    
    viewer._message_callback.assert_called_once_with(expected_json)
    viewer.config_manager.save_config.assert_called_once_with(viewer.config)
    assert viewer.config[STR_BLOCKED_DOMAINS][domain] is True

def test_add_duplicate_domain(viewer: Viewer) -> None:
    """Test adding a duplicate domain."""
    domain = "test.com"
    viewer.config[STR_BLOCKED_DOMAINS][domain] = True
    viewer.domain_entry.get.return_value = domain
    
    viewer._add_domain()
    
    viewer._message_callback.assert_not_called()
    viewer._show_error.assert_called_once_with(ERR_DUPLICATE_DOMAIN)
    assert len(viewer.config[STR_BLOCKED_DOMAINS]) == 1

def test_remove_domain(viewer: Viewer) -> None:
    """Test removing a domain."""
    domain = "test.com"
    viewer.config[STR_BLOCKED_DOMAINS][domain] = True
    viewer.domains_listbox.curselection.return_value = (0,)
    viewer.domains_listbox.get.return_value = domain
    
    viewer._remove_domain()
    
    expected_json = json.dumps({
        STR_CODE: Codes.CODE_REMOVE_DOMAIN,
        STR_CONTENT: domain
    })
    
    viewer._message_callback.assert_called_once_with(expected_json)
    viewer.config_manager.save_config.assert_called_once_with(viewer.config)
    assert domain not in viewer.config[STR_BLOCKED_DOMAINS]
