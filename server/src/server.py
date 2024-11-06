import asyncio
import json
import uuid
from typing import Dict, Any, Set, Optional
from .config import HOST, CLIENT_PORT, KERNEL_PORT, DB_FILE
from .db_manager import DatabaseManager
from .state_manager import StateManager
from .handlers import RequestFactory
from .response_codes import (
    create_response,
    create_error_response,
    ServerCodes,
    ClientCodes
)

class Server:
    def __init__(self, db_file: str):
        """Initialize server with all necessary components."""
        self.db_manager = DatabaseManager(db_file)
        self.state_manager = StateManager(self.db_manager)
        self.request_factory = RequestFactory(self.db_manager, self.state_manager)
        
        # Track client connections
        self.clients: Dict[str, asyncio.StreamWriter] = {}
        self.kernel_writers: Set[asyncio.StreamWriter] = set()

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle client connections with unique ID and state tracking."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = writer
        self.state_manager.register_client(client_id)
        
        try:
            # Send initial state to client
            await self.send_initial_state(writer, client_id)
            
            while True:
                data = await reader.readline()
                if not data:
                    break

                request_data = json.loads(data.decode('utf-8'))
                response_data = self.request_factory.handle_request(request_data)

                # Send response to the requesting client
                writer.write(json.dumps(response_data).encode('utf-8') + b'\n')
                await writer.drain()

                # Broadcast updates if necessary
                if self._should_broadcast(request_data):
                    await self.broadcast_state_update(client_id)

        except Exception as e:
            print(f"Error handling client {client_id}: {str(e)}")
        finally:
            self.cleanup_client(client_id, writer)

    async def handle_kernel(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """Handle kernel module connections."""
        self.kernel_writers.add(writer)
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                request_data = json.loads(data.decode('utf-8'))
                response = self.handle_kernel_request(request_data)
                
                writer.write(json.dumps(response).encode('utf-8') + b'\n')
                await writer.drain()

        except Exception as e:
            print(f"Error handling kernel request: {str(e)}")
        finally:
            self.kernel_writers.remove(writer)
            writer.close()
            await writer.wait_closed()

    def handle_kernel_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process kernel module requests."""
        domain = request_data.get('domain')
        categories = request_data.get('categories', [])

        # Check various blocking conditions
        should_block = (
            self.db_manager.is_domain_blocked(domain) or
            (self.db_manager.is_easylist_blocked(domain) and
             self.state_manager.get_feature_state('ad_block')['state'] == 'on') or
            (
                'adult' in categories and
                self.state_manager.get_feature_state('adult_block')['state'] == 'on'
            )
        )

        return {'block': should_block}

    async def send_initial_state(
        self,
        writer: asyncio.StreamWriter,
        client_id: str
    ) -> None:
        """Send initial state to new client connections."""
        initial_state = {
            'settings': {
                'ad_block': self.state_manager.get_feature_state('ad_block'),
                'adult_block': self.state_manager.get_feature_state('adult_block')
            },
            'domains': list(self.state_manager.get_all_domains().keys())
        }
        
        response = create_response(
            ServerCodes.SUCCESS,
            ClientCodes.DOMAIN_LIST_UPDATE,
            content=initial_state
        )
        
        writer.write(json.dumps(response).encode('utf-8') + b'\n')
        await writer.drain()

    async def broadcast_state_update(self, exclude_client: Optional[str] = None) -> None:
        """Broadcast state updates to all connected clients except the sender."""
        domains = list(self.state_manager.get_all_domains().keys())
        update_message = create_response(
            ServerCodes.SUCCESS,
            ClientCodes.DOMAIN_LIST_UPDATE,
            content=domains
        )
        
        message_data = json.dumps(update_message).encode('utf-8') + b'\n'
        
        for client_id, writer in self.clients.items():
            if client_id != exclude_client:
                try:
                    writer.write(message_data)
                    await writer.drain()
                except Exception as e:
                    print(f"Error broadcasting to client {client_id}: {str(e)}")

    def cleanup_client(self, client_id: str, writer: asyncio.StreamWriter) -> None:
        """Clean up client connection resources."""
        if client_id in self.clients:
            del self.clients[client_id]
        self.state_manager.unregister_client(client_id)
        writer.close()

    def _should_broadcast(self, request_data: Dict[str, Any]) -> bool:
        """Determine if a request should trigger a broadcast."""
        broadcast_codes = {
            ClientCodes.ADD_DOMAIN,
            ClientCodes.REMOVE_DOMAIN,
            ClientCodes.AD_BLOCK,
            ClientCodes.ADULT_BLOCK
        }
        return request_data.get('code') in broadcast_codes

async def start_server(db_manager: DatabaseManager) -> None:
    """Start the server with both client and kernel handlers."""
    server = Server(db_manager.db_file)
    
    client_server = await asyncio.start_server(
        server.handle_client,
        HOST,
        CLIENT_PORT
    )
    
    kernel_server = await asyncio.start_server(
        server.handle_kernel,
        HOST,
        KERNEL_PORT
    )

    print(f"Client server running on {HOST}:{CLIENT_PORT}")
    print(f"Kernel server running on {HOST}:{KERNEL_PORT}")

    async with client_server, kernel_server:
        await asyncio.gather(
            client_server.serve_forever(),
            kernel_server.serve_forever()
        )

def run(db_file: str) -> None:
    """Initialize and run the server."""
    try:
        asyncio.run(start_server(DatabaseManager(db_file)))
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {str(e)}")