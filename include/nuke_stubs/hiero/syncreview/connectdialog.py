from PySide2.QtCore import (QEvent,
                            QObject)
from PySide2.QtGui import (QMovie,
                           QKeySequence)
from PySide2.QtWidgets import (QApplication,
                               QDialog,
                               QDialogButtonBox,
                               QFrame,
                               QFormLayout,
                               QHBoxLayout,
                               QLabel,
                               QLineEdit,
                               QPushButton,
                               QSizePolicy,
                               QSpinBox,
                               QWidget)
import hiero.ui
from hiero.core import ApplicationSettings
from . connectionmanager import (ConnectionManager,
                                 ConnectionState)
from . import config


class _PasteLineEdit(QLineEdit):
  def __init__(self, callback, parent=None):
    super(_PasteLineEdit, self).__init__(parent)
    self._callback = callback

  def createPasteContextMenu(self):
    menu = self.createStandardContextMenu()
    pasteAction = next((a for a in menu.actions() if "Paste" in a.text()), None)

    if pasteAction is not None:
      pasteAction.triggered.disconnect()
      pasteAction.triggered.connect(self._handlePasteAction)

    return menu

  def contextMenuEvent(self, event):
    self.createPasteContextMenu().exec_(event.globalPos())
    
  def _handlePasteAction(self):
    if self._callback() == False:
      # If callback can't handle the paste i.e. returns False, handle the paste directly
      self.paste()


class _PasteSpinBox(QSpinBox):
  def __init__(self, callback, parent=None):
    super(_PasteSpinBox, self).__init__(parent)
    self._pasteLineEdit = _PasteLineEdit(callback)
    self.setLineEdit(self._pasteLineEdit)

  def contextMenuEvent(self, event):
    self._pasteLineEdit.createPasteContextMenu().exec_(event.globalPos())


class _PasteFilter(QObject):
  def __init__(self, callback, parent=None):
    super(_PasteFilter, self).__init__(parent)
    self._callback = callback

  def eventFilter(self, _, event):
    if event.type() == QEvent.ShortcutOverride and event.matches(QKeySequence.Paste):
      # Override the default shortcut behavior and let Qt know that we want to handle QEvent.KeyPress for Paste.
      return True
    elif event.type() == QEvent.KeyPress and event.matches(QKeySequence.Paste):
      # Execute the provided callback. If callback can't handle the paste i.e. returns False, fallback to default paste behavior
      return self._callback()
    return False


