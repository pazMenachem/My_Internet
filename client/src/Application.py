import json
import threading
from .Communicator import Communicator
from .View import Viewer
from .Logger import setup_logger
from .ConfigManager import ConfigManager

class Application:
    """
    Main application class that coordinates communication between UI and server.
    
    Uses threading to handle simultaneous GUI and network operations.
    
    Attributes:
        _logger: Logger instance for application logging
        _view: Viewer instance for GUI operations
        _communicator: Communicator instance for network operations
    """
    
    def __init__(self) -> None:
        """Initialize application components."""
        self._logger = setup_logger(__name__)
        self._config_manager = ConfigManager()
        self._view = Viewer(config_manager=self._config_manager, message_callback=self._handle_request)
        self._communicator = Communicator(config_manager=self._config_manager, message_callback=self._handle_request)

    def run(self) -> None:
        """
        Start the application with threaded communication handling.
        
        Raises:
            Exception: If there's an error during startup of either component.
        """
        self._logger.info("Starting application")
        
        try:
            # self._start_communication()
            self._start_gui()
            
        except Exception as e:
            self._logger.error(f"Error during execution: {str(e)}", exc_info=True)
            raise
        finally:
            self._cleanup()

    def _start_communication(self) -> None:
        """Initialize and start the communication thread."""
        try:
            self._communicator.connect()
            threading.Thread(
                target=self._communicator.receive_message,
                daemon=True
            ).start()
            
            self._logger.info("Communication server started successfully")
        except Exception as e:
            self._logger.error(f"Failed to start communication: {str(e)}")
            raise

    def _start_gui(self) -> None:
        """Start the GUI main loop."""
        try:
            self._logger.info("Starting GUI")
            self._view.run()
            
        except Exception as e:
            self._logger.error(f"Failed to start GUI: {str(e)}")
            raise

    def _handle_request(self, request: str) -> None:
        """
        Handle outgoing messages from the UI and Server.
        
        Args:
            request: received request from server or user input from UI.
        """
        try:
            self._logger.info(f"Processing request: {request}")
            
            pass ## TODO: Implement request handling from server or UI.
            
        except json.JSONDecodeError as e:
            self._logger.error(f"Invalid JSON format: {str(e)}")
            raise
        except Exception as e:
            self._logger.error(f"Error handling request: {str(e)}")
            raise

    def _cleanup(self) -> None:
        """Clean up resources and stop threads."""
        self._logger.info("Cleaning up application resources")
        try:
            if self._communicator:
                self._communicator.close()
                
            if self._view and self._view.root.winfo_exists():
                self._view.root.destroy()
                
        except Exception as e:
            self._logger.warning(f"Cleanup encountered an error: {str(e)}")
