# server.py

import asyncio
import json
from typing import Dict, Any
from My_Internet.server.src.config import HOST, CLIENT_PORT, KERNEL_PORT, DB_FILE
from My_Internet.server.src.db_manager import DatabaseManager
from My_Internet.server.src.handlers import RequestFactory, AdultContentBlockHandler



async def handle_client(
    reader: asyncio.StreamReader, 
    writer: asyncio.StreamWriter, 
    request_factory: RequestFactory
) -> None:
    while True:
        try:
            data = await reader.readline()
            if not data:
                break

            request_data = json.loads(data.decode('utf-8'))
            response_data = request_factory.handle_request(request_data)

            writer.write(json.dumps(response_data).encode('utf-8') + b'\n')
            await writer.drain()

        except ConnectionResetError:
            print("Client disconnected.")
            break

    writer.close()


async def handle_kernel(
    reader: asyncio.StreamReader, 
    writer: asyncio.StreamWriter, 
    db_manager: DatabaseManager
) -> None:
    while True:
        try:
            data = await reader.readline()
            if not data:
                break

            request_data = json.loads(data.decode('utf-8'))
            response_data = route_kernel_request(request_data, db_manager)

            writer.write(json.dumps(response_data).encode('utf-8') + b'\n')
            await writer.drain()

        except ConnectionResetError:
            print("Kernel module disconnected.")
            break

    writer.close()


def route_kernel_request(request_data: Dict[str, Any], db_manager: DatabaseManager) -> Dict[str, Any]:
    domain = request_data.get('domain')
    categories = request_data.get('categories', [])

    # Fast checks in order of most common to least common
    should_block = (
        db_manager.is_domain_blocked(domain) or 
        db_manager.is_easylist_blocked(domain) or
        (AdultContentBlockHandler.is_blocking_enabled() and 'adult' in categories)
    )

    return {'block': should_block}


async def start_server(db_manager: DatabaseManager) -> None:
    request_factory = RequestFactory(db_manager)
    
    client_server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, request_factory), 
        HOST, 
        CLIENT_PORT
    )
    kernel_server = await asyncio.start_server(
        lambda r, w: handle_kernel(r, w, db_manager), 
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
    """Initialize and run the server with the given database file."""
    db_manager = DatabaseManager(db_file)
    try:
        asyncio.run(start_server(db_manager))
    except KeyboardInterrupt:
        print("Server stopped by user.")
    finally:
        db_manager.close()