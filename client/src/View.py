import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from typing import Callable, Dict, List, Any
import json
import os
from .Logger import setup_logger
from .ConfigManager import ConfigManager


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
        
        self.root: tk.Tk = tk.Tk()
        self.root.title("Site Blocker")
        self.root.geometry("800x600")
        
        self._setup_ui()
        self.logger.info("Viewer initialization complete")

    def _send_message(self) -> None:
        """Handle the sending of messages from the input field."""
        message = self.input_field.get().strip()
        if message:
            message_json = json.dumps({"CODE": "100", "content": message})
            self._message_callback(message_json)
            self.input_field.delete(0, tk.END)
            self.display_message("You", message)

    def run(self) -> None:
        """Start the main event loop of the viewer."""
        self.logger.info("Starting main event loop")
        self.root.mainloop()

    def _setup_ui(self) -> None:
        """Set up the UI components including block controls and domain list."""
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left side - Specific sites block
        sites_frame = ttk.LabelFrame(main_container, text="Specific sites block", padding="5")
        sites_frame.grid(row=0, column=0, rowspan=3, padx=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Domains listbox
        self.domains_listbox = tk.Listbox(sites_frame, width=40, height=15)
        self.domains_listbox.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add domain entry
        domain_entry_frame = ttk.Frame(sites_frame)
        domain_entry_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(domain_entry_frame, text="Add Domain:").grid(row=0, column=0, padx=5)
        self.domain_entry = ttk.Entry(domain_entry_frame)
        self.domain_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        # Add buttons for domain management
        button_frame = ttk.Frame(sites_frame)
        button_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Add", command=self._add_domain).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Remove", command=self._remove_domain).grid(row=0, column=1, padx=5)
        
        # Bind double-click event for removing domains
        self.domains_listbox.bind('<Double-Button-1>', lambda e: self._remove_domain())
        
        # Load saved domains into listbox
        for domain in self.config["blocked_domains"].keys():
            self.domains_listbox.insert(tk.END, domain)
        
        # Ad Block controls
        ad_frame = ttk.LabelFrame(main_container, text="Ad Block", padding="5")
        ad_frame.grid(row=0, column=1, pady=10, sticky=(tk.W, tk.E))
        
        self.ad_var = tk.StringVar(value=self.config["settings"]["ad_block"])
        ttk.Radiobutton(ad_frame, text="on", value="on", variable=self.ad_var).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(ad_frame, text="off", value="off", variable=self.ad_var).grid(row=0, column=1, padx=10)
        
        # Adult sites Block controls
        adult_frame = ttk.LabelFrame(main_container, text="Adult sites Block", padding="5")
        adult_frame.grid(row=1, column=1, pady=10, sticky=(tk.W, tk.E))
        
        self.adult_var = tk.StringVar(value=self.config["settings"]["adult_block"])
        ttk.Radiobutton(adult_frame, text="on", value="on", variable=self.adult_var).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(adult_frame, text="off", value="off", variable=self.adult_var).grid(row=0, column=1, padx=10)
        
        # Bind radio button commands
        self.ad_var.trace_add('write', lambda *args: self._handle_ad_block())
        self.adult_var.trace_add('write', lambda *args: self._handle_adult_block())
        
        # Configure grid weights
        main_container.columnconfigure(0, weight=1)
        sites_frame.columnconfigure(0, weight=1)
        domain_entry_frame.columnconfigure(1, weight=1)

    def _add_domain(self) -> None:
        """Add a domain to the blocked sites list."""
        domain = self.domain_entry.get().strip()
        if domain:
            if domain not in self.config["blocked_domains"]:
                self.domains_listbox.insert(tk.END, domain)
                self.config["blocked_domains"][domain] = True
                self.domain_entry.delete(0, tk.END)
                self.config_manager.save_config(self.config)
                self.logger.info(f"Domain added: {domain}")
            else:
                self.logger.warning(f"Attempted to add duplicate domain: {domain}")
                self._show_error("Domain already exists in the list")

    def _remove_domain(self) -> None:
        """Remove the selected domain from the blocked sites list."""
        selection = self.domains_listbox.curselection()
        if selection:
            domain = self.domains_listbox.get(selection)
            self.domains_listbox.delete(selection)
            del self.config["blocked_domains"][domain]
            self.config_manager.save_config(self.config)
            self.logger.info(f"Domain removed: {domain}")
        else:
            self.logger.warning("Attempted to remove domain without selection")
            self._show_error("Please select a domain to remove")

    def _handle_ad_block(self) -> None:
        """Handle changes to the ad block setting."""
        state = self.ad_var.get()
        self.config["settings"]["ad_block"] = state
        self.config_manager.save_config(self.config)
        self.logger.info(f"Ad blocking state changed to: {state}")

    def _handle_adult_block(self) -> None:
        """Handle changes to the adult sites block setting."""
        state = self.adult_var.get()
        self.config["settings"]["adult_block"] = state
        self.config_manager.save_config(self.config)
        self.logger.info(f"Adult site blocking state changed to: {state}")

    def _show_error(self, message: str) -> None:
        """
        Display an error message in a popup window.
        
        Args:
            message: The error message to display.
        """
        self.logger.error(f"Error message displayed: {message}")
        tk.messagebox.showerror("Error", message)

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
            "ad_block": self.ad_var.get(),
            "adult_block": self.adult_var.get()
        }
