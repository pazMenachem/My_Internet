from View import Viewer
from Communicator import Communicator
import os
import logging
from datetime import datetime

LOG_DIR = "client_logs"

class Controller:
    def __init__(self):
        self._view = Viewer()
        self._communicator = Communicator()
        self._logger = None
        self._logger_setup()

    def run(self):
        self._logger.info("Starting application")
        
        try:    
            self._view.run()
            
        except Exception as e:
            self._logger.error(f"Error during execution: {str(e)}", exc_info=True)
            raise
    
    def _logger_setup(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        log_file = os.path.join(LOG_DIR, f"client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self._logger = logging.getLogger(__name__)
        self._logger.info("Logger setup complete")
