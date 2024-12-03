import pytest
import json
import asyncio
from unittest import mock
from typing import Dict, Any
from My_Internet.server.src.server import Server
from My_Internet.server.src.utils import (
    DEFAULT_ADDRESS, CLIENT_PORT, KERNEL_PORT,
    Codes, STR_CODE, STR_CONTENT
)
import socket

@pytest.fixture
def mock_request_factory():
    """Create a mock request factory."""
    factory = mock.Mock()
    factory.handle_request.return_value = {
        STR_CODE: Codes.CODE_SUCCESS,
        STR_CONTENT: "Test response"
    }
    return factory

class TestServerInitialization:
    def test_server_init(self, mock_db_manager):
        """Test server initialization."""
        server = Server(mock_db_manager)
        assert server.db_manager == mock_db_manager
        assert server.running is True
        assert server.kernel_writer is None

class TestKernelCommunication:
    @pytest.mark.asyncio
    async def test_notify_kernel(self, server_instance):
        """Test kernel notification when kernel is connected."""
        mock_writer = mock.Mock()
        mock_writer.write = mock.Mock()
        mock_writer.drain = mock.AsyncMock()
        server_instance.kernel_writer = mock_writer
        notification = {"test": "data"}
        await server_instance.notify_kernel(notification)
        mock_writer.write.assert_called_once_with(
            json.dumps(notification).encode() + b'\n'
        )
        mock_writer.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_kernel_no_connection(self, server_instance):
        """Test kernel notification when kernel is not connected."""
        server_instance.kernel_writer = None
        notification = {"test": "data"}
        await server_instance.notify_kernel(notification)
        
    @pytest.mark.asyncio
    async def test_handle_kernel_requests(
        self,
        server_instance,
        mock_stream_reader,
        mock_stream_writer
    ):
        """Test kernel connection handling."""
        initial_settings = {
            STR_CODE: Codes.CODE_SUCCESS,
            STR_CONTENT: "Initial settings"
        }
        server_instance._get_initial_settings = mock.Mock(
            return_value=initial_settings
        )
        mock_stream_reader.read.side_effect = [b"test data", b""]
        await server_instance.handle_kernel_requests(
            mock_stream_reader,
            mock_stream_writer
        )
        assert mock_stream_writer.write.called
        assert mock_stream_writer.close.called
        assert server_instance.kernel_writer is None

class TestClientCommunication:
    """Test suite for client communication functionality."""
    @pytest.mark.timeout(5)
    def test_handle_client_thread(
        self,
        server_instance,
        monkeypatch
    ):
        """Test the client thread handling functionality.
        
        Args:
            server_instance: The server instance being tested
            monkeypatch: Pytest fixture for modifying objects
            
        Tests:
            - Socket binding and configuration
            - Client connection acceptance
            - Timeout handling
            - Proper cleanup of resources
            - Thread termination
        """
        mock_socket = mock.Mock()
        mock_socket.accept = mock.Mock()
        mock_socket.bind = mock.Mock()
        mock_socket.listen = mock.Mock()
        mock_socket.close = mock.Mock()
        mock_socket.settimeout = mock.Mock()
        mock_conn = mock.Mock()
        mock_conn.recv = mock.Mock()
        mock_conn.settimeout = mock.Mock()
        mock_conn.close = mock.Mock()
        mock_conn.send = mock.Mock()
        mock_socket.accept.side_effect = [
            (mock_conn, ("127.0.0.1", 65432)),
            socket.timeout()
        ]
        
        def mock_recv(size):
            server_instance.running = False
            return b""
        mock_conn.recv.side_effect = mock_recv
        
        def mock_socket_create(*args, **kwargs):
            return mock_socket
        monkeypatch.setattr(socket, 'socket', mock_socket_create)

        server_instance.handle_client_thread()
        mock_socket.bind.assert_called_with((DEFAULT_ADDRESS, CLIENT_PORT))
        mock_socket.listen.assert_called_with(1)
        mock_socket.settimeout.assert_called_with(1.0)
        mock_conn.settimeout.assert_called_with(1.0)
        mock_socket.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_process_client_request_valid(
        self,
        server_instance,
        mock_request_factory
    ):
        """Test processing valid client request."""
        server_instance.request_factory = mock_request_factory
        mock_conn = mock.Mock()        
        test_data = {
            STR_CODE: Codes.CODE_SUCCESS,
            STR_CONTENT: "test"
        }
        server_instance._process_client_request(
            mock_conn,
            json.dumps(test_data).encode()
        )
        mock_request_factory.handle_request.assert_called_with(test_data)
        assert mock_conn.send.called

    def test_process_client_request_invalid_json(
        self,
        server_instance,
        mock_request_factory
    ):
        """Test processing invalid JSON request."""
        server_instance.request_factory = mock_request_factory
        mock_conn = mock.Mock()
        server_instance._process_client_request(
            mock_conn,
            b"invalid json"
        )
        assert mock_conn.send.called
        sent_data = json.loads(
            mock_conn.send.call_args[0][0].decode().strip()
        )
        assert sent_data[STR_CODE] == Codes.CODE_ERROR

class TestServerLifecycle:
    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_start_server(
        self,
        server_instance,
        monkeypatch
    ):
        """Test server startup and shutdown.

        Args:
            server_instance: The server instance being tested
            monkeypatch: Pytest fixture for modifying objects
            
        Tests:
            - Server initialization
            - Thread creation and startup
            - Kernel server setup
            - Proper cleanup on shutdown
            - Resource cleanup
        """
        mock_thread = mock.Mock()
        mock_thread.is_alive.return_value = True
        mock_thread.join = mock.Mock()
        mock_thread_class = mock.Mock(return_value=mock_thread)
        monkeypatch.setattr('threading.Thread', mock_thread_class)
        mock_kernel_server = mock.AsyncMock()
        mock_kernel_server.serve_forever = mock.AsyncMock(
            side_effect=lambda: server_instance.__setattr__('running', False)
        )
        mock_kernel_server.close = mock.AsyncMock()
        mock_kernel_server.wait_closed = mock.AsyncMock()
        
        async def mock_start_server(*args, **kwargs):
            return mock_kernel_server
        monkeypatch.setattr('asyncio.start_server', mock_start_server)
        
        def mock_cleanup(kernel_server, client_thread):
            server_instance.running = False
            if kernel_server:
                kernel_server.close()
            if client_thread and client_thread.is_alive():
                client_thread.join(timeout=1.0)
                
        monkeypatch.setattr(server_instance, '_cleanup_server', mock_cleanup)
        await server_instance.start_server()
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        mock_kernel_server.close.assert_called_once()
        assert not server_instance.running

    def test_cleanup_server(self, server_instance, monkeypatch):
        """Test server cleanup."""
        mock_kernel_server = mock.Mock()
        mock_kernel_server.close = mock.Mock()
        
        async def mock_wait_closed():
            return None
        mock_kernel_server.wait_closed = mock.AsyncMock(return_value=None)
        
        def mock_run(coro):
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        monkeypatch.setattr('asyncio.run', mock_run)
        mock_thread = mock.Mock()
        mock_thread.is_alive.return_value = True
        server_instance._cleanup_server(mock_kernel_server, mock_thread)
        assert not server_instance.running
        mock_kernel_server.close.assert_called_once()
        mock_thread.join.assert_called_once_with(timeout=1.0)