import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Callable
import json

class Viewer:
    """
    Graphical user interface for the application.
    """

    def __init__(self, message_callback: Callable[[str], None]) -> None:
        """
        Initialize the viewer window and its components.
        
        Args:
            message_callback: Callback function to handle message sending.
        """
        self.root: tk.Tk = tk.Tk()
        self.root.title("Chat Application")
        self.root.geometry("800x600")
        self._message_callback = message_callback
        self._setup_ui()

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
        self.root.mainloop()

    def _setup_ui(self) -> None:
        """Set up the UI components including text areas and buttons."""
        main_container = ttk.Frame(self.root, padding="5")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.message_area = scrolledtext.ScrolledText(
            main_container,
            wrap=tk.WORD,
            width=70,
            height=30
        )
        
        self.message_area.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.message_area.config(state=tk.DISABLED)

        self.input_field = ttk.Entry(main_container)
        self.input_field.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.input_field.bind("<Return>", lambda e: self._send_message())

        self.send_button = ttk.Button(
            main_container,
            text="Send",
            command=self._send_message
        )
        self.send_button.grid(row=1, column=1)

        main_container.columnconfigure(0, weight=3)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(0, weight=1)

    ## TODO: This method won't be relevant for the final version
    def display_message(self, sender: str, message: str) -> None:
        """
        Display a message in the message area.
        
        Args:
            sender: The name of the message sender.
            message: The message content to display.
        """
        self.message_area.config(state=tk.NORMAL)
        self.message_area.insert(tk.END, f"{sender}: {message}\n")
        self.message_area.see(tk.END)
        self.message_area.config(state=tk.DISABLED)

    ## TODO: This method won't be relevant for the final version
    def display_error(self, error_message: str) -> None:
        """
        Display an error message in the message area.
        
        Args:
            error_message: The error message to display.
        """
        self.message_area.config(state=tk.NORMAL)
        self.message_area.insert(tk.END, f"Error: {error_message}\n")
        self.message_area.see(tk.END)
        self.message_area.config(state=tk.DISABLED)