class ConnectDialog(QDialog):
  """ Dialog for connecting as a client, allowing the user to specify the hostname
  and port to connect on
  """

  READY_TO_CONNECT_LABEL = "<font color='green'>Ready to connect</font>"
  CANCELLED_CONNECTION_LABEL = "Cancelled connect"
  ERROR_LABEL = "<font color='red'>{}</font>"
  DEFAULT_ERROR_MESSAGE = "Connection failed: Adjust settings and try again"

  def __init__(self, connectionManager):
    super(ConnectDialog, self).__init__()

    settings = hiero.core.ApplicationSettings()

    self._connectionManager = connectionManager
    self._connectionManager.connectionState.changed.connect(self.onConnectionStateChanged)
    self._connectionManager.connectionState.error.connect(self.onConnectError)

    self._pasteFilter = _PasteFilter(self._connectionInfoFromClipboard, self)

    layout = QFormLayout()
    self.setLayout(layout)

    layout.addRow("<b>Session Setup<b>", self._createDivider())

    nameAndColorLayout = QHBoxLayout()
    nameAndColorLayout.setContentsMargins(0, 0, 0, 0)

    self._nameField = QLineEdit()
    self._nameField.setToolTip(config.NAME_TOOL_TIP)
    nameSetting = settings.value(config.NAME_SETTING_KEY)
    self._nameField.setText(nameSetting)
    nameAndColorLayout.addWidget(self._nameField)

    self._colorPickerButton = hiero.ui.ColorButton("")
    self._colorPickerButton.setToolTip(config.COLOR_TOOL_TIP)
    colorSetting = settings.value(config.COLOR_SETTING_KEY)
    self._colorPickerButton.setColor(colorSetting)
    self._colorPickerButton.clicked.connect(self._openColorPicker)
    nameAndColorLayout.addWidget(self._colorPickerButton)

    self._nameAndColor = QWidget()
    self._nameAndColor.setLayout(nameAndColorLayout)
    layout.addRow("Your Name", self._nameAndColor)

    layout.addRow("<b>Connection Info<b>", self._createDivider())

    self._hostnameWidget = _PasteLineEdit(self._connectionInfoFromClipboard)
    self._hostnameWidget.setToolTip(config.CONNECT_HOSTNAME_TOOL_TIP)
    hostName = settings.value(config.PREVIOUS_HOST_KEY, config.DEFAULT_HOST)
    self._hostnameWidget.setText(hostName)
    self._hostnameWidget.installEventFilter(self._pasteFilter)
    layout.addRow("Host", self._hostnameWidget)

    self._portWidget = _PasteSpinBox(self._connectionInfoFromClipboard)
    self._portWidget.setToolTip(config.PORT_TOOL_TIP)
    self._portWidget.setMaximum(config.PORT_MAX)
    self._portWidget.setMinimum(config.PORT_MIN)
    port = int(settings.value(config.PREVIOUS_PORT_NUMBER_KEY, config.DEFAULT_PORT))
    self._portWidget.setValue(port)
    self._portWidget.installEventFilter(self._pasteFilter)
    layout.addRow("Port", self._portWidget)

    layout.addRow(QLabel("<b>Status<b>"))
    self._statusLabel = QLabel()
    self.setStatusText(ConnectDialog.READY_TO_CONNECT_LABEL)
    layout.addRow(self._statusLabel)

    self._connectingSpinner = QMovie("icons:RenderingSpinner.gif")

    self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    self._buttonBox.accepted.connect(self.connect)
    self._buttonBox.rejected.connect(self.cancel)
    layout.addRow("", self._buttonBox)

    okButton = self._buttonBox.button(QDialogButtonBox.Ok)
    okButton.setText("Connect")

    self.updateConnectButtonEnabled()
    self._portWidget.valueChanged.connect(self.onConnectDetailsChanged)
    self._hostnameWidget.textChanged.connect(self.onConnectDetailsChanged)

  def _createDivider(self):
    """ Convenience function for creating a sunken hirzontal divider """
    divider = QFrame()
    divider.setFrameStyle(QFrame.HLine | QFrame.Sunken)
    divider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return divider

  def _connectionInfoFromClipboard(self):
    """ Try to paste connection info from the clipboard """
    clipboardContents = QApplication.clipboard().text()
    try:
      hostNameStr, portStr = clipboardContents.split(':')
    except ValueError:
      return False

    if hostNameStr:
      try:
        port = int(portStr)
      except ValueError:
        # TODO user intended to paste connection info but port is not a valid int, fail silently for now
        return True
      self._hostnameWidget.setText(hostNameStr)
      self._portWidget.setValue(port)
      return True
    return False

  def _openColorPicker(self):
    """ Open the color picker dialog"""
    colorPickerDialog = hiero.ui.ColorPickerDialog()
    colorPickerDialog.setCurrentColor(self._colorPickerButton.color())
    colorPickerDialog.exec_()
    self._colorPickerButton.setColor(colorPickerDialog.currentColor())

  def getHostAndPort(self):
    """ Get the hostname and port to connect to """
    return self._hostnameWidget.text(), self._portWidget.value()

  def getClientData(self):
    """ Get the current client data info from the dialog """
    color = self._colorPickerButton.color()
    clientDataColor = (color.red(), color.green(), color.blue())
    return (self._nameField.text(), clientDataColor)

  def connect(self):
    """ Try to connect with the current settings """
    host, port = self.getHostAndPort()
    clientData = self.getClientData()
    self._connectionManager.connectClient(host, port, clientData)

    # Save the connect details unless there was an error
    if self._connectionManager.connectionState.errorState() == ConnectionState.ERROR_NONE:
      settings = hiero.core.ApplicationSettings()
      settings.setValue(config.PREVIOUS_HOST_KEY, host)
      settings.setValue(config.PREVIOUS_PORT_NUMBER_KEY, port)

  def cancel(self):
    """ Close the dialog and cancel any in-progress connections """
    if self._connectionManager.connectionState == ConnectionState.CLIENT_CONNECTING:
      self._connectionManager.disconnectClient()
    self.reject()

  def onConnectDetailsChanged(self):
    """ Called whenever the hostname or port is edited. If a connection attempt was
    already in progress, it will be cancelled.
    """
    if self._connectionManager.connectionState == ConnectionState.CLIENT_CONNECTING:
      self._connectionManager.disconnectClient()
      self.setStatusText(ConnectDialog.CANCELLED_CONNECTION_LABEL)
    self.updateConnectButtonEnabled()

  def updateConnectButtonEnabled(self):
    """ Set if the connect button is enabled state based on the connection state
    and the settings. At the moment it just checks if the hostname field has anything
    in it. We could maybe make this check the host is valid before the user tries to
    connect
    """
    enable = ((self._connectionManager.connectionState == ConnectionState.DISCONNECTED)
              and (len(self._hostnameWidget.text()) > 0))
    button = self._buttonBox.button(QDialogButtonBox.Ok)
    button.setEnabled(enable)

  def onConnectionStateChanged(self, state):
    """ Connection state change handling """
    if state == ConnectionState.CLIENT_CONNECTING:
      self.setStatusConnecting()
    elif state == ConnectionState.CLIENT_CONNECTED:
      self.accept() # Close the dialog
    self.updateConnectButtonEnabled()

  def onConnectError(self, error, errorText):
    """ Connection error handling """
    if not errorText:
      errorText = ConnectDialog.DEFAULT_ERROR_MESSAGE
    self.setStatusText(ConnectDialog.ERROR_LABEL.format(errorText))

  def setStatusText(self, text):
    """ Set the status label text """
    self._statusLabel.setMovie(None)
    self._statusLabel.setText(text)

  def setStatusConnecting(self):
    """ Show the connecting spinner """
    self._statusLabel.setText('')
    self._connectingSpinner.start()
    self._statusLabel.setMovie(self._connectingSpinner)
