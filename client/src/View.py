import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List
import json
from .Logger import setup_logger
from .ConfigManager import ConfigManager

from .utils import (
    Codes,
    WINDOW_SIZE, WINDOW_TITLE,
    ERR_NO_DOMAIN_SELECTED, ERR_DOMAIN_LIST_UPDATE_FAILED,
    STR_AD_BLOCK, STR_ADULT_BLOCK, STR_CODE, STR_BLOCKED_DOMAINS,
    STR_CONTENT, STR_SETTINGS, STR_ERROR, STR_SUCCESS,
    STR_ADD_DOMAIN_RESPONSE, STR_REMOVE_DOMAIN_REQUEST, STR_ADD_DOMAIN_REQUEST,
    STR_AD_BLOCK_RESPONSE, STR_ADULT_BLOCK_RESPONSE, STR_REMOVE_DOMAIN_RESPONSE,
    STR_DOMAINS,
)

class Viewer:
    """
    Graphical user interface for the application.
    """

    def __init__(self, config_manager: ConfigManager, message_callback: Callable[[str], None]) -> None:
        """
        Initialize the viewer window and its components.
        
        Args:
            config_manager: Configuration manager instance
            message_callback: Callback function to handle message sending.
        """
        self.logger = setup_logger(__name__)
        self.logger.info("Initializing Viewer")
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self._message_callback = message_callback

        # Initialize root window first
        self.root: tk.Tk = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        self.root.withdraw()  # Hide the window temporarily
        
        # Configure styles
        style = ttk.Style()
        style.configure('TLabelframe', padding=10)
        style.configure('TLabelframe.Label', font=('Arial', 10, 'bold'))
        style.configure('TButton', padding=5)
        style.configure('TRadiobutton', font=('Arial', 10))
        style.configure('TLabel', font=('Arial', 10))
        
        self._setup_ui()
        
        # Show the window after setup is complete
        self.root.deiconify()
        self.logger.info("Viewer initialization complete")

    def run(self) -> None:
        """Start the main event loop of the viewer."""
        self.logger.info("Starting main event loop")
        self.root.mainloop()

    def get_blocked_domains(self) -> tuple[str, ...]:
        """
        Get the list of currently blocked domains.
        
        Returns:
            A tuple containing all blocked domains.
        """
        return self.domains_listbox.get(0, tk.END)

    def get_block_settings(self) -> dict[str, str]:
        """
        Get the current state of blocking settings.
        
        Returns:
            A dictionary containing the current state of ad and adult content blocking.
        """
        return {
            STR_AD_BLOCK: self.ad_var.get(),
            STR_ADULT_BLOCK: self.adult_var.get()
        }

    def update_domain_list_response(self, domains: List[str]) -> None:
        """
        Update the domains listbox with a new list of domains from the server.

        Args:
            domains: List of domain strings to be displayed in the listbox.
        """
        self.logger.info("Updating domain list from server")

        try:
            self.domains_listbox.delete(0, tk.END)
            
            for domain in domains:
                self.domains_listbox.insert(tk.END, domain)

        except Exception as e:
            self.logger.error(f"Error updating domain list: {str(e)}")
            self._show_error(ERR_DOMAIN_LIST_UPDATE_FAILED)
            return
        
        self.logger.info(f"Updated domain list with {len(domains)} domains")
        
    def add_domain_response(self, response: dict) -> None:
            """
            Handle the response from the server after attempting to add a domain.
            
            Args:
                response: Dictionary containing the server's response with code and content.
            """
            try:
                match response[STR_CODE]:
                    case Codes.CODE_SUCCESS:
                        domain = response[STR_CONTENT]
                        with self._update_list_lock:
                            self.domains_listbox.insert(tk.END, domain)
                            self.domain_entry.delete(0, tk.END)
                            
                        self._show_success(
                            message=f"Domain '{domain}' added successfully",
                            operation=STR_ADD_DOMAIN_RESPONSE
                        )

                    case Codes.CODE_ERROR:
                        self._show_error(
                            message=response[STR_CONTENT],
                            operation=STR_ADD_DOMAIN_RESPONSE
                        )
                
            except Exception as e:
                self._show_error(
                    message="An unexpected error occurred",
                    operation=f"Processing add domain response: {str(e)}"
                )

    def ad_block_response(self, response: dict) -> None:
        """
        Handle the response from the server after changing ad block setting.
        
        Args:
            response: Dictionary containing the server's response with code and content.
        """
        prev_state = "off" if self.ad_var.get() == "on" else "on"
        
        try:
            match response[STR_CODE]:
                case Codes.CODE_SUCCESS:
                    self._show_success(
                        message=f"Ad blocking turned {self.ad_var.get()}",
                        operation=STR_AD_BLOCK_RESPONSE
                    )
                case Codes.CODE_ERROR:
                    self.ad_var.set(prev_state)
                    self._show_error(
                        message=response[STR_CONTENT],
                        operation=STR_AD_BLOCK_RESPONSE
                    )
        except Exception as e:
            self.ad_var.set(prev_state)
            self._show_error(
                message="An unexpected error occurred",
                operation=f"Processing ad block response: {str(e)}"
            )

    def adult_block_response(self, response: dict) -> None:
        """
        Handle the response from the server after changing adult block setting.
        
        Args:
            response: Dictionary containing the server's response with code and content.
        """
        prev_state = "off" if self.adult_var.get() == "on" else "on"
        
        try:
            match response[STR_CODE]:
                case Codes.CODE_SUCCESS:
                    self._show_success(
                        message=f"Adult content blocking turned {self.adult_var.get()}",
                        operation=STR_ADULT_BLOCK_RESPONSE
                    )
                case Codes.CODE_ERROR:
                    self.adult_var.set(prev_state)
                    self._show_error(
                        message=response[STR_CONTENT],
                        operation=STR_ADULT_BLOCK_RESPONSE
                    )
        except Exception as e:
            self.adult_var.set(prev_state)
            self._show_error(
                message="An unexpected error occurred",
                operation=f"Processing adult block response: {str(e)}"
            )

    def remove_domain_response(self, response: dict) -> None:
        """
        Handle the response from the server after removing a domain.
        
        Args:
            response: Dictionary containing the server's response with code and content.
        """
        try:
            match response[STR_CODE]:
                case Codes.CODE_SUCCESS:
                    domain = response[STR_CONTENT]
                    self.domains_listbox.delete(self.domains_listbox.curselection())
                    self._show_success(
                        message=f"Domain '{domain}' removed successfully",
                        operation=STR_REMOVE_DOMAIN_RESPONSE
                    )
                case Codes.CODE_ERROR:
                    self._show_error(
                        message=response[STR_CONTENT],
                        operation=STR_REMOVE_DOMAIN_RESPONSE
                    )
        except Exception as e:
            self._show_error(
                message="An unexpected error occurred",
                operation=f"Processing remove domain response: {str(e)}"
            )

    def update_initial_settings(self, response: dict) -> None:
        """
        Update all initial settings from server response.
        
        Args:
            response: Dictionary containing initial settings:
                     - domains: List of blocked domains
                     - settings: Dictionary with ad_block and adult_block states
        """
        try:
            self.root.after(0, lambda: self.update_domain_list_response(response[STR_DOMAINS]))
            self.root.after(0, lambda: self._update_block_settings(response[STR_SETTINGS]))
            
            self.logger.info("Successfully initialized settings from server")
            
        except Exception as e:
            self._show_error(
                message="Failed to initialize settings",
                operation=f"Initial settings update: {str(e)}"
            )
    
    def _add_domain_request(self) -> None:
        """Add a domain to the blocked sites list."""
        domain = self.domain_entry.get().strip()
        
        if domain:
            self.logger.debug(f"Sending add domain request for: {domain}")
            self._message_callback(json.dumps({
                STR_CODE: Codes.CODE_ADD_DOMAIN,
                STR_CONTENT: domain
                }))
        else:
            self._show_error(
                message="Please enter a domain name",
                operation=STR_ADD_DOMAIN_REQUEST
            )

    def _remove_domain_request(self) -> None:
        """Remove the selected domain from the blocked sites list."""
        selection = self.domains_listbox.curselection()
        
        if selection:
            domain = self.domains_listbox.get(selection)
            self.logger.debug(f"Sending remove domain request for: {domain}")
            self._message_callback(json.dumps({
                STR_CODE: Codes.CODE_REMOVE_DOMAIN,
                STR_CONTENT: domain
            }))
        else:
            self._show_error(
                message=ERR_NO_DOMAIN_SELECTED,
                operation=STR_REMOVE_DOMAIN_REQUEST
            )

    def _handle_ad_block_request(self) -> None:
        """Handle changes to the ad block setting."""
        state = self.ad_var.get()
        self.logger.debug(f"Sending ad block request: {state}")

        self._message_callback(json.dumps({
            STR_CODE: Codes.CODE_AD_BLOCK,
            STR_CONTENT: state
        }))

    def _handle_adult_block_request(self) -> None:
        """Handle changes to the adult sites block setting."""
        state = self.adult_var.get()
        self.logger.debug(f"Sending adult block request: {state}")

        self._message_callback(json.dumps({
            STR_CODE: Codes.CODE_ADULT_BLOCK,
            STR_CONTENT: state
        }))

    def _update_block_settings(self, settings: dict) -> None:
        """Update the block settings radio buttons."""
        self.ad_var.set(settings[STR_AD_BLOCK])
        self.adult_var.set(settings[STR_ADULT_BLOCK])
        
    def _show_error(self, message: str, operation: str = "") -> None:
        """
        Display and log an error message for an operation.
        
        Args:
            message: The error message to display to the user.
            operation: Optional description of the operation that failed.
                      If provided, will be included in the log message.
        """
        if operation:
            self.logger.error(f"Operation failed: {operation} - Error: {message}")
        else:
            self.logger.error(f"Error: {message}")
            
        tk.messagebox.showerror(STR_ERROR, message)

    def _show_success(self, message: str, operation: str = "") -> None:
        """
        Display and log a success message for an operation.
        
        Args:
            message: The success message to display to the user.
            operation: Optional description of the operation that succeeded.
                      If provided, will be included in the log message.
        """
        log_message = f"Operation successful: {operation}" if operation else message
        self.logger.info(log_message)
        tk.messagebox.showinfo(STR_SUCCESS, message)

    def _setup_ui(self) -> None:
        """Set up the UI components including block controls and domain list."""
        # Main container with increased padding
        main_container = ttk.Frame(self.root, padding="20")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left side - Specific sites block (now with better proportions)
        sites_frame = ttk.LabelFrame(
            main_container,
            text="Specific Sites Block",
            padding="15"
        )
        sites_frame.grid(
            row=0,
            column=0,
            rowspan=3,
            padx=10,
            sticky=(tk.W, tk.E, tk.N, tk.S)
        )
        
        # Create a frame for listbox and scrollbar
        listbox_frame = ttk.Frame(sites_frame)
        listbox_frame.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Domains listbox with scrollbars
        self.domains_listbox = tk.Listbox(
            listbox_frame,
            width=40,
            height=15,
            selectmode=tk.SINGLE,
            activestyle='dotbox',
            font=('Arial', 10)
        )
        scrollbar_y = ttk.Scrollbar(
            listbox_frame,
            orient=tk.VERTICAL,
            command=self.domains_listbox.yview
        )
        scrollbar_x = ttk.Scrollbar(
            listbox_frame,
            orient=tk.HORIZONTAL,
            command=self.domains_listbox.xview
        )
        
        self.domains_listbox.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        
        # Grid layout for listbox and scrollbars
        self.domains_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Add domain entry with improved layout
        domain_entry_frame = ttk.Frame(sites_frame)
        domain_entry_frame.grid(
            row=1,
            column=0,
            pady=15,
            sticky=(tk.W, tk.E)
        )
        
        ttk.Label(
            domain_entry_frame,
            text="Add Domain:",
            font=('Arial', 10)
        ).grid(row=0, column=0, padx=5)
        
        self.domain_entry = ttk.Entry(
            domain_entry_frame,
            font=('Arial', 10)
        )
        self.domain_entry.grid(
            row=0,
            column=1,
            padx=5,
            sticky=(tk.W, tk.E)
        )
        
        # Buttons with improved styling
        button_frame = ttk.Frame(sites_frame)
        button_frame.grid(
            row=2,
            column=0,
            pady=10,
            sticky=(tk.W, tk.E)
        )
        
        style = ttk.Style()
        style.configure('Action.TButton', padding=5)
        
        ttk.Button(
            button_frame,
            text="Add Domain",
            style='Action.TButton',
            command=self._add_domain_request
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Remove Domain",
            style='Action.TButton',
            command=self._remove_domain_request
        ).grid(row=0, column=1, padx=5)

        # Right side controls with improved spacing
        controls_frame = ttk.Frame(main_container)
        controls_frame.grid(
            row=0,
            column=1,
            padx=20,
            sticky=(tk.N, tk.S)
        )

        # Ad Block controls with better styling
        ad_frame = ttk.LabelFrame(
            controls_frame,
            text="Ad Blocking",
            padding="15"
        )
        ad_frame.grid(
            row=0,
            column=0,
            pady=10,
            sticky=(tk.W, tk.E)
        )
        
        # Initialize with config value
        self.ad_var = tk.StringVar()
        ttk.Radiobutton(
            ad_frame,
            text="Enable",
            value="on",
            variable=self.ad_var,
            command=self._handle_ad_block_request
        ).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(
            ad_frame,
            text="Disable",
            value="off",
            variable=self.ad_var,
            command=self._handle_ad_block_request
        ).grid(row=0, column=1, padx=10)
        
        # Adult sites Block controls
        adult_frame = ttk.LabelFrame(
            controls_frame,
            text="Adult Content Blocking",
            padding="15"
        )
        adult_frame.grid(
            row=1,
            column=0,
            pady=10,
            sticky=(tk.W, tk.E)
        )
        
        # Initialize with config value
        self.adult_var = tk.StringVar()
        ttk.Radiobutton(
            adult_frame,
            text="Enable",
            value="on",
            variable=self.adult_var,
            command=self._handle_adult_block_request
        ).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(
            adult_frame,
            text="Disable",
            value="off",
            variable=self.adult_var,
            command=self._handle_adult_block_request
        ).grid(row=0, column=1, padx=10)

        # Configure grid weights for better resizing
        main_container.columnconfigure(0, weight=3)
        main_container.columnconfigure(1, weight=1)
        sites_frame.columnconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        domain_entry_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Bind events
        self.domains_listbox.bind('<Double-Button-1>', lambda e: self._remove_domain_request())
