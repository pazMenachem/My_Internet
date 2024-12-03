import pytest
import json
import asyncio
from unittest import mock
from typing import Dict, Any, Generator
from My_Internet.server.src.server import Server
from My_Internet.server.src.utils import HOST, CLIENT_PORT, KERNEL_PORT

@pytest.mark.asyncio
async def test_handle_kernel_requests_block_custom_domain(
    server_instance: Server,
    mock_stream_reader: mock.AsyncMock,
    mock_stream_writer: mock.Mock
) -> None:
    """Test handling kernel requests for custom blocked domain."""
    server_instance.db_manager.is_domain_blocked.return_value = True
    mock_stream_reader.readline.side_effect = [
        json.dumps({
            'domain': 'example.com',
            'is_ad': False,
            'categories': []
        }).encode() + b'\n',
        b''
    ]
    
    await server_instance.handle_kernel_requests(mock_stream_reader, mock_stream_writer)
    
    response_data = json.loads(mock_stream_writer.write.call_args[0][0].decode().strip())
    assert response_data['block'] is True
    assert response_data['reason'] == 'custom_blocklist'
    assert response_data['domain'] == 'example.com'

@pytest.mark.asyncio
async def test_handle_kernel_requests_block_ad(
    server_instance: Server,
    mock_stream_reader: mock.AsyncMock,
    mock_stream_writer: mock.Mock
) -> None:
    """Test handling kernel requests for ad blocking."""
    server_instance.db_manager.is_domain_blocked.return_value = False
    server_instance.db_manager.get_setting.side_effect = lambda x: 'on' if x == 'ad_block' else 'off'
    mock_stream_reader.readline.side_effect = [
        json.dumps({
            'domain': 'ad.example.com',
            'is_ad': True,
            'categories': []
        }).encode() + b'\n',
        b''
    ]
    
    await server_instance.handle_kernel_requests(mock_stream_reader, mock_stream_writer)
    
    response_data = json.loads(mock_stream_writer.write.call_args[0][0].decode().strip())
    assert response_data['block'] is True
    assert response_data['reason'] == 'ads'
    assert response_data['domain'] == 'ad.example.com'

@pytest.mark.asyncio
async def test_handle_kernel_requests_block_adult_content(
    server_instance: Server,
    mock_stream_reader: mock.AsyncMock,
    mock_stream_writer: mock.Mock
) -> None:
    """Test handling kernel requests for adult content blocking."""
    server_instance.db_manager.is_domain_blocked.return_value = False
    server_instance.db_manager.get_setting.side_effect = lambda x: 'on' if x == 'adult_block' else 'off'
    mock_stream_reader.readline.side_effect = [
        json.dumps({
            'domain': 'adult.example.com',
            'is_ad': False,
            'categories': ['adult']
        }).encode() + b'\n',
        b''
    ]
    
    await server_instance.handle_kernel_requests(mock_stream_reader, mock_stream_writer)
    
    response_data = json.loads(mock_stream_writer.write.call_args[0][0].decode().strip())
    assert response_data['block'] is True
    assert response_data['reason'] == 'adult_content'
    assert response_data['domain'] == 'adult.example.com'

