"""Unit tests for the Viewer class."""

import pytest
from unittest import mock
import json
from typing import Dict, Any

from src.View import Viewer
from src.utils import (
    Codes, STR_CODE, STR_CONTENT, STR_DOMAINS, STR_SETTINGS,
    STR_AD_BLOCK, STR_ADULT_BLOCK
)

@pytest.fixture
def mock_config_manager() -> mock.Mock:
    """Create a mock configuration manager fixture."""
    config_manager = mock.Mock()
    config_manager.get_config.return_value = {
        "network": {
            "host": "127.0.0.1",
            "port": 65432
        }
    }
    return config_manager

@pytest.fixture
def mock_callback() -> mock.Mock:
    """Create a mock callback function fixture."""
    return mock.Mock()

@pytest.fixture
def mock_tk() -> mock.Mock:
    """Create a mock for tkinter components."""
    with mock.patch('src.View.tk') as mock_tk:
        # Mock Tk instance
        mock_root = mock.Mock()
        mock_tk.Tk.return_value = mock_root
        
        # Mock StringVar
        mock_string_var = mock.Mock()
        mock_string_var.get.return_value = "on"
        mock_tk.StringVar.return_value = mock_string_var
        
        # Mock Listbox
        mock_listbox = mock.Mock()
        mock_listbox.get.side_effect = lambda start, end: ["domain1.com", "domain2.com"]
        mock_tk.Listbox.return_value = mock_listbox
        
        yield mock_tk

@pytest.fixture
def viewer(
    mock_config_manager: mock.Mock,
    mock_callback: mock.Mock,
    mock_tk: mock.Mock
) -> Viewer:
    """Create a Viewer instance with mocked dependencies."""
    with mock.patch('src.View.ttk'), \
         mock.patch('src.View.messagebox'), \
         mock.patch('src.View.setup_logger') as mock_logger:
        logger_instance = mock.Mock()
        mock_logger.return_value = logger_instance
        
        viewer = Viewer(
            config_manager=mock_config_manager,
            message_callback=mock_callback
        )
        
        # Set up instance variables that would normally be created in _setup_ui
        viewer.domains_listbox = mock_tk.Listbox.return_value
        viewer.ad_var = mock_tk.StringVar.return_value
        viewer.adult_var = mock_tk.StringVar.return_value
        viewer.domain_entry = mock.Mock()
        
        return viewer

def test_handle_ad_block_request(viewer: Viewer) -> None:
    """Test handling ad block request message formation."""
    expected_message = json.dumps({
        STR_CODE: Codes.CODE_AD_BLOCK,
        STR_CONTENT: "on"
    })
    
    viewer._handle_ad_block_request()
    viewer._message_callback.assert_called_once_with(expected_message)

def test_handle_adult_block_request(viewer: Viewer) -> None:
    """Test handling adult block request message formation."""
    expected_message = json.dumps({
        STR_CODE: Codes.CODE_ADULT_BLOCK,
        STR_CONTENT: "on"
    })
    
    viewer._handle_adult_block_request()
    viewer._message_callback.assert_called_once_with(expected_message)

def test_update_initial_settings(viewer: Viewer) -> None:
    """Test updating initial settings from server response."""
    test_settings = {
        STR_DOMAINS: ["example.com", "test.com"],
        STR_SETTINGS: {
            STR_AD_BLOCK: "on",
            STR_ADULT_BLOCK: "off"
        }
    }
    
    viewer.update_initial_settings(test_settings)
    viewer.logger.info.assert_called_with("Successfully initialized settings from server")

def test_update_domain_list_response(viewer: Viewer) -> None:
    """Test updating domain list from server response."""
    test_domains = ["domain1.com", "domain2.com"]
    
    viewer.update_domain_list_response(test_domains)
    viewer.logger.info.assert_called_with(f"Updated domain list with {len(test_domains)} domains")

@pytest.mark.parametrize("response,expected_log", [
    (
        {STR_CODE: Codes.CODE_SUCCESS,
         STR_CONTENT: "test.com"},
        "info"
    ),
    (
        {STR_CODE: Codes.CODE_ERROR,
         STR_CONTENT: "Failed to add domain"},
        "error"
    )
])
def test_add_domain_response(
    viewer: Viewer,
    response: Dict[str, Any],
    expected_log: str
) -> None:
    """Test handling add domain response from server."""
    # Reset the mock call counts before our test
    viewer.logger.info.reset_mock()
    viewer.logger.error.reset_mock()
    
    viewer.add_domain_response(response)
    
    if expected_log == "info":
        viewer.logger.info.assert_called_once()
        viewer.logger.error.assert_not_called()
    else:
        viewer.logger.error.assert_called_once()

def test_get_blocked_domains(viewer: Viewer) -> None:
    """Test getting list of blocked domains."""
    expected_domains = ["domain1.com", "domain2.com"]
    domains = list(viewer.get_blocked_domains())
    assert domains == expected_domains

def test_get_block_settings(viewer: Viewer) -> None:
    """Test getting block settings."""
    settings = viewer.get_block_settings()
    assert settings == {
        STR_AD_BLOCK: "on",
        STR_ADULT_BLOCK: "on"
    }
