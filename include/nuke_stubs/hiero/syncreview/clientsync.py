
from . import messages
from . messagedispatcher import MessageDispatcher
from PySide2.QtCore import Signal
from . synctool import SyncTool

"""
Classes for syncing information about connected clients.
"""

messages.defineMessageType('SyncClientData', ('clientData', messages.Json))


class ClientDataProvider(SyncTool):
  """
  Class that holds connected client data. The key of this dictionary is the unique ID of the client. The value is a
  tuple holding the client name and a tuple of the RGB color associated to it.
  """

  clientDataChanged = Signal()
  clientDataCleared = Signal()

  def __init__(self, messageDispatcher):
    super(ClientDataProvider, self).__init__(messageDispatcher)
    self.clientData = dict()
    self.messageDispatcher._registerCallback(messages.Disconnected, self._onGuestDisconnected)
    self.clientDataChanged.emit()

  def _onGuestDisconnected(self, msg):
    del self.clientData[msg.disconnected]
    self.clientDataChanged.emit()

  def shutdown(self):
    self.clientDataCleared.emit()

class ClientSyncHost(ClientDataProvider):
  """ Listens for connections from other clients, updates the connected client data and sends it to guests. """

  def __init__(self, messageDispatcher):
    super(ClientSyncHost, self).__init__(messageDispatcher)
    self.messageDispatcher._registerCallback(messages.Connect, self._onGuestConnected)

  def addGuest(self, clientId, clientData):
    """ Adds a new guest to the client data without sending notifications to clients. """
    self.clientData[clientId] = clientData
    self.clientDataChanged.emit()

  def _onGuestConnected(self, msg):
    self.addGuest(msg.sender, msg.clientData)
    syncMsg = messages.SyncClientData(clientData=self.clientData)
    self.messageDispatcher.sendMessage(syncMsg)
    self.clientDataChanged.emit()


class ClientSyncGuest(ClientDataProvider):
  """ Makes available the connected client data received from the server's ClientSyncHost tool. """

  def __init__(self, messageDispatcher):
    super(ClientSyncGuest, self).__init__(messageDispatcher)
    self.messageDispatcher._registerCallback(messages.SyncClientData, self._onSyncClientData)

  def _onSyncClientData(self, msg):
    self.clientData = msg.clientData
    self.clientDataChanged.emit()
