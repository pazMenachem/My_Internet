import pytest
import socket
import json
import time
import threading
from unittest import mock
import logging
from typing import Generator

from client.src.Application import Application
from server.src.server import Server
from server.src.db_manager import DatabaseManager
from server.src.dns_manager import DNSManager
from client.src.utils import (
    Codes, STR_CODE, STR_CONTENT, STR_OPERATION, STR_DOMAINS, STR_SETTINGS,
    STR_AD_BLOCK, STR_ADULT_BLOCK
)
from server.src.utils import DEFAULT_ADDRESS, CLIENT_PORT

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    """Create a database manager with temporary database."""
    db_path = tmp_path / "test.db"
    manager = DatabaseManager(str(db_path))
    manager._create_tables()
    return manager

@pytest.fixture
def mock_dns_manager() -> mock.Mock:
    """Create a mock DNS manager."""
    dns_manager = mock.Mock(spec=DNSManager)
    dns_manager.update_dns_settings = mock.Mock()
    return dns_manager

@pytest.fixture
def mock_view() -> mock.Mock:
    """Create a mock view with all required methods."""
    view = mock.Mock()
    view.update_initial_settings = mock.Mock()
    view.ad_block_response = mock.Mock()
    view.adult_block_response = mock.Mock()
    view.add_domain_response = mock.Mock()
    view.remove_domain_response = mock.Mock()
    view.update_domain_list_response = mock.Mock()
    view.root = mock.Mock()
    view.root.winfo_exists = mock.Mock(return_value=True)
    return view

@pytest.fixture
def server_socket() -> Generator[socket.socket, None, None]:
    """Create and configure server socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.0)  # Add timeout to prevent hanging
    
    # Find available port
    for port in range(CLIENT_PORT, CLIENT_PORT + 10):
        try:
            sock.bind((DEFAULT_ADDRESS, port))
            sock.listen(1)
            break
        except OSError:
            if port == CLIENT_PORT + 9:
                raise
            continue
    
    yield sock
    sock.close()

@pytest.fixture
def server_instance(
    db_manager: DatabaseManager,
    mock_dns_manager: mock.Mock,
    server_socket: socket.socket
) -> Generator[Server, None, None]:
    """Create and start a server instance."""
    server = Server(db_manager)
    server.running = True
    
    # Replace DNS manager in all handlers
    for handler in server.request_factory.handlers.values():
        handler.dns_manager = mock_dns_manager
    
    def accept_connections(sock: socket.socket, server_instance: Server):
        while server_instance.running:
            try:
                conn, addr = sock.accept()
                server_instance.logger.info(f"Accepted connection from {addr}")
                client_thread = threading.Thread(
                    target=server_instance._handle_client_communication,
                    args=(conn,),
                    daemon=True
                )
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if server_instance.running:  # Only log if server is still running
                    server_instance.logger.error(f"Error accepting connections: {e}")
                break
    
    accept_thread = threading.Thread(
        target=accept_connections,
        args=(server_socket, server),
        daemon=True
    )
    accept_thread.start()
    
    yield server
    
    server.running = False
    accept_thread.join(timeout=1)

@pytest.fixture
def application(mock_view: mock.Mock) -> Generator[Application, None, None]:
    """Create application instance with mock view."""
    app = Application()
    app._view = mock_view
    yield app
    app._cleanup()

def start_client_communication(application: Application) -> None:
    """Helper function to start client communication."""
    comm_thread = threading.Thread(
        target=application._start_communication,
        daemon=True
    )
    comm_thread.start()
    time.sleep(1)  # Wait for connection to establish

def test_initial_connection(server_instance: Server, application: Application, mock_view: mock.Mock):
    """Test initial connection and settings retrieval."""
    start_client_communication(application)
    
    request = {
        STR_CODE: Codes.CODE_INIT_SETTINGS,
        STR_OPERATION: Codes.CODE_INIT_SETTINGS
    }
    
    application._handle_request(json.dumps(request), to_server=True)
    time.sleep(1)  # Wait for response
    
    assert mock_view.update_initial_settings.call_count >= 1

def test_ad_block_workflow(server_instance: Server, application: Application, mock_view: mock.Mock):
    """Test complete ad blocking workflow."""
    start_client_communication(application)
    
    request = {
        STR_CODE: Codes.CODE_AD_BLOCK,
        STR_CONTENT: "on",
        STR_OPERATION: Codes.CODE_AD_BLOCK
    }
    
    application._handle_request(json.dumps(request), to_server=True)
    time.sleep(1)  # Increased wait time
    
    assert mock_view.ad_block_response.call_count >= 1

def test_add_domain_workflow(server_instance: Server, application: Application, mock_view: mock.Mock):
    """Test adding a domain to the block list."""
    start_client_communication(application)
    
    request = {
        STR_CODE: Codes.CODE_ADD_DOMAIN,
        STR_CONTENT: "example.com",
        STR_OPERATION: Codes.CODE_ADD_DOMAIN
    }
    
    application._handle_request(json.dumps(request), to_server=True)
    time.sleep(1)
    
    assert mock_view.add_domain_response.call_count >= 1

def test_remove_domain_workflow(server_instance: Server, application: Application, mock_view: mock.Mock):
    """Test removing a domain from the block list."""
    start_client_communication(application)
    
    # First add a domain
    add_request = {
        STR_CODE: Codes.CODE_ADD_DOMAIN,
        STR_CONTENT: "example.com",
        STR_OPERATION: Codes.CODE_ADD_DOMAIN
    }
    
    application._handle_request(json.dumps(add_request), to_server=True)
    time.sleep(1)
    
    # Then remove it
    remove_request = {
        STR_CODE: Codes.CODE_REMOVE_DOMAIN,
        STR_CONTENT: "example.com",
        STR_OPERATION: Codes.CODE_REMOVE_DOMAIN
    }
    
    application._handle_request(json.dumps(remove_request), to_server=True)
    time.sleep(1)
    
    assert mock_view.remove_domain_response.call_count >= 1