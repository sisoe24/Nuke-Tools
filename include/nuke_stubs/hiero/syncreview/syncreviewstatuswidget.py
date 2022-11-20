from PySide2.QtCore import (QObject, Qt)
from PySide2.QtWidgets import (QWidget, QLabel, QHBoxLayout)
from . connectionmanager import ConnectionManager
from . connectionstate import ConnectionState


class SyncReviewStatusWidget(QWidget):
  """ Widget for editing displaying info about the current sync review state
  """
  def __init__(self, connectionManager):
    QWidget.__init__(self)

    self.connectionManager = connectionManager
    self.numberOfClients = 0
    self.connectionManager.connectionState.changed.connect(self._updateConnectionState)
    self.connectionManager.numberOfClientsChanged.connect(self._updateNumberOfClients)

    self.connectionState = QLabel("")
    self.connectionState.setToolTip("Sync review connection state")

    self.clientsConnected = QLabel("")
    self.clientsConnected.setToolTip("Number of clients connected to your sync review session")

    hLayout = QHBoxLayout()
    hLayout.setContentsMargins(0, 0, 0, 0)
    hLayout.addWidget(self.connectionState)
    hLayout.addWidget(self.clientsConnected)
    self.setLayout(hLayout)

  def _setStatus(self, connectionStateVisible, clientsConnectedVisible, connectionStateText, clientsConnectedText):
    self.connectionState.setVisible(connectionStateVisible)
    self.clientsConnected.setVisible(clientsConnectedVisible)
    self.connectionState.setText(connectionStateText)
    self.clientsConnected.setText(clientsConnectedText)

  def _updateConnectionState(self):
    if (self.connectionManager.connectionState == ConnectionState.DISCONNECTED):
      self._setStatus(False, False, "", "")
    elif (self.connectionManager.connectionState == ConnectionState.SERVER_RUNNING):
      self._setStatus(True, True, "Connection Status: listening", "Clients Connected: %d" % (self.numberOfClients))
    elif (self.connectionManager.connectionState == ConnectionState.CLIENT_CONNECTED):
      self._setStatus(True, True, "Connection Status: connected", "Clients Connected: %d" % (self.numberOfClients))
    elif (self.connectionManager.connectionState == ConnectionState.CLIENT_CONNECTING):
      self._setStatus(True, False, "Connection Status: connecting", "")

  def _updateNumberOfClients(self, numberOfClients):
    self.numberOfClients = numberOfClients
    if (self.connectionManager.connectionState == ConnectionState.SERVER_RUNNING):
      self._setStatus(True, True, "Connection Status: listening", "Clients Connected: %d" % (self.numberOfClients))
    elif (self.connectionManager.connectionState == ConnectionState.CLIENT_CONNECTED):
      self._setStatus(True, True, "Connection Status: connected", "Clients Connected: %d" % (self.numberOfClients))
