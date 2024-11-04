# server.py

import asyncio
import json
from typing import Dict, Any
from My_Internet.server.src.config import HOST, CLIENT_PORT, KERNEL_PORT, DB_FILE
from My_Internet.server.src.db_manager import DatabaseManager
from My_Internet.server.src.handlers import AdBlockHandler, DomainBlockHandler, AdultContentBlockHandler
from response_codes import INVALID_REQUEST, RESPONSE_MESSAGES


async def handle_client(
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
            response_data = route_request(request_data, db_manager)

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

# create request factory class , and make an instance of it to handle the request base on the data send it to the right handler.
def route_request(request_data: Dict[str, Any], db_manager: DatabaseManager) -> Dict[str, Any]:
    request_type = request_data.get('type')

    if request_type == 'ad_block':
        handler = AdBlockHandler(db_manager)
    elif request_type == 'domain_block':
        handler = DomainBlockHandler(db_manager)
    elif request_type == 'adult_content_block':
        handler = AdultContentBlockHandler()
    else:
        return {
            'code': INVALID_REQUEST,
            'message': RESPONSE_MESSAGES[INVALID_REQUEST]
        }

    return handler.handle_request(request_data)


def route_kernel_request(request_data: Dict[str, Any], db_manager: DatabaseManager) -> Dict[str, Any]:
    domain = request_data.get('domain')

    if db_manager.is_domain_blocked(domain) or db_manager.is_easylist_blocked(domain):
        return {'block': True}
    else:
        return {'block': False}


async def start_server(db_manager: DatabaseManager) -> None:
    client_server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, db_manager), 
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