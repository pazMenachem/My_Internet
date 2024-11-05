import pytest
import json
import asyncio
from unittest import mock
from typing import AsyncGenerator, Dict, Any

from My_Internet.server.src.server import (
    handle_client,
    handle_kernel,
    route_kernel_request,
    start_server
)
from My_Internet.server.src.config import HOST, CLIENT_PORT, KERNEL_PORT
from My_Internet.server.src.handlers import RequestFactory
from My_Internet.server.src.response_codes import SUCCESS, INVALID_REQUEST

class TestServer:
    @pytest.fixture
    def mock_stream_reader(self) -> mock.AsyncMock:
        reader = mock.AsyncMock()
        reader.readline = mock.AsyncMock()
        return reader

    @pytest.fixture
    def mock_stream_writer(self) -> mock.Mock:
        writer = mock.Mock()
        writer.write = mock.Mock()
        writer.drain = mock.AsyncMock()
        writer.close = mock.Mock()
        return writer

    @pytest.mark.asyncio  # Only for async functions
    async def test_handle_client(
        self,
        mock_stream_reader: mock.AsyncMock,
        mock_stream_writer: mock.Mock,
        request_factory: RequestFactory
    ) -> None:
        """Test client request handling."""
        test_request = {
            'type': 'domain_block',
            'action': 'block',
            'domain': 'example.com'
        }
        
        mock_stream_reader.readline.side_effect = [
            json.dumps(test_request).encode() + b'\n',
            b''
        ]
        
        await handle_client(mock_stream_reader, mock_stream_writer, request_factory)
        
        assert mock_stream_writer.write.called
        assert mock_stream_writer.drain.called
        assert mock_stream_writer.close.called

    @pytest.mark.asyncio  # Only for async functions
    async def test_handle_kernel(
        self,
        mock_stream_reader: mock.AsyncMock,
        mock_stream_writer: mock.Mock,
        mock_db_manager: mock.Mock
    ) -> None:
        """Test kernel request handling."""
        test_request = {
            'domain': 'example.com',
            'categories': ['adult']
        }
        
        mock_stream_reader.readline.side_effect = [
            json.dumps(test_request).encode() + b'\n',
            b''
        ]
        
        await handle_kernel(mock_stream_reader, mock_stream_writer, mock_db_manager)
        
        assert mock_stream_writer.write.called
        assert mock_stream_writer.drain.called
        assert mock_stream_writer.close.called

    # No asyncio marker for synchronous functions
    def test_route_kernel_request(self, mock_db_manager: mock.Mock) -> None:
        """Test kernel request routing."""
        # Test blocked domain
        mock_db_manager.is_domain_blocked.return_value = True
        response = route_kernel_request({'domain': 'example.com'}, mock_db_manager)
        assert response['block'] is True

        # Test allowed domain
        mock_db_manager.is_domain_blocked.return_value = False
        mock_db_manager.is_easylist_blocked.return_value = False
        response = route_kernel_request({'domain': 'example.com'}, mock_db_manager)
        assert response['block'] is False

    @pytest.mark.asyncio  # Only for async functions
    async def test_start_server(self, mock_db_manager: mock.Mock) -> None:
        """Test server startup."""
        mock_client_server = mock.AsyncMock()
        mock_kernel_server = mock.AsyncMock()
        
        with mock.patch('asyncio.start_server', 
                       side_effect=[mock_client_server, mock_kernel_server]) as mock_start:
            task = asyncio.create_task(start_server(mock_db_manager))
            await asyncio.sleep(0.1)
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            assert mock_start.call_count == 2
            assert mock_client_server.serve_forever.called
            assert mock_kernel_server.serve_forever.called

    @pytest.mark.asyncio  # Only for async functions
    async def test_client_connection_error(
        self,
        mock_stream_reader: mock.AsyncMock,
        mock_stream_writer: mock.Mock,
        request_factory: RequestFactory
    ) -> None:
        """Test handling of client connection errors."""
        mock_stream_reader.readline.side_effect = ConnectionResetError()
        
        await handle_client(mock_stream_reader, mock_stream_writer, request_factory)
        assert mock_stream_writer.close.called

    # No asyncio marker for synchronous functions
    @pytest.mark.parametrize("request_data,expected_block", [
        ({'domain': 'example.com', 'categories': []}, False),
        ({'domain': 'blocked.com', 'categories': ['adult']}, True),
    ])
    def test_kernel_request_scenarios(
        self,
        request_data: Dict[str, Any],
        expected_block: bool,
        mock_db_manager: mock.Mock
    ) -> None:
        """Test various kernel request scenarios."""
        is_blocked = 'blocked.com' in request_data['domain']
        mock_db_manager.is_domain_blocked.return_value = is_blocked
        
        response = route_kernel_request(request_data, mock_db_manager)
        assert response['block'] is expected_block