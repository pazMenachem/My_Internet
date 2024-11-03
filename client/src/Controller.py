import logging
import os
from datetime import datetime
from typing import Optional

from .Communicator import Communicator
from .View import Viewer

LOG_DIR = "client_logs"

class Controller:
    def __init__(self) -> None:
        self._view: Viewer = Viewer()
        self._communicator: Communicator = Communicator()
        self._logger: Optional[logging.Logger] = None

        self._logger_setup()

    def run(self) -> None:
        """Run the controller."""
        self._logger.info("Starting application")
        
        try:    
            self._view.run()
            
        except Exception as e:
            self._logger.error(f"Error during execution: {str(e)}", exc_info=True)
            raise
    
    def _logger_setup(self) -> None:
        """Set up the logger."""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        log_file: str = os.path.join(
            LOG_DIR, f"Client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ],
        )

        self._logger = logging.getLogger(__name__)
        self._logger.info("Logger setup complete")
