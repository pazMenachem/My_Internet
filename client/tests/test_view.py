import tkinter as tk
from unittest import mock
import json
from typing import Callable

import pytest

from src.View import Viewer


@pytest.fixture
def mock_callback() -> Callable[[str], None]:
    """Fixture to provide a mock callback function."""
    return mock.Mock()


@pytest.fixture
def viewer(mock_callback: Callable[[str], None]) -> Viewer:
    """Fixture to create a Viewer instance."""
    with mock.patch('src.View.tk.Tk') as mock_tk:
        mock_tk.return_value.title = mock.Mock()
        mock_tk.return_value.geometry = mock.Mock()
        return Viewer(message_callback=mock_callback)


def test_init(viewer: Viewer, mock_callback: Callable[[str], None]) -> None:
    """Test the initialization of Viewer."""
    viewer.root.title.assert_called_once_with("Chat Application")
    viewer.root.geometry.assert_called_once_with("800x600")
    assert viewer._message_callback == mock_callback


def test_send_message(viewer: Viewer, mock_callback: Callable[[str], None]) -> None:
    """Test sending a message."""
    test_message = "Hello, World!"
    viewer.input_field = mock.Mock()
    viewer.input_field.get.return_value = test_message
    
    viewer._send_message()
    
    expected_json = json.dumps({"CODE": "100", "content": test_message})
    mock_callback.assert_called_once_with(expected_json)
    viewer.input_field.delete.assert_called_once_with(0, tk.END)


def test_display_message(viewer: Viewer) -> None:
    """Test displaying a message."""
    viewer.message_area = mock.Mock()
    
    viewer.display_message("User", "Test message")
    
    viewer.message_area.config.assert_any_call(state=tk.NORMAL)
    viewer.message_area.insert.assert_called_once_with(tk.END, "User: Test message\n")
    viewer.message_area.see.assert_called_once_with(tk.END)
    viewer.message_area.config.assert_any_call(state=tk.DISABLED)


def test_display_error(viewer: Viewer) -> None:
    """Test displaying an error message."""
    viewer.message_area = mock.Mock()
    
    viewer.display_error("Test error")
    
    viewer.message_area.config.assert_any_call(state=tk.NORMAL)
    viewer.message_area.insert.assert_called_once_with(tk.END, "Error: Test error\n")
    viewer.message_area.see.assert_called_once_with(tk.END)
    viewer.message_area.config.assert_any_call(state=tk.DISABLED)
