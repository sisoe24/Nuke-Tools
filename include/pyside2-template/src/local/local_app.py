# coding: utf-8
from __future__ import print_function

import sys

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow
)

from ..main import MainWindow


def user_geometry():
    """Personal screen loc for rapid testing."""
    # modify here if needed
    return 0, 0, 500, 500


class _MainWindow(QMainWindow):
    """Main Window that inherits from main.py.

    This is to add some extra functionality when testing locally, like screen
    position.
    """

    def __init__(self):
        """Init method for the _MainWindow class."""
        MainWindow.__init__(self)
        self.setWindowTitle('__projectSlug__ Local')

        self.setGeometry(*user_geometry())


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = _MainWindow()
    window.show()
    app.exec_()
