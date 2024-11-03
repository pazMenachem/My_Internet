import tkinter as tk
from unittest import mock

import pytest

from src.View import Viewer

@pytest.fixture
def viewer() -> Viewer:
    """Fixture to create a Viewer instance."""
    with mock.patch('src.View.tk.Tk'):
        yield Viewer()


def test_init(viewer: Viewer) -> None:
    """Test the initialization of Viewer."""
    viewer.root.title.assert_called_once_with("My Application")
    viewer.root.geometry.assert_called_once_with("800x600")


def test_run(viewer: Viewer) -> None:
    """Test running the viewer's main loop."""
    viewer.run()
    viewer.root.mainloop.assert_called_once()
