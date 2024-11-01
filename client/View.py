import tkinter as tk

class Viewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("My Application")
        self.root.geometry("800x600")

    def run(self):
        self.root.mainloop()
