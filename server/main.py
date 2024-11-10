from src.server import initialize_server
from src.config import DB_FILE

if __name__ == '__main__':
    initialize_server(DB_FILE)