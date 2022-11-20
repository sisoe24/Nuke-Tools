import platform
from PySide2.QtCore import (QPoint,
                            Qt)
from PySide2.QtGui import (QFont,
                           QIcon,
                           QPalette)
from PySide2.QtNetwork import (QAbstractSocket, QNetworkInterface)
from PySide2.QtWidgets import (QApplication,
                               QComboBox,
                               QDialog,
                               QDialogButtonBox,
                               QFormLayout,
                               QFrame,
                               QHBoxLayout,
                               QLabel,
                               QLineEdit,
                               QMessageBox,
                               QPushButton,
                               QSizePolicy,
                               QSpinBox,
                               QToolTip,
                               QWidget)
from hiero.core import ApplicationSettings
import hiero.ui
from . import config
from . connectionstate import ConnectionState

__RequiredFlags = QNetworkInterface.IsUp | QNetworkInterface.IsRunning
__InvalidFlags = QNetworkInterface.IsLoopBack


def _GetLocalAddresses():
  """ Get a list of local IP address strings. """
  results = []
  interfaces = QNetworkInterface.allInterfaces()
  for interface in interfaces:
    # Check the flags match what we're looking for. Must match.
    flags = interface.flags()
    if ((flags & __RequiredFlags) != __RequiredFlags) or (flags & __InvalidFlags):
      continue

    # Filter out VMWare interfaces
    if interface.name().startswith("vmnet"):
      continue

    addressEntries = interface.addressEntries()
    for addressEntry in addressEntries:
      address = addressEntry.ip()
      # Only include IPv4 addresses for the moment.
      if address.protocol() != QAbstractSocket.IPv4Protocol:
        continue
      results.append(str(address.toString()))
  return results


