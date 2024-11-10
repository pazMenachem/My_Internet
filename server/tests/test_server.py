import pytest
import json
import asyncio
from unittest import mock
from typing import Dict, Any
from My_Internet.server.src.server import (
    Server,
    start_server
)
from My_Internet.server.src.config import HOST, CLIENT_PORT, KERNEL_PORT
from My_Internet.server.src.response_codes import Codes
from My_Internet.server.src.db_manager import DatabaseManager

class TestServer:
    @pytest.fixture
    def db_manager(self) -> mock.Mock:
        """Create a mock database manager."""
        mock_db = mock.Mock(spec=DatabaseManager)
        mock_db.db_file = "test.db"
        mock_db.is_domain_blocked.return_value = True
        mock_db.get_setting.return_value = "on"
        return mock_db

    @pytest.fixture
    def server(self, db_manager: mock.Mock) -> Server:
        """Create server instance for testing with a mocked DatabaseManager."""
        return Server(db_manager)

    @pytest.fixture
    def mock_stream_reader(self) -> mock.AsyncMock:
        """Mock for asyncio StreamReader."""
        reader = mock.AsyncMock()
        reader.readline = mock.AsyncMock()
        return reader

    @pytest.fixture
    def mock_stream_writer(self) -> mock.Mock:
        """Mock for asyncio StreamWriter."""
        writer = mock.Mock()
        writer.write = mock.Mock()
        writer.drain = mock.AsyncMock()
        writer.close = mock.Mock()
        writer.wait_closed = mock.AsyncMock()
        return writer

    @pytest.mark.asyncio
    async def test_handle_client(
        self,
        server: Server,
        mock_stream_reader: mock.AsyncMock,
        mock_stream_writer: mock.Mock
    ) -> None:
        """Test client request handling."""
        # Setup mocks
        mock_stream_writer.write = mock.Mock()
        mock_stream_writer.drain = mock.AsyncMock()
        mock_stream_writer.get_extra_info = mock.Mock(return_value="test_client")
        server.db_manager.get_blocked_domains.return_value = []
        
        # Setup test request
        test_request = {
            'code': Codes.CODE_ADD_DOMAIN,
            'action': 'block',
            'domain': 'example.com'
        }

        # Configure mock reader responses
        mock_stream_reader.readline.side_effect = [
            json.dumps(test_request).encode() + b'\n',
            b''  # End connection after request
        ]

        # Handle client connection
        await server.handle_client(mock_stream_reader, mock_stream_writer)

        # Verify response was sent at least twice (domain list + request response)
        assert mock_stream_writer.write.call_count >= 2

    @pytest.mark.asyncio
    async def test_handle_kernel(self, server: Server, mock_stream_reader: mock.AsyncMock, mock_stream_writer: mock.Mock) -> None:
        """Test kernel module request handling."""
        # Setup test request
        test_request = {
            'domain': 'example.com',
            'categories': ['adult']
        }
        
        # Configure mocks
        server.db_manager.is_domain_blocked.return_value = True
        mock_stream_writer.write = mock.Mock()
        mock_stream_writer.drain = mock.AsyncMock()
        
        # Configure mock reader responses
        mock_stream_reader.readline.side_effect = [
            json.dumps(test_request).encode() + b'\n',
            b''  # End connection after request
        ]
        
        await server.handle_kernel(mock_stream_reader, mock_stream_writer)
        assert mock_stream_writer.write.called

    def test_handle_kernel_request(self, server: Server) -> None:
        """Test kernel request processing."""
        test_cases = [
            # Test manually blocked domain
            {
                'setup': {
                    'is_domain_blocked': True,
                    'get_setting': 'off'
                },
                'request': {
                    'domain': 'blocked.com'
                },
                'expected': True
            },
            # Test ad blocking
            {
                'setup': {
                    'is_domain_blocked': False,
                    'get_setting': 'on',
                    'is_easylist_blocked': True
                },
                'request': {
                    'domain': 'ads.example.com'
                },
                'expected': True
            },
            # Test adult content blocking
            {
                'setup': {
                    'is_domain_blocked': False,
                    'get_setting': 'on'
                },
                'request': {
                    'domain': 'example.com',
                    'categories': ['adult']
                },
                'expected': True
            },
            # Test allowed domain
            {
                'setup': {
                    'is_domain_blocked': False,
                    'get_setting': 'off',
                    'is_easylist_blocked': False
                },
                'request': {
                    'domain': 'example.com'
                },
                'expected': False
            }
        ]

        for case in test_cases:
            # Setup mocks
            server.db_manager.is_domain_blocked.return_value = case['setup'].get('is_domain_blocked', False)
            server.db_manager.get_setting.return_value = case['setup'].get('get_setting', 'off')
            server.db_manager.is_easylist_blocked.return_value = case['setup'].get('is_easylist_blocked', False)
            
            # Test request
            response = server.handle_kernel_request(case['request'])
            assert response['block'] is case['expected']

    @pytest.mark.asyncio
    async def test_start_server(self, db_manager: mock.Mock) -> None:
        """Test server startup."""
        # Configure mock
        db_manager.db_file = "test.db"
        mock_client_server = mock.AsyncMock()
        mock_kernel_server = mock.AsyncMock()
        
        with mock.patch('asyncio.start_server', side_effect=[mock_client_server, mock_kernel_server]) as mock_start:
            task = asyncio.create_task(start_server(db_manager))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_client_error_handling(
        self,
        server: Server,
        mock_stream_reader: mock.AsyncMock,
        mock_stream_writer: mock.Mock
    ) -> None:
        """Test handling of client errors."""
        # Configure mocks
        mock_stream_writer.write = mock.Mock()
        mock_stream_writer.drain = mock.AsyncMock()
        mock_stream_writer.get_extra_info = mock.Mock(return_value="test_client")
        server.db_manager.get_blocked_domains.return_value = []

        # Set up the mock to return invalid JSON
        mock_stream_reader.readline.side_effect = [
            b'invalid json\n',
            b''  # End connection after invalid request
        ]

        # Handle the client connection
        await server.handle_client(mock_stream_reader, mock_stream_writer)

        # Verify responses were sent (domain list + error response)
        assert mock_stream_writer.write.call_count >= 2

    @pytest.mark.asyncio
    async def test_kernel_error_handling(
        self,
        server: Server,
        mock_stream_reader: mock.AsyncMock,
        mock_stream_writer: mock.Mock
    ) -> None:
        """Test handling of kernel errors."""
        # Test connection error
        mock_stream_reader.readline.side_effect = ConnectionError()
        
        await server.handle_kernel(mock_stream_reader, mock_stream_writer)
        
        # Verify connection was closed
        assert mock_stream_writer.close.called

    def test_multiple_kernel_requests(self, server: Server) -> None:
        """Test handling multiple kernel requests."""
        # Setup mocks
        server.db_manager.get_setting.side_effect = ['on', 'off']
        server.db_manager.is_domain_blocked.return_value = True
        
        # Test first request (blocking enabled)
        response1 = server.handle_kernel_request({
            'domain': 'example.com',
            'categories': ['adult']
        })
        assert response1['block'] is True
