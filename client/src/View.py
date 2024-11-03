import tkinter as tk


class Viewer:
    def __init__(self) -> None:
        self.root: tk.Tk = tk.Tk()
        self.root.title("My Application")
        self.root.geometry("800x600")

    def run(self) -> None:
        """Run the viewer."""
        self.root.mainloop()
