# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtWidgets import (
    QPushButton,
    QTableWidgetItem,
    QTableWidget,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLabel
)


from .utils import color_widget
from .widgets import ErrorDialog, ToolBar
from . import nuke

LOGGER = logging.getLogger('projectname.main')
LOGGER.debug('-*- START APPLICATION -*-')


class NodesTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(['Name', 'Type'])

        self.itemClicked.connect(self.zoom_node)

        self.refresh()

    def zoom_node(self):
        # clear previous selection of nodes
        if nuke.nodesSelected():
            for _ in nuke.selectedNodes():
                _.setSelected(False)

        item = self.item(self.currentRow(), 0)
        nuke.toNode(item.text()).setSelected(True)
        nuke.zoomToFitSelected()

    def refresh(self):
        # clear previous rows
        self.setRowCount(0)

        nodes = nuke.allNodes()
        self.setRowCount(len(nodes))

        for index, node in enumerate(nodes):
            self.setItem(index, 0, QTableWidgetItem(node.name()))
            self.setItem(index, 1, QTableWidgetItem(node.Class()))


class ExampleWidgets(QWidget):
    """Main widgets class.

    Here you can create more widgets which are going to be displayed
    in the main window.

    """

    @color_widget()
    def __init__(self):
        QWidget.__init__(self)

        label = QLabel('Dag Nodes')
        label.setStyleSheet('font-size: 25px')

        table = NodesTable()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(table.refresh)

        _layout = QVBoxLayout()
        _layout.addWidget(label)
        _layout.addWidget(table)
        _layout.addWidget(refresh_btn)

        self.setLayout(_layout)


class MainWindow(QMainWindow):
    """Custom QMainWindow class.

    The window comes with a toolbar and a status bar. It also spawns an error
    dialog box if an exception happens when loading the main widgets.
    """

    def __init__(self):
        """Init method for main window widget."""
        QMainWindow.__init__(self)
        self.setWindowTitle("projectname")

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        try:
            main_widgets = ExampleWidgets()
        except Exception as err:
            ErrorDialog(err, self).show()
            LOGGER.critical(err, exc_info=True)
        else:
            self.setCentralWidget(main_widgets)

    def show_status_message(self, msg, timeout=5000):
        self.statusBar().showMessage(msg, timeout)


try:
    import nukescripts
except ImportError as error:
    pass
else:
    nukescripts.panels.registerWidgetAsPanel(
        'projectname.src.main.MainWindow', 'projectname',
        'projectname.MainWindow')
