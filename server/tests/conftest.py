import pytest
from unittest import mock
from typing import Generator
from My_Internet.server.src.server import Server
from My_Internet.server.src.db_manager import DatabaseManager

@pytest.fixture
def mock_db_manager() -> mock.Mock:
    """Create a mock database manager."""
    db_manager = mock.Mock(spec=DatabaseManager)
    db_manager.get_blocked_domains.return_value = []
    db_manager.get_setting.return_value = 'off'
    db_manager.is_domain_blocked.return_value = False
    return db_manager

@pytest.fixture
def server_instance(mock_db_manager: mock.Mock) -> Server:
    """Create a server instance for testing."""
    server = Server(mock_db_manager)
    server.logger = mock.Mock()  # Mock the logger to prevent actual logging
    return server

@pytest.fixture
def mock_socket() -> mock.Mock:
    """Create a mock socket for testing."""
    socket_mock = mock.Mock()
    socket_mock.bind = mock.Mock()
    socket_mock.listen = mock.Mock()
    socket_mock.accept = mock.Mock()
    socket_mock.close = mock.Mock()
    socket_mock.settimeout = mock.Mock()
    return socket_mock

@pytest.fixture
def mock_stream_reader() -> mock.AsyncMock:
    """Create a mock stream reader."""
    reader = mock.AsyncMock()
    reader.readline = mock.AsyncMock()
    return reader

@pytest.fixture
def mock_stream_writer() -> mock.Mock:
    """Create a mock stream writer."""
    writer = mock.Mock()
    writer.write = mock.Mock()
    writer.drain = mock.AsyncMock()
    writer.close = mock.Mock()
    writer.wait_closed = mock.AsyncMock()
    writer.get_extra_info = mock.Mock(return_value=('127.0.0.1', 12345))
    return writer

@pytest.fixture
def mock_asyncio_start_server() -> mock.AsyncMock:
    """Create a mock for asyncio.start_server."""
    return mock.AsyncMock()