def test_handle_client_thread_initial_domain_list(
    server_instance: Server,
    mock_socket: mock.Mock,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test sending initial domain list to client."""
    mock_conn = mock.Mock()
    mock_conn.send = mock.Mock()
    mock_conn.recv.return_value = b''
    
    server_instance.db_manager.get_blocked_domains.return_value = ['example.com']
    
    mock_socket_instance = mock.Mock()
    mock_socket_instance.accept = mock.Mock(return_value=(mock_conn, ('127.0.0.1', 12345)))
    
    mock_socket_class = mock.Mock(return_value=mock_socket_instance)
    monkeypatch.setattr('socket.socket', mock_socket_class)
    
    def mock_accept(*args: Any, **kwargs: Any) -> tuple[mock.Mock, tuple[str, int]]:
        server_instance.running = False
        return mock_conn, ('127.0.0.1', 12345)
    
    mock_socket_instance.accept = mock.Mock(side_effect=mock_accept)
    
    server_instance.handle_client_thread()
    
    mock_conn.send.assert_called()
    sent_data = json.loads(mock_conn.send.call_args_list[0][0][0].decode().strip())
    assert sent_data['type'] == 'domain_list'
    assert isinstance(sent_data['domains'], list)
    assert 'example.com' in sent_data['domains']

def test_handle_client_thread_process_request(
    server_instance: Server,
    mock_socket: mock.Mock,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test processing client request."""
    mock_conn = mock.Mock()
    mock_conn.send = mock.Mock()
    
    mock_conn.recv.side_effect = [
        json.dumps({'code': '50', 'action': 'on'}).encode(),
        b''
    ]
    
    mock_socket_instance = mock.Mock()
    mock_socket_instance.accept = mock.Mock(return_value=(mock_conn, ('127.0.0.1', 12345)))
    
    mock_socket_class = mock.Mock(return_value=mock_socket_instance)
    monkeypatch.setattr('socket.socket', mock_socket_class)
    
    def mock_accept(*args: Any, **kwargs: Any) -> tuple[mock.Mock, tuple[str, int]]:
        server_instance.running = False
        return mock_conn, ('127.0.0.1', 12345)
    
    mock_socket_instance.accept = mock.Mock(side_effect=mock_accept)
    
    server_instance.db_manager.get_blocked_domains.return_value = ['example.com']
    
    mock_request_factory = mock.Mock()
    mock_request_factory.handle_request.return_value = {
        'status': 'success',
        'message': 'Request processed'
    }
    server_instance.request_factory = mock_request_factory
    
    server_instance.handle_client_thread()
    
    assert mock_conn.send.call_count >= 2
    assert server_instance.request_factory.handle_request.called

def test_handle_client_thread_invalid_json(
    server_instance: Server,
    mock_socket: mock.Mock,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test handling invalid JSON request."""
    mock_conn = mock.Mock()
    mock_conn.send = mock.Mock()
    mock_conn.recv.side_effect = [b'invalid json', b'']
    
    mock_socket_instance = mock.Mock()
    mock_socket_instance.accept = mock.Mock(return_value=(mock_conn, ('127.0.0.1', 12345)))
    
    mock_socket_class = mock.Mock(return_value=mock_socket_instance)
    monkeypatch.setattr('socket.socket', mock_socket_class)
    
    def mock_accept(*args: Any, **kwargs: Any) -> tuple[mock.Mock, tuple[str, int]]:
        server_instance.running = False
        return mock_conn, ('127.0.0.1', 12345)
    
    mock_socket_instance.accept = mock.Mock(side_effect=mock_accept)
    
    server_instance.db_manager.get_blocked_domains.return_value = ['example.com']
    
    server_instance.handle_client_thread()
    
    assert mock_conn.send.call_count >= 2
    sent_data = json.loads(mock_conn.send.call_args_list[1][0][0].decode().strip())
    assert sent_data['status'] == 'error'
    assert 'Invalid JSON format' in sent_data['message']

@pytest.mark.asyncio
async def test_start_server(
    server_instance: Server,
    mock_asyncio_start_server: mock.AsyncMock,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test server startup process."""
    monkeypatch.setattr('asyncio.start_server', mock_asyncio_start_server)
    
    mock_thread = mock.Mock()
    mock_thread_class = mock.Mock(return_value=mock_thread)
    monkeypatch.setattr('threading.Thread', mock_thread_class)
    
    mock_kernel_server = mock.AsyncMock()
    mock_kernel_server.__aenter__ = mock.AsyncMock(return_value=mock_kernel_server)
    mock_kernel_server.__aexit__ = mock.AsyncMock()
    mock_kernel_server.close = mock.AsyncMock()
    
    async def mock_serve_forever():
        server_instance.running = False
    
    mock_kernel_server.serve_forever = mock.AsyncMock(side_effect=mock_serve_forever)
    mock_asyncio_start_server.return_value = mock_kernel_server
    
    await server_instance.start_server()
    
    mock_thread_class.assert_called_once()
    mock_thread.start.assert_called_once()
    assert mock_asyncio_start_server.called
    assert mock_kernel_server.__aenter__.called
    assert mock_kernel_server.serve_forever.called
    assert not server_instance.running
    await mock_kernel_server.close()