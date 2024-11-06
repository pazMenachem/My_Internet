import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List
import json
import threading
from .Logger import setup_logger
from .ConfigManager import ConfigManager

from .utils import (
    Codes,
    WINDOW_SIZE, WINDOW_TITLE,
    ERR_DUPLICATE_DOMAIN, ERR_NO_DOMAIN_SELECTED, ERR_DOMAIN_LIST_UPDATE_FAILED,
    STR_AD_BLOCK, STR_ADULT_BLOCK, STR_CODE,
    STR_BLOCKED_DOMAINS, STR_CONTENT, STR_SETTINGS, STR_ERROR
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
        self._update_list_lock = threading.Lock()

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

    def update_domain_list(self, domains: List[str]) -> None:
        """
        Update the domains listbox with a new list of domains from the server.

        Args:
            domains: List of domain strings to be displayed in the listbox.
        """
        with self._update_list_lock:
            self.logger.info("Updating domain list from server")

            try:
                self.domains_listbox.delete(0, tk.END)
                
                for domain in domains:
                    self.domains_listbox.insert(tk.END, domain)
                    
                self.logger.info(f"Updated domain list with {len(domains)} domains")

            except Exception as e:
                self.logger.error(f"Error updating domain list: {str(e)}")
                self._show_error(ERR_DOMAIN_LIST_UPDATE_FAILED)

    def _add_domain(self) -> None:
        """Add a domain to the blocked sites list."""
        domain = self.domain_entry.get().strip()
        
        if domain:
            if domain not in self.config[STR_BLOCKED_DOMAINS]:
                self.domains_listbox.insert(tk.END, domain)
                self.domain_entry.delete(0, tk.END)

                self.config[STR_BLOCKED_DOMAINS][domain] = True
                self.config_manager.save_config(self.config)

                self._message_callback(json.dumps({
                    STR_CODE: Codes.CODE_ADD_DOMAIN,
                    STR_CONTENT: domain
                    }))

                self.logger.info(f"Domain added: {domain}")
            else:
                self.logger.warning(f"Attempted to add duplicate domain: {domain}")
                self._show_error(ERR_DUPLICATE_DOMAIN)
                
    def _remove_domain(self) -> None:
        """Remove the selected domain from the blocked sites list."""
        selection = self.domains_listbox.curselection()
        
        if selection:
            domain = self.domains_listbox.get(selection)
            self.domains_listbox.delete(selection)
            
            del self.config[STR_BLOCKED_DOMAINS][domain]
            self.config_manager.save_config(self.config)
            
            self._message_callback(json.dumps({
                STR_CODE: Codes.CODE_REMOVE_DOMAIN,
                STR_CONTENT: domain
                }))
            
            self.logger.info(f"Domain removed: {domain}")
        else:
            self.logger.warning("Attempted to remove domain without selection")
            self._show_error(ERR_NO_DOMAIN_SELECTED)

    def _handle_ad_block(self) -> None:
        """Handle changes to the ad block setting."""
        state = self.ad_var.get()
        self.config[STR_SETTINGS][STR_AD_BLOCK] = state
        self.config_manager.save_config(self.config)
        
        self._message_callback(json.dumps({
            STR_CODE: Codes.CODE_AD_BLOCK,
            STR_CONTENT: state
            }))
        
        self.logger.info(f"Ad blocking state changed to: {state}")

    def _handle_adult_block(self) -> None:
        """Handle changes to the adult sites block setting."""
        state = self.adult_var.get()
        self.config[STR_SETTINGS][STR_ADULT_BLOCK] = state
        self.config_manager.save_config(self.config)
        
        self._message_callback(json.dumps({
            STR_CODE: Codes.CODE_ADULT_BLOCK,
            STR_CONTENT: state
            }))
        
        self.logger.info(f"Adult site blocking state changed to: {state}")

    def _show_error(self, message: str) -> None:
        """
        Display an error message in a popup window.
        
        Args:
            message: The error message to display.
        """
        self.logger.error(f"Error message displayed: {message}")
        tk.messagebox.showerror(STR_ERROR, message)

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
            command=self._add_domain
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Remove Domain",
            style='Action.TButton',
            command=self._remove_domain
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
        self.ad_var = tk.StringVar(value=self.config[STR_SETTINGS][STR_AD_BLOCK])
        ttk.Radiobutton(
            ad_frame,
            text="Enable",
            value="on",
            variable=self.ad_var,
            command=self._handle_ad_block
        ).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(
            ad_frame,
            text="Disable",
            value="off",
            variable=self.ad_var,
            command=self._handle_ad_block
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
        self.adult_var = tk.StringVar(value=self.config[STR_SETTINGS][STR_ADULT_BLOCK])
        ttk.Radiobutton(
            adult_frame,
            text="Enable",
            value="on",
            variable=self.adult_var,
            command=self._handle_adult_block
        ).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(
            adult_frame,
            text="Disable",
            value="off",
            variable=self.adult_var,
            command=self._handle_adult_block
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
        self.domains_listbox.bind('<Double-Button-1>', lambda e: self._remove_domain())

        # Load saved domains
        for domain in self.config[STR_BLOCKED_DOMAINS].keys():
            self.domains_listbox.insert(tk.END, domain)