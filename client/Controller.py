from View import Viewer
from Communicator import Communicator

class Controller:
    def __init__(self):
        self._view = Viewer()
        self._communicator = Communicator()

    def run(self):
        self._view.run()
