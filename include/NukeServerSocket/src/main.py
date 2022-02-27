"""Main application logic. This is where main window and widget are created."""
# coding: utf-8
from __future__ import print_function

import os
import logging

from PySide2.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget
)

from .utils import AppSettings
from .connection import QServer, SendTestClient, SendNodesClient
from .widgets import (
    LogWidgets,
    ConnectionsWidget,
    ErrorDialog,
    ToolBar
)

LOGGER = logging.getLogger('NukeServerSocket.main')
LOGGER.debug(' -*- START APPLICATION -*-')


def init_settings():
    """Set up some settings in the config file.

    Function will create the tmp folder if doesn't exists already, and write
    the path to the application settings file. Function will also validate the
    port configuration.
    """
    # ! TODO: need to re think this

    tmp_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '.tmp'
    )

    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)

    settings = AppSettings()
    LOGGER.debug('Main :: settings file : %s', settings.fileName())
    settings.validate_port_settings()
    settings.setValue('path/transfer_file',
                      os.path.join(tmp_folder, 'transfer_nodes.tmp'))

    settings.setValue('dialog/dont_show', False)


class MainWindowWidget(QWidget):
    """Main window widgets and logic.

    This is were all of the main widgets are laid out. Class also deals with
    a higher level logic of user interaction when clicking the various buttons.
    """

    def __init__(self):
        """Init method for MainWindowWidget."""
        QWidget.__init__(self)
        LOGGER.debug('Main :: init')
        # ! TODO: Refactor needed

        init_settings()

        self.connections = ConnectionsWidget(parent=self)

        self.connect_btn = self.connections.buttons.connect_btn
        self.connect_btn.toggled.connect(self.toggle_connection)

        self.send_btn = self.connections.buttons.send_btn
        self.send_btn.clicked.connect(self.send_nodes)

        self.test_btn = self.connections.buttons.test_btn
        self.test_btn.clicked.connect(self.send_test)

        self.log_widgets = LogWidgets()

        _layout = QVBoxLayout()
        _layout.addWidget(self.connections)
        _layout.addWidget(self.log_widgets)

        self.setLayout(_layout)

        self._server = None
        self._client = None

    def _enable_connection_mod(self, state):  # type: (bool) -> None
        """Enable/disable connection widgets modification.

        When connected the port and the sender mode will be disabled.

        Args:
            state (bool): state of the widget.
        """
        self.connections.server_port.setEnabled(state)
        self.connections.sender_mode.setEnabled(state)

    def _disconnect(self):
        """If server connection gets timeout then close it and reset UI."""
        self.connect_btn.setChecked(False)

    def setup_server(self):
        """Set up the server class and its custom signals.

        Returns:
            QServer: the server object.
        """
        def _setup_socket_log(socket):
            """Set up socket log signals."""
            socket.state_changed.connect(self.log_widgets.set_status_text)
            socket.received_text.connect(self.log_widgets.set_received_text)
            socket.output_text.connect(self.log_widgets.set_output_text)
            socket.execution_error.connect(
                lambda text: ErrorDialog(text, self).show()
            )

        _server = QServer()
        _server.server_timeout.connect(
            self.connections._timeout._server_timeout.setText)

        _server.timeout.connect(self._disconnect)
        _server.state_changed.connect(self.log_widgets.set_status_text)
        _server.socket_ready.connect(_setup_socket_log)

        return _server

    def toggle_connection(self, state):  # type: (bool) -> None
        """Toggle connection state."""
        def _start_connection():
            """Start connection to server."""
            self._server = self.setup_server()

            try:
                status = self._server.start_server()
            except RuntimeError as err:
                LOGGER.error('server did not connect: %s', err)
                self.connections._disconnect()
                return False
            else:
                LOGGER.debug('server is connected: %s', status)
                self._enable_connection_mod(False)

            return bool(status)

        if state:
            return _start_connection()
        try:
            self._server.close_server()
        except AttributeError:
            # if function is called with False as an argument when connection
            # has never started, will cause a AttributeError  because _server
            # hasn't been declared yet
            pass

        self._enable_connection_mod(True)

    def send_nodes(self):
        """Send the selected Nuke Nodes using the internal client.

        Returns:
            SendNodesClient: SendNodesClient object.
        """
        self._client = SendNodesClient()
        self._connect_client(self.send_btn)
        self._client.client_timeout.connect(
            self.connections._timeout._socket_timeout.setText)
        return self._client

    def send_test(self):
        """Send a test message using the internal _client.

        Returns:
            SendTestClient: SendTestClient object.
        """
        self._client = SendTestClient()
        self._client.client_timeout.connect(
            self.connections._timeout._client_timeout.setText)
        self._connect_client(self.test_btn)
        return self._client

    def _connect_client(self, client_btn):
        """Connect the client to host and update status log.

        Args:
            client_btn (QPushButton): the client button to enable back when
            client is ready so send new data. This will be emitted from the
            client object signal.
        """
        self._client.client_ready.connect(client_btn.setEnabled)
        self._client.state_changed.connect(self.log_widgets.set_status_text)
        self._client.connect_to_host()


class MainWindow(QMainWindow):
    """Custom QMainWindow class.

    A toolbar and a status bar will be added in the main app together with the
    main widgets.

    If app has an exception loading the main widget, will spawn an ErrorDialog
    class.
    """

    def __init__(self, main_widget=MainWindowWidget):
        """Init method for main window widget."""
        QMainWindow.__init__(self)
        self.setWindowTitle("NukeServerSocket")

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        try:
            main_widgets = main_widget()
        except Exception as err:  # skipcq: PYL-W0703
            ErrorDialog(err, self).show()
            LOGGER.critical(err, exc_info=True)
        else:
            self.setCentralWidget(main_widgets)


try:
    import nukescripts
except ImportError:
    pass
else:
    nukescripts.panels.registerWidgetAsPanel(
        'NukeServerSocket.src.main.MainWindow', 'NukeServerSocket',
        'NukeServerSocket.MainWindow')