class SessionSetupDialog(QDialog):
  """ Dialog for setting up a new sync review session
  """

  def __init__(self, connectionManager, project):
    super(SessionSetupDialog, self).__init__()

    settings = ApplicationSettings()
    self._connectionManager = connectionManager
    self._project = project

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

    layout.addRow("<b>Connection Setup<b>", self._createDivider())

    self._hostNameComboBox = QComboBox()
    self._hostNameComboBox.setToolTip(config.HOST_HOSTNAME_TOOL_TIP)
    self._hostNameComboBox.addItem(platform.node())
    for address in _GetLocalAddresses():
      self._hostNameComboBox.addItem(address)

    # Explicitly set the font of the combo box entries, because we want to
    # change the font of the whole widget to italic when 'Other' is selected, but
    # these should not be italicised
    plainFont = self.font()
    plainFont.setItalic(False)
    for index in range(self._hostNameComboBox.count()):
      self._hostNameComboBox.setItemData(index, plainFont, Qt.FontRole)

    # Add the 'Other' entry. When this is selected, a line edit for the user to
    # put their own address in is shown
    self._otherHostNameIndex = self._hostNameComboBox.count()
    self._hostNameComboBox.addItem('Other')
    italicFont = self.font()
    italicFont.setItalic(True)
    self._hostNameComboBox.setItemData(self._otherHostNameIndex, italicFont, Qt.FontRole)
    self._otherHostNameEdit = QLineEdit()
    self._otherHostNameEdit.setMinimumWidth(100)
    self._otherHostNameEdit.textEdited.connect(self._updateConnectionInfo)
    hostNameLayout = QHBoxLayout()
    hostNameLayout.addWidget(self._hostNameComboBox)
    hostNameLayout.addWidget(self._otherHostNameEdit)
    layout.addRow("Hostname", hostNameLayout)

    self._port = QSpinBox()
    self._port.setToolTip(config.PORT_TOOL_TIP)
    self._port.setMaximum(config.PORT_MAX)
    port = int(settings.value(config.LAST_SHARED_PORT_KEY, config.DEFAULT_PORT))
    self._port.setValue(port)
    self._port.setMinimum(config.PORT_MIN)
    layout.addRow("Port", self._port)

    self._initConnectionInfoWidgets()
    layout.addRow("Connection Info", self._connectionInfoLayout)
    self._updateConnectionInfo()
    self._hostNameComboBox.currentTextChanged.connect(self._onHostNameSelectionChanged)
    self._port.valueChanged.connect(self._updateConnectionInfo)

    self._buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
    self._buttonBox.accepted.connect(self.startSession)
    self._buttonBox.rejected.connect(self.reject)
    layout.addRow("", self._buttonBox)

    okButton = self._buttonBox.button(QDialogButtonBox.Ok)
    okButton.setText("Start")

    lastHostname = settings.value(config.LAST_SHARED_HOST_KEY)
    if lastHostname:
      if self._hostNameComboBox.findText(lastHostname) == -1:
        self._otherHostNameEdit.setText(lastHostname)
        self._hostNameComboBox.setCurrentIndex(self._otherHostNameIndex)
      else:
        self._hostNameComboBox.setCurrentText(lastHostname)
    self._onHostNameSelectionChanged() # Make sure all the widgets are in the correct state

  def _initConnectionInfoWidgets(self):
    self._connectionInfo = QLineEdit()
    self._connectionInfo.setToolTip(config.CONNECTION_INFO_TOOL_TIP)
    self._connectionInfo.setReadOnly(True)
    # Because the text is read only, make it appear as though the widget is disabled
    palette = self.palette()
    palette.setBrush(QPalette.Active, QPalette.Text, palette.brush(QPalette.Disabled, QPalette.Text))
    self._connectionInfo.setPalette(palette)

    self._connectionInfoButton = QPushButton(QIcon("icons:SyncCopyInfo.png"), '')
    self._connectionInfoButton.setToolTip(config.COPY_INFO_TOOL_TIP)
    self._connectionInfoButton.clicked.connect(self._copyConnectionInfo)
    self._connectionInfoButton.setFocusPolicy(Qt.NoFocus)

    self._connectionInfoLayout = QHBoxLayout()
    self._connectionInfoLayout.setContentsMargins(0, 0, 0, 0)
    self._connectionInfoLayout.addWidget(self._connectionInfo)
    self._connectionInfoLayout.addWidget(self._connectionInfoButton)

  def _onHostNameSelectionChanged(self):
    """ User selected an entry in the host name combo box. If this was 'Other'
    show the line edit for that
    """
    otherSelected = (self._hostNameComboBox.currentIndex() == self._otherHostNameIndex)
    self._otherHostNameEdit.setVisible(otherSelected)
    # If other is selected, make the combo box show it italic
    font = self.font()
    font.setItalic(otherSelected)
    self._hostNameComboBox.setFont(font)
    self._updateConnectionInfo()

  def _createDivider(self):
    """ Convenience function for creating a sunken horizontal divider """
    divider = QFrame()
    divider.setFrameStyle(QFrame.HLine | QFrame.Sunken)
    divider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return divider

  def _openColorPicker(self):
    """ Open the color picker dialog"""
    colorPickerDialog = hiero.ui.ColorPickerDialog()
    colorPickerDialog.setCurrentColor(self._colorPickerButton.color())
    colorPickerDialog.exec_()
    self._colorPickerButton.setColor(colorPickerDialog.currentColor())

  def getClientData(self):
    """ Get the clients data from the dialog """
    color = self._colorPickerButton.color()
    clientDataColor = (color.red(), color.green(), color.blue())
    return (self._nameField.text(), clientDataColor)

  def getPort(self):
    """ Get the port number from the dialog """
    return self._port.value()

  def _copyConnectionInfo(self):
    QApplication.clipboard().setText(self._connectionInfo.text())
    toolTipPosition = self.mapToGlobal(self._connectionInfoButton.pos())
    toolTipPosition += QPoint(0, 10)  # Adjust tooltip position so it doesn't cover the button.
    QToolTip.showText(toolTipPosition,
                      "Connection info successfully copied to clipboard",
                      self._connectionInfoButton,
                      self._connectionInfoButton.rect(),
                      3000)

  def _hostNameText(self):
    """ Get the currently selected host name text, which will either be an entry
    in the combo box or from the text edit if 'other' was selected
    """
    if self._hostNameComboBox.currentIndex() == self._otherHostNameIndex:
      return self._otherHostNameEdit.text()
    else:
      return self._hostNameComboBox.currentText()

  def _updateConnectionInfo(self):
    self._connectionInfo.setText('{}:{}'.format(self._hostNameText(), self.getPort()))

  def startSession(self):
    """ Start the server session using the current dialog info"""
    lastHostname = self._hostNameText()
    port = self.getPort()

    connectionState = self._connectionManager.connectionState

    clientData = self.getClientData()
    self._connectionManager.startServer(port, clientData, self._project)

    if connectionState == ConnectionState.SERVER_RUNNING:
      # Store the host and port settings in the preferences
      settings = ApplicationSettings()
      settings.setValue(config.LAST_SHARED_HOST_KEY, lastHostname)
      settings.setValue(config.LAST_SHARED_PORT_KEY, port)
      self._connectionManager.setConnectionInfo(self._connectionInfo.text())
      self.accept()
    else:
      errorText = "Failed to start session. Please check the port is valid."
      QMessageBox.warning(self, "Session Setup", errorText)